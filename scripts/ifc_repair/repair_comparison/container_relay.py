"""Network relay: fixed host controller, no keys, arbitrary URLs or GET proxy."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import http.client
import os
import re

HOST_PORT = int(os.environ['REPAIR_CONTROLLER_PORT'])


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def do_POST(self):
        if not re.fullmatch(r'/[a-f0-9]{32}/(?:v1/(?:messages|chat/completions)|questions)', self.path):
            self.send_error(404)
            return
        length = int(self.headers.get('Content-Length', '0'))
        if not 0 < length <= 64*1024*1024:
            self.send_error(413)
            return
        body = self.rfile.read(length)
        headers = {k:v for k,v in self.headers.items() if k.lower() not in {'host','connection','transfer-encoding'}}
        connection = http.client.HTTPConnection('host.docker.internal', HOST_PORT, timeout=7200)
        try:
            connection.request('POST', self.path, body, headers)
            response = connection.getresponse()
            self.send_response(response.status)
            self.send_header('Content-Type',response.getheader('Content-Type','application/json'))
            self.send_header('Connection','close')
            self.end_headers()
            while chunk := response.read1(65536):
                self.wfile.write(chunk)
                self.wfile.flush()
        finally:
            connection.close()
            self.close_connection = True
    def log_message(self,*args):
        pass


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0',8000),Handler).serve_forever()
