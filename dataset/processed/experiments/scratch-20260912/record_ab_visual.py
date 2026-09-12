"""Record the assistant's completed inspection, separate from human acceptance."""
import hashlib
import json
from pathlib import Path
import sys

branch = sys.argv[1]
assert branch in ('A-revise', 'B-retain')
folder = Path(__file__).resolve().parents[1]/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910'/branch
images = {}
for name in ('overall', 'cutaway', 'window-double', 'door'):
    p = folder/'views'/(name+'.png')
    images[p.relative_to(folder).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
result = dict(status='assistant_review_complete', reviewer='Codex assistant',
    method='Viewed four PNGs rendered from this IFC native mesh; not AI concept images or interactive viewer inspection.',
    human_acceptance='pending', proof_registration=False, images_sha256=images,
    observations=[
        '三层体量与门窗排列整齐；暖浅墙面与深色边框协调。',
        '双竖面板窗的外框、中梃与两块玻璃可见，玻璃和框采用不同样式。',
        '门框与门扇完整可见、分色明确；没有添加五金细节。',
        '内部剖切显示楼层、分隔墙、门与梯段；隐藏项只属于视图。',
        ('A的梯段按已批准内部修订分开；净空结论来自独立测量。' if branch=='A-revise'
         else 'B保留共用平面的反向梯段；已知净空缺陷不因外观检查而消除。')],
    limitations='Static diagnostic views, not full building-code, engineering or all-angle appearance certification.')
with (folder/'visual-review.json').open('x', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(branch, result['status'])
