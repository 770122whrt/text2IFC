"""Bounded, read-only IFC2X3 viewer smoke checks against the existing dataset.
No repair, provider calls, recursive corpus extraction or IFC rewriting.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / '.artifacts' / 'dataset-ifc2x3'

def catalog():
    manifest = ROOT / 'dataset/manifests/ifc-files.jsonl'
    result = []
    for line in manifest.read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        path = ROOT / row['local_path']
        if row.get('header_schema') != 'IFC2X3' or not path.is_file():
            continue
        size = row.get('size_bytes', 0)
        if not 10000 <= size <= 15 * 1048576:
            continue
        with path.open('rb') as f:
            prefix = f.read(512)
        result.append({'path': row['local_path'], 'source': row['source_id'],
                       'bytes': size, 'state': 'lfs_pointer' if prefix.startswith(b'version https://git-lfs') else 'materialized',
                       'license': row.get('license'), 'counts': {k: row.get('entity_counts', {}).get(k, 0) for k in ['IfcWall', 'IfcWindow', 'IfcColumn']}})
    print(json.dumps(result, ensure_ascii=False, indent=2))

def run(label):
    import base64, importlib.util, subprocess, time, urllib.request
    import ifcopenshell
    output = OUT / label
    output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('viewer_qa', HERE / 'verify_browser.py')
    qa = importlib.util.module_from_spec(spec); spec.loader.exec_module(qa)
    samples = json.loads((HERE / 'tests/dataset-samples.json').read_text(encoding='utf8'))['samples']
    metadata = {r['local_path']: r for r in map(json.loads, (ROOT / 'dataset/manifests/ifc-files.jsonl').read_text(encoding='utf8').splitlines())}
    log = (output / 'browser.log').open('wb')
    process = subprocess.Popen(['/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', '--headless=new', '--no-first-run', '--no-default-browser-check', '--disable-extensions', '--disable-background-networking', '--remote-debugging-port=9342', '--remote-allow-origins=*', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--user-data-dir=' + qa.winpath(output / 'profile'), 'about:blank'], stdout=log, stderr=subprocess.STDOUT)
    client = None; results = []
    try:
        pages = None
        for _ in range(60):
            try:
                pages = json.load(urllib.request.urlopen('http://127.0.0.1:9342/json', timeout=1)); break
            except Exception: time.sleep(.2)
        if not pages: raise RuntimeError('Isolated browser did not start')
        client = qa.CDP(next(p['webSocketDebuggerUrl'] for p in pages if p['type'] == 'page'))
        client.call('Page.enable'); client.call('Runtime.enable')
        client.call('Emulation.setDeviceMetricsOverride', {'width':1440, 'height':960, 'deviceScaleFactor':1, 'mobile':False})
        for sample in samples:
            row = dict(sample); path = ROOT / sample['path']; original = None
            try:
                original = path.read_bytes()
                if original.startswith(b'version https://git-lfs'): raise RuntimeError('LFS content unavailable; not a parser failure')
                source = ifcopenshell.open(str(path))
                row.update(bytes=len(original), source_collection=metadata[sample['path']]['source_id'], schema=source.schema)
                if source.schema != 'IFC2X3': raise RuntimeError('Outside declared IFC2X3 scope')
                expected = {p.id():p.GlobalId for p in source.by_type('IfcProduct') if not p.is_a('IfcSpace') and not p.is_a('IfcOpeningElement') and not p.is_a('IfcAnnotation') and any(r.RepresentationIdentifier=='Body' for r in getattr(getattr(p,'Representation',None),'Representations',[]) or [])}
                row['expected_body_objects'] = len(expected)
                client.call('Page.navigate', {'url':'http://127.0.0.1:4178/ifc-viewer/index.html'})
                for _ in range(150):
                    time.sleep(.1)
                    if client.js('!!globalThis.__PARSER_READY__'): break
                else: raise RuntimeError('Parser bootstrap timeout')
                doc = client.call('DOM.getDocument')['root']['nodeId']
                node = client.call('DOM.querySelector', {'nodeId':doc, 'selector':'#file'})['nodeId']
                start = time.monotonic()
                client.call('DOM.setFileInputFiles', {'nodeId':node, 'files':[qa.winpath(path)]})
                for _ in range(300):
                    time.sleep(.15)
                    if client.js('!!globalThis.__IFC_READY__'): break
                    error = client.js('globalThis.__IFC_ERROR__||null')
                    if error: raise RuntimeError(error)
                else: raise RuntimeError('File loading deadline exceeded')
                report = client.js('__viewer.report()')
                row['load_wall_seconds'] = round(time.monotonic()-start, 3)
                row['parsed_objects'] = report['geometry']['renderedProducts']; row['triangles'] = report['geometry']['triangles']
                row['parser'] = report['parser']['name']; row['diagnostic_count'] = len(report.get('diagnostics', []))
                records = {r['id']:r for r in report['sourceProducts']}
                rendered = set(client.js('__viewer.snapshot().visible'))
                row['missing_expected_ids'] = sorted(set(expected) - rendered)
                row['guids_match'] = all(records[i]['guid'] == guid for i, guid in expected.items() if i in rendered)
                row['load_success'] = report['source']['name'] == path.name and row['parsed_objects'] > 0 and row['triangles'] > 0
                from collections import Counter
                expected_classes = dict(Counter(p.is_a() for p in source.by_type('IfcProduct') + source.by_type('IfcProject')))
                actual_classes = client.js('Object.fromEntries(Array.from(document.querySelectorAll(".tree-category")).map(e=>[e.dataset.type,e.querySelectorAll(".tree-leaf").length]))')
                row['model_tree_classes_match_source'] = actual_classes == expected_classes
                row['model_tree_objects'] = client.js('document.querySelectorAll(".tree-leaf").length')
                (output / (sample['id']+'-parser.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
                client.button('fit'); time.sleep(.2)
                shot = client.call('Page.captureScreenshot', {'format':'png','fromSurface':True})
                (output / (sample['id']+'.png')).write_bytes(base64.b64decode(shot['data']))
                # Exercise actual pointer controls; no hidden state mutation.
                before = client.js('__viewer.camera()')
                client.call('Input.dispatchMouseEvent', {'type':'mousePressed','x':660,'y':450,'button':'left','clickCount':1})
                for dx in [8,16,24,32]: client.call('Input.dispatchMouseEvent', {'type':'mouseMoved','x':660+dx,'y':450,'button':'left','buttons':1})
                client.call('Input.dispatchMouseEvent', {'type':'mouseReleased','x':692,'y':450,'button':'left','clickCount':1})
                row['rotation_works'] = before['position'] != client.js('__viewer.camera()')['position']
                zoom = client.js('__viewer.camera().zoom')
                client.call('Input.dispatchMouseEvent', {'type':'mouseWheel','x':660,'y':450,'deltaX':0,'deltaY':-120})
                row['zoom_works'] = zoom != client.js('__viewer.camera().zoom')
                client.button('fit')
                candidates = client.js('__viewer.snapshot().visible.slice(0,100).map(id=>({id,p:__viewer.project(id)}))')
                row['pick_hide_restore'] = False
                for candidate in candidates:
                    p = candidate['p']
                    if not p or not (70 < p['x'] < 1000 and 250 < p['y'] < 740): continue
                    client.click(p['x'],p['y']); picked = client.js('__viewer.state().inspected')
                    if picked is None: continue
                    camera = client.js('__viewer.camera()')
                    client.click(p['x'],p['y'],button='right')
                    if client.js('document.getElementById("context").hidden'): continue
                    client.button('hide')
                    hidden = client.js('__viewer.snapshot().visible')
                    valid = len(hidden) == len(rendered)-1 and picked not in hidden and camera == client.js('__viewer.camera()')
                    client.button('undoHide'); restored = client.js('__viewer.snapshot().visible')
                    row['pick_hide_restore'] = valid and len(restored)==len(rendered)
                    client.click(p['x'],p['y']); prop_id=client.js('__viewer.state().inspected')
                    client.button('propertiesBtn'); time.sleep(.3)
                    prop_text=client.js('document.getElementById("properties").textContent')
                    row['readable_property_identity'] = prop_id is not None and str(source.by_id(prop_id).GlobalId) in prop_text
                    payload=client.js('document.querySelector("#rawProperty pre")?.textContent||null')
                    row['property_read_errors'] = len(json.loads(payload)['errors']) if payload else None
                    client.button('closeProperty')
                    break
                row['outcome'] = 'loaded_with_diagnostics' if row['diagnostic_count'] or row['missing_expected_ids'] else 'loaded_clean'
            except Exception as error:
                row.update(load_success=False, outcome='failed_or_unavailable', error=str(error))
            finally:
                row['source_unchanged'] = original is not None and path.read_bytes() == original
                results.append(row)
                (output / 'results.json').write_text(json.dumps({'label':label,'scope':'12-file IFC2X3 smoke; not validator/full surface certification','browser':'Edge headless SwiftShader WebGL2','repair_called':False,'results':results},ensure_ascii=False,indent=2),encoding='utf8')
                print(json.dumps(row,ensure_ascii=False),flush=True)
        return results
    finally:
        if client:
            try: client.call('Browser.close')
            except Exception: pass
        try: process.wait(timeout=5)
        except subprocess.TimeoutExpired: process.terminate()
        log.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', action='store_true')
    parser.add_argument('--run')
    args = parser.parse_args()
    if args.catalog: catalog()
    if args.run: run(args.run)
