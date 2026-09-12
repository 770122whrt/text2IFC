"""Supplemental evaluator: compare requested HEX at its specified 8-bit precision.

Preserves the original strict-float report. Geometry and all other checks are
copied without changing their verdicts. Source IFC SHA must match that report.
"""
import argparse, copy, hashlib, json, math
from pathlib import Path
import ifcopenshell
from text2ifc_presentation import item_appearance_signatures


def matches_hex8(signatures, hex_color):
    if len(signatures) != 1: return False
    values = [signatures[0].get(k) for k in ('red','green','blue')]
    if any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or not 0<=v<=1 for v in values): return False
    wanted = [int(hex_color[i:i+2],16) for i in (1,3,5)]
    return [math.floor(v*255+.5) for v in values] == wanted


def matches_part_styles(actual, requested):
    for part, channels in requested.items():
        values = actual.get(part, [])
        if not values or any(len(v)!=1 for v in values): return False
        if 'color' in channels:
            color = '#'+''.join(f'{math.floor(v*255+.5):02X}' for v in channels['color'])
            if not all(matches_hex8(v,color) for v in values): return False
        if 'transparency' in channels and not all(math.isclose(v[0]['transparency'],channels['transparency'],rel_tol=0,abs_tol=1e-6) for v in values): return False
    return True


def run(ifc, original):
    source = json.loads(Path(original).read_text(encoding='utf-8'))
    result = copy.deepcopy(source.get('independent',source))
    assert result['ifc_sha256'] == hashlib.sha256(Path(ifc).read_bytes()).hexdigest()
    model = ifcopenshell.open(str(ifc))
    for check in result['checks']:
        if check['check'].endswith(':part_colors'):
            from text2ifc_presentation.part_readback import read_part_styles
            product = model.by_guid(result['matches'][check['check'][:-12]])
            styles = read_part_styles(product)
            check['prior_strict_float_passed'] = check['passed']
            check['actual'] = styles
            check['passed'] = matches_part_styles(styles,check['expected'])
            continue
        if not check['check'].endswith(':color'): continue
        label = check['check'][:-6]
        product = model.by_guid(result['matches'][label])
        items = [i for r in product.Representation.Representations if r.RepresentationIdentifier=='Body' for i in r.Items]
        styles = [item_appearance_signatures(i) for i in items]
        check['prior_strict_float_passed'] = check['passed']
        check['actual'] = styles
        check['passed'] = bool(items) and all(matches_hex8(s,check['expected']) for s in styles)
    result['passed'] = all(c['passed'] for c in result['checks'])
    result['evaluation_revision'] = 'requested-hex8-readback/2.1'
    result['prior_report_sha256'] = hashlib.sha256(Path(original).read_bytes()).hexdigest()
    result['revision_reason'] = 'HEX requests define 8-bit RGB for whole elements and parts. Compare round-half-up reconstructed bytes, retaining ambiguity and range rejection; no tolerance change to geometry, materials or transparency.'
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('ifc');p.add_argument('original');p.add_argument('output');a=p.parse_args()
    result=run(a.ifc,a.original)
    with Path(a.output).open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'passed':result['passed'],'checks':len(result['checks']),'failures':[c['check'] for c in result['checks'] if not c['passed']]}))
