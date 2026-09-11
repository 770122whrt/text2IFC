"""Serve local review artifacts without modifying their frozen bytes."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class ReviewHandler(SimpleHTTPRequestHandler):
    def guess_type(self, path):
        if Path(path).suffix.lower() in {'.txt', '.md'}:
            return 'text/plain; charset=utf-8'
        content_type = super().guess_type(path)
        if content_type.startswith('text/') or content_type in {'application/json', 'application/javascript'}:
            return content_type + '; charset=utf-8'
        return content_type


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--port', default=8768, type=int)
    args = parser.parse_args()
    directory = args.root.resolve(strict=True)
    if not directory.is_dir():
        parser.error('--root must be a directory')
    handler = partial(ReviewHandler, directory=str(directory))
    with ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
        print(f'Local UTF-8 review: http://127.0.0.1:{server.server_port}/', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
