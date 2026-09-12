import copy
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
old = root / 'dataset/processed/ifc-presentation-validation/three-storey-human-review-20260909'
out = root / 'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910'
out.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
question = '参考 IFC 中，一层通往二层的楼梯接近北端平台时，被上方反向梯段遮挡，局部净空为零。请确认是调整楼梯及关联布局，还是保留原要求并在 Audit 和报告中记录这个问题。'
answers = {
    'A-revise': '我选择调整内部布局，不向外扩建。三层分隔墙均向西移动300毫米，保持200毫米厚，改为X=7300～7500、Y=0～8400。各层大厅净范围改为X=0～7300、Y=0～8400，楼梯间净范围改为X=7500～10000、Y=0～8400。第一段楼梯仍从南向北上升，平面改为X=7500～8700、Y=1500～6900；第二段仍从北向南上升，平面改为X=8800～10000、Y=1500～6900。两段仍各宽1200毫米，18个踢面高175毫米、18个踏面深300毫米，起止标高不变。二层楼板洞口改为X=7500～8700、Y=1500～6900；三层洞口改为X=8800～10000、Y=1500～6900，各自穿透所属楼板，不再保留原位置洞口。二层北端平台及三层南端平台的X范围均改为7500～10000，Y范围不变；首层楼梯间空间同样从X=7500开始。三樘分隔墙门随墙向西移动300毫米，南北位置、宽高及开启侧不变。建筑外轮廓、楼层标高、外墙门窗、材料、配色及其他原要求均不变。我接受每层大厅减少2.52平方米。请保留这次修订记录，Audit 仍须说明未做完整工程和规范审查。',
    'B-retain': '我已知悉两段反向楼梯在同一平面相互遮挡，接近二层北端平台处局部净空为零，无法作为正常通行楼梯使用。本分支用于忠实建模和问题展示，请仍严格按原始请求中的尺寸、位置、方向、洞口与关系生成，不要移动楼梯或修改大厅、分隔墙、门窗来消除这个问题。请在 Audit 和交付报告中保留问题位置、影响以及我的保留决定，不得写成合理性或建筑规范检查通过。其他原要求不变。',
}
for branch, answer in answers.items():
    case = out / branch
    case.mkdir(exist_ok=False)
    (case / 'request.txt').write_bytes((old / 'request.txt').read_bytes())
    turns = [
        {'turn_id': 'turn-user-001', 'role': 'user', 'content': (old / 'request.txt').read_text(encoding='utf-8').rstrip('\r\n'), 'question_ids': []},
        {'turn_id': 'turn-assistant-002', 'role': 'assistant', 'content': question, 'question_ids': ['design-review-choice']},
        {'turn_id': 'turn-user-003', 'role': 'user', 'content': answer, 'question_ids': ['design-review-choice']},
    ]
    def write(name, value):
        (case / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write('conversation.json', turns)
    (case / 'clarification.txt').write_text(
        '来源：用户已授权的受控分支测试脚本，由 Codex 整理；不是 Provider 现场提问，也不是逐字真人回答记录。\n\n问题：' + question + '\n\n分支回答：' + answer + '\n', encoding='utf-8')
    write('reference.json', {
        'role': 'immutable reference of the same Generation case; not Repair source or private Gold',
        'ifc_path': (old / 'generated.ifc').relative_to(root).as_posix(), 'ifc_sha256': sha(old / 'generated.ifc'),
        'request_sha256': sha(old / 'request.txt'),
        'decision_origin': 'user-authorized scripted branch; A authorized internal shift or expansion, Codex selected internal shift',
        'reference_review_path': (old / 'stair-clearance-diagnostic.json').relative_to(root).as_posix(),
    })
    (case / 'reference-review.json').write_bytes((old / 'stair-clearance-diagnostic.json').read_bytes())
    expected = json.loads((old / 'frozen-expectations.json').read_text(encoding='utf-8'))
    expected['conversation_sha256'] = sha(case / 'conversation.json')
    expected['purpose'] = 'controlled related A/B development branch; not blind capability evidence'
    if branch == 'A-revise':
        expected['wall_intervals_mm']['partition'][1] = [7300, 7500]
        for bounds in expected['spaces_mm']:
            bounds[0] = [0, 7300] if bounds[0][0] == 0 else [7500, 10000]
        for i, interval in enumerate([[7500, 8700], [8800, 10000]]):
            expected['stairs'][i]['bbox_mm'][0] = interval
            expected['openings_mm'][i][0] = interval
    write('frozen-expectations.json', expected)
    checker = (old / 'check_ifc_v2.py').read_text(encoding='utf-8')
    checker = checker.replace("m=ifcopenshell.open(str(source))", "assert hashlib.sha256((base/'conversation.json').read_bytes()).hexdigest()==expected['conversation_sha256']\nm=ifcopenshell.open(str(source))")
    (case / 'check_ifc.py').write_text(checker, encoding='utf-8')
    write('review-status.json', {'status': 'prepared_not_run', 'human_review_status': 'pending', 'proof_registration_status': 'unregistered'})
preview = {
    'destination': 'https://api.deepseek.com', 'model': 'deepseek-v4-flash',
    'scope': 'Two controlled branches of the frozen three-storey Generation case, with real Brief/Generator/Audit responses. No old raw IFC file will be sent to the Provider.',
    'branches': {b: json.loads((out / b / 'conversation.json').read_text(encoding='utf-8')) for b in answers},
    'reference_diagnostic': json.loads((old / 'stair-clearance-diagnostic.json').read_text(encoding='utf-8')),
    'subsequent_payload': 'Only these branch conversations, their Briefs/candidates, versioned prompts/schema, automated checks, acknowledged design review context and run metadata. No Repair IFC, private Gold, other task data, or credential text.',
    'budget_per_branch': {'max_calls': 6, 'max_tokens': 800000, 'max_active_seconds': 1800},
    'strategy': 'legacy_full', 'approval_required_before_transport': True,
}
(out / 'payload-preview.json').write_text(json.dumps(preview, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(out)
