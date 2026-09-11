from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.request import urlopen

import pytest

from scripts.presentation.serve_review import ReviewHandler


@pytest.mark.parametrize('suffix', ['txt', 'md', 'json'])
def test_review_text_declares_utf8_without_changing_evidence_bytes(tmp_path, suffix):
    content = '中文请求：砖墙与透明玻璃。'.encode('utf-8')
    (tmp_path / f'request.{suffix}').write_bytes(content)
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(ReviewHandler, directory=str(tmp_path)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f'http://127.0.0.1:{server.server_port}/request.{suffix}') as response:
            assert response.headers.get_content_charset() == 'utf-8'
            assert response.read() == content
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
