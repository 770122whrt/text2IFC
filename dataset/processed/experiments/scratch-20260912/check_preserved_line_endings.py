"""Check existing staged-diff diagnostics without reopening a file for every line."""
import json
from pathlib import Path
import re

text=Path('.tmp/typed-attempt-staged-diff-check.log').read_text(encoding='utf-8')
cache={}
counts={'original_crlf':0,'raw_test_trace_whitespace':0}
for match in re.finditer(r'^(.+):(\d+): (trailing whitespace\.|new blank line at EOF\.)$',text,re.MULTILINE):
    path,number=match.group(1),int(match.group(2))
    if path not in cache: cache[path]=Path(path).read_bytes().split(b'\n')
    if cache[path][number-1].endswith(b'\r'):
        counts['original_crlf']+=1
    else:
        assert path.endswith(('.xml','.log')),match.group(0)
        counts['raw_test_trace_whitespace']+=1
assert counts['original_crlf']
print(json.dumps({'known_evidence_only':True,'files':len(cache),'findings':counts}))
