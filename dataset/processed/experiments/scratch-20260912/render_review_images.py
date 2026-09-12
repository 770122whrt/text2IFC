import json
import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
base = root / 'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01/generation'
report = json.loads((base / 'independent-review.json').read_text(encoding='utf-8'))
selections = [('all', 'overall.png'), *[(r['guid'], {'south': 'door.png', 'east': 'window-double.png', 'west': 'window-single.png'}[r['side']]) for r in report['fillings']]]
for selection, name in selections:
    subprocess.run([sys.executable, str(root / '.tmp/export_ifc_review_png.py'), str(base / 'review.html'),
                    str(base / name), '--selection', selection], check=True)
