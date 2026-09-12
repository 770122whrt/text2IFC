import hashlib
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen

root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root), str(root / 'src')]
from scripts.proof.package import validate_package

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        self.urls += [v for k, v in attrs if k in {'href', 'src'} and v]

summary = {}
for workflow, phase, case_id in [('generation','phase6.6','reception-basic-fillings'),
                                 ('repair','phase12.1','vvo-instance-properties')]:
    collection = root / 'dataset/processed/proof' / workflow / phase / 'semantic-appearance-20260908'
    case = collection / case_id
    manifest = json.loads((collection / 'review-manifest.json').read_text(encoding='utf-8'))
    assert manifest['registration_status'] == 'unregistered'
    assert not (collection / 'manifest.json').exists()
    links = 0
    files = [collection/'README.md', collection/'REPORT.md', collection/'index.html',
             case/'REPORT.md', case/'REPORT.html', case/'request.html', case/'evidence/README.md']
    for path in files:
        text = path.read_text(encoding='utf-8')
        if path.suffix == '.md':
            urls = re.findall(r'\]\(([^)]+)\)', text)
        else:
            parser = Links()
            parser.feed(text)
            urls = parser.urls
        for url in urls:
            parsed = urlsplit(url)
            if parsed.scheme or not parsed.path:
                continue
            assert (path.parent / unquote(parsed.path)).resolve().exists(), (path, url)
            links += 1
    request = (case / 'request.txt').read_bytes()
    served = f'http://127.0.0.1:8768/{workflow}/{phase}/semantic-appearance-20260908/{case_id}/request.txt'
    with urlopen(served) as response:
        assert response.headers.get_content_charset() == 'utf-8'
        assert response.read() == request
    body = re.search(r'<pre>(.*?)</pre>', (case/'request.html').read_text(encoding='utf-8'), re.S).group(1)
    assert html.unescape(body) == request.decode('utf-8').replace('\r\n','\n')
    validation = validate_package(collection, manifest)
    assert validation['status'] == 'passed', validation
    summary[workflow] = {**validation, 'human_links_checked': links, 'utf8_http_body_unchanged': True,
                          'request_html_text_equal': True, 'registration': 'unregistered'}
    (collection/'presentation-validation.json').write_text(json.dumps(summary[workflow],ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
