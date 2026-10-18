"""Read-only experiment snapshot and report assets; never run/score a repair.

Only this report's directory is written. Run with the bundled Python runtime
(ReportLab), then rasterize progress.svg with the existing bundled Sharp.
"""
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))
from scripts.ifc_repair.repair_comparison.budget import normalize_usage

TERMINAL = {'submitted', 'no_output', 'runtime_error', 'budget_exhausted', 'unsupported', 'cancelled'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def snapshot(root, selected=None):
    # No Ledger construction, CREATE TABLE, PRAGMA write, or model access.
    db = sqlite3.connect((root / 'control.sqlite').absolute().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute('BEGIN')
        states = [json.loads(r['state']) for r in db.execute('SELECT state FROM runs ORDER BY run_id')]
        calls = [dict(r) for r in db.execute('SELECT run_id,state,usage,metadata,response FROM calls ORDER BY rowid')]
    finally:
        db.close()
    rows = []
    for state in states:
        if selected is not None and state['run_id'] not in selected:
            continue
        associated = [c for c in calls if c['run_id'] == state['run_id']]
        known, unknown = 0, 0
        for call in associated:
            usage = json.loads(call['usage']) if call['usage'] else None
            metadata = json.loads(call['metadata']) if call['metadata'] else {}
            response = json.loads(call['response']) if call['response'] else {}
            protocol = metadata.get('wire_protocol', 'chat')
            complete = protocol != 'messages' or response.get('usage_complete', response.get('stream_complete')) is True
            normalized = normalize_usage(usage, protocol=protocol, complete=complete) if call['state'] != 'inflight' else None
            if normalized is None:
                unknown += 1
            else:
                known += normalized['total_tokens']
        score_file = root / 'evaluation' / (state['run_id'] + '.json')
        score = read(score_file) if score_file.exists() else {}
        result = score.get('metrics', {}).get('task_success', {}).get('value')
        rows.append({
            'run_id': state['run_id'], 'case_id': state['case_id'], 'arm': state['arm'],
            'status': state['status'], 'terminal': state['status'] in TERMINAL,
            'submitted': state['status'] == 'submitted',
            'strict_success': result if isinstance(result, bool) else None,
            'score_path': str(score_file.relative_to(REPO)),
            'known_tokens': known, 'unknown_calls': unknown, 'calls': len(associated),
            'active_seconds': state['active_elapsed_s'],
        })
    return {
        'root': str(root.relative_to(REPO)), 'rows': rows,
        'inflight_calls': sum(c['state'] == 'inflight' for c in calls),
        'terminal': sum(r['terminal'] for r in rows),
        'scored_terminal': sum(r['terminal'] and isinstance(r['strict_success'], bool) for r in rows),
        'known_tokens': sum(r['known_tokens'] for r in rows),
        'unknown_calls': sum(r['unknown_calls'] for r in rows),
    }


def collect():
    baseline = snapshot(REPO / '.tmp/repair-comparison-formal-live')
    fresh = snapshot(REPO / '.tmp/repair-comparison-b-first-five-revalidation',
                     {f'formal-{n:03d}-B' for n in range(1, 6)})
    cases = []
    for folder in sorted((REPO / 'dataset/processed/ifc-repair/repair-comparison/formal').glob('formal-*')):
        task = read(folder / 'private/task.json')
        source = task['source']
        review = task['review']
        cases.append({
            'case_id': folder.name, 'asset_id': source['asset_id'],
            'file': Path(source['source_path']).name, 'source_path': source['source_path'],
            'license': source['license'], 'source_url': source.get('rights_source_url'),
            'source_sha256': task['source_sha256'], 'profile': task['damage_profile'],
            'clarification_required': task['clarification_required'],
            'review_status': review.get('status'), 'human_viewed': review.get('human_viewed'),
        })
    arms = {}
    for arm in 'ABCD':
        rows = [r for r in baseline['rows'] if r['arm'] == arm]
        arms[arm] = {
            'planned': len(rows), 'terminal': sum(r['terminal'] for r in rows),
            'submitted': sum(r['submitted'] for r in rows),
            'scored': sum(r['terminal'] and isinstance(r['strict_success'], bool) for r in rows),
            'passed': sum(r['terminal'] and r['strict_success'] is True for r in rows),
            'scored_failed': sum(r['terminal'] and r['strict_success'] is False for r in rows),
            'pending_score': sum(r['terminal'] and r['strict_success'] is None for r in rows),
            'not_started': sum(r['status'] == 'ready' for r in rows),
            'statuses': dict(Counter(r['status'] for r in rows)),
        }
    value = {
        'captured_at_beijing': datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),
        'role': 'weekly_report_read_only_snapshot_not_final_benchmark',
        'baseline': baseline, 'development_first_five': fresh, 'arms': arms, 'cases': cases,
        'licenses': dict(Counter(c['license'] for c in cases)),
        'damage_levels': dict(Counter(c['profile']['level'] for c in cases)),
        'targets': sum(c['profile']['target_count'] for c in cases),
        'components': dict(sum((Counter(c['profile']['targets']) for c in cases), Counter())),
        'notes': ['Original attempts and revealed development revalidation are separate.',
            'Only persisted independent score booleans count as scored; null is pending.',
            'Versions differ within the original batch; this figure is progress, not a ranking.'],
    }
    (HERE / 'evidence.json').write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    figures = HERE / 'figures'
    figures.mkdir(exist_ok=True)
    asset_sources = []
    for case in ['formal-001', 'formal-004', 'formal-005']:
        source = REPO / 'dataset/processed/ifc-repair/repair-comparison/formal' / case / 'REVIEW.png'
        target = figures / (case + '-damage.png')
        shutil.copyfile(source, target)
        asset_sources.append({'file': str(target.relative_to(HERE)), 'source': str(source.relative_to(REPO)),
            'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'role': 'actual_IFC_G_D_mesh_section_not_repair_output'})
    (HERE / 'image-sources.json').write_text(json.dumps(asset_sources, indent=2) + '\n', encoding='utf8')
    return value


def draw_progress(value):
    from reportlab.graphics.charts.barcharts import HorizontalBarChart
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.graphics import renderPDF, renderSVG
    from reportlab.lib.colors import HexColor, white

    drawing = Drawing(960, 405)
    drawing.add(Rect(0, 0, 960, 405, fillColor=white, strokeColor=None))
    drawing.add(String(35, 365, 'Repair comparison: execution and scoring progress',
                       fontName='Helvetica-Bold', fontSize=19, fillColor=HexColor('#243B53')))
    total = value['baseline']['terminal']
    scored = value['baseline']['scored_terminal']
    drawing.add(String(35, 338, f'{total}/80 terminal tasks | {scored} scored | '
                       f'{total - scored} scores pending | {80 - total} not started',
                       fontName='Helvetica', fontSize=12, fillColor=HexColor('#526777')))

    chart = HorizontalBarChart()
    chart.x, chart.y, chart.width, chart.height = 236, 106, 677, 193
    keys = ['passed', 'scored_failed', 'pending_score', 'not_started']
    order = 'DCBA'
    chart.data = [[value['arms'][arm][key] for arm in order] for key in keys]
    chart.categoryAxis.categoryNames = ['D  Official DSH', 'C  GPT-6 Sol + generic', 'B  Repair Harness', 'A  DeepSeek + generic']
    chart.categoryAxis.labels.fontName = 'Helvetica'
    chart.categoryAxis.labels.fontSize = 12
    chart.categoryAxis.labels.dx = -9
    chart.categoryAxis.labels.boxAnchor = 'e'
    chart.categoryAxis.style = 'stacked'
    chart.categoryAxis.strokeColor = None
    chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = 0, 20, 5
    chart.valueAxis.labels.fontName = 'Helvetica'
    chart.valueAxis.labels.fontSize = 10
    chart.valueAxis.strokeColor = HexColor('#B3C1C9')
    chart.valueAxis.tickDown = 4
    chart.valueAxis.visibleGrid = True
    chart.valueAxis.gridStrokeColor = HexColor('#EBEFF2')
    chart.barWidth = 26
    chart.barLabels.fontName = 'Helvetica-Bold'
    chart.barLabels.fontSize = 10
    chart.barLabels.boxAnchor = 'c'
    chart.barLabels.boxTarget = 'mid'
    chart.barLabelFormat = lambda number: str(int(number)) if number else ''
    colors = ['#2A9D8F', '#E76F51', '#E9C46A', '#DDE5EA']
    for i, color in enumerate(colors):
        chart.bars[i].fillColor = HexColor(color)
        chart.bars[i].strokeColor = white
        chart.bars[i].strokeWidth = .8
    drawing.add(chart)
    legend = ['Strict pass', 'Scored: not passed', 'Score pending', 'Not started']
    for index, (label, color) in enumerate(zip(legend, colors)):
        x = 70 + index * 222
        drawing.add(Rect(x, 55, 17, 11, fillColor=HexColor(color), strokeColor=None))
        drawing.add(String(x + 25, 55, label, fontName='Helvetica', fontSize=11, fillColor=HexColor('#243B53')))
    drawing.add(String(35, 24, '20 tasks planned per arm. Mixed execution versions; incomplete batch. Progress only, not a performance ranking.',
                       fontName='Helvetica', fontSize=9, fillColor=HexColor('#526777')))
    svg = HERE / 'figures/progress.svg'
    renderSVG.drawToFile(drawing, str(svg))
    # Windows rasterizers need an installed CSS family, whereas the PDF uses
    # its built-in Helvetica metrics. Arial has matching practical metrics.
    svg.write_text(svg.read_text(encoding='utf8').replace(
        'font-family: Helvetica-Bold;', 'font-family: Arial; font-weight: bold;').replace(
        'font-family: Helvetica;', 'font-family: Arial;'), encoding='utf8')
    renderPDF.drawToFile(drawing, str(HERE / 'figures/progress.pdf'))


if __name__ == '__main__':
    value = read(HERE / 'evidence.json') if '--figures-only' in sys.argv else collect()
    draw_progress(value)
    print(json.dumps({k: value[k] for k in ['captured_at_beijing', 'arms', 'licenses', 'damage_levels', 'targets', 'components']}, ensure_ascii=False))
