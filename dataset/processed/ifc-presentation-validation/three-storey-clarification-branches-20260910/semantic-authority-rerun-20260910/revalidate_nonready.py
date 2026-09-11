"""Scoped revalidation within the admitted Generation stage; no network."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parents[3]
CHANGED = {'src/text2ifc_agent/semantic_requirements.py', 'tests/agent/test_semantic_authority_completeness.py'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def main():
    validation = OUT/'validation-nonready'
    current = read(OUT/'admission.json')
    if sys.argv[1:] == ['--capture']:
        validation.mkdir(exist_ok=False)
        drift = {p for p,digest in current['files_sha256'].items() if sha(ROOT/p) != digest}
        assert drift == CHANGED, drift
        write(validation/'bound-inputs.json', {p:sha(ROOT/p) for p in current['files_sha256']})
        return
    captured = read(validation/'bound-inputs.json')
    assert all(sha(ROOT/p)==digest for p,digest in captured.items())
    for suffix in ['xml', 'log']:
        for name in ['nonready-authority-red-20260910', 'nonready-authority-scoped-20260910']:
            shutil.copyfile(ROOT/'.tmp'/(name+'.'+suffix), validation/(name+'.'+suffix))
    tree = ET.parse(validation/'nonready-authority-scoped-20260910.xml')
    cases = list(tree.getroot().iter('testcase'))
    assert len(cases) == 76, len(cases)
    assert all(not any(t.find(k) is not None for k in ['failure','error','skipped']) for t in cases)
    prior = OUT/'admission-before-nonready.json'
    assert not prior.exists()
    shutil.copyfile(OUT/'admission.json', prior)
    current['scoped_revalidation'] = {'prior_admission':prior.relative_to(ROOT).as_posix(),
        'prior_admission_sha256':sha(prior), 'tests':len(cases), 'all_passed':True,
        'changed_paths':sorted(CHANGED), 'new_tests':3,
        'reason':'Only strengthen unresolved authority for non-ready/partial Briefs. Ready semantics remain unchanged. Revalidated complete extraction, source and scope guards, both Brief entry seams, clarification/resume, semantic atomic cleanup and publication/resume family.',
        'xml':(validation/'nonready-authority-scoped-20260910.xml').relative_to(ROOT).as_posix()}
    current['effective_unique_tests'] += 3
    current['files_sha256'] = captured
    current['files_sha256'].update({p.relative_to(ROOT).as_posix():sha(p) for p in validation.iterdir()})
    current['files_sha256'][prior.relative_to(ROOT).as_posix()] = sha(prior)
    current['files_sha256'][Path(__file__).relative_to(ROOT).as_posix()] = sha(Path(__file__))
    (OUT/'admission.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('SCOPED REVALIDATION PASSED:',len(cases),'tests; effective stage cases',current['effective_unique_tests'])


if __name__ == '__main__':
    main()
