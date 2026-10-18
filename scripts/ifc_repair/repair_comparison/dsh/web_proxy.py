"""Opt-in, credential-free public HTTP/HTTPS proxy for native DSH page reads."""
import http.client
import ipaddress
import os
import select
import socket
import time
from urllib.parse import urlsplit


def _public_literal(host):
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return
    if not address.is_global:
        raise ValueError('PUBLIC_DESTINATION_REQUIRED')


def http_target(value):
    if any(ord(c) <= 32 or ord(c) == 127 for c in value):
        raise ValueError('INVALID_PROXY_URL')
    url = urlsplit(value)
    if (url.scheme != 'http' or not url.hostname or url.username is not None
            or url.password is not None or url.fragment or url.port not in (None, 80)):
        raise ValueError('PUBLIC_HTTP_PORT_REQUIRED')
    _public_literal(url.hostname)
    return url.hostname, (url.path or '/') + ('?' + url.query if url.query else '')


def public_addresses(host, port):
    addresses = []
    for family, _, _, _, address in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(address[0]).is_global:
            raise ValueError('PUBLIC_DESTINATION_REQUIRED')
        item = (family, address)
        if item not in addresses:
            addresses.append(item)
    if not addresses:
        raise OSError('NO_PUBLIC_ADDRESS')
    return addresses


def open_public_socket(host, port):
    # Connect to the checked addresses themselves; never resolve a second time.
    error = None
    for family, address in public_addresses(host, port)[:3]:
        stream = socket.socket(family, socket.SOCK_STREAM)
        stream.settimeout(10)
        try:
            stream.connect(address)
            return stream
        except OSError as failure:
            error = failure
            stream.close()
    raise error or OSError('PUBLIC_CONNECT_FAILED')


class WebProxyMixin:
    """Add public GET and HTTPS CONNECT without opening controller POST routes."""
    def do_GET(self):
        if os.environ.get('REPAIR_WEB_PROXY') != '1':
            self.send_error(403)
            return
        connection = None
        sent = False
        try:
            host, path = http_target(self.path)
            connection = http.client.HTTPConnection(host, 80, timeout=30)
            connection.sock = open_public_socket(host, 80)
            headers = {name: self.headers[name] for name in ('User-Agent', 'Accept') if name in self.headers}
            headers.update({'Host': host, 'Accept-Encoding': 'identity', 'Connection': 'close'})
            connection.request('GET', path, headers=headers)
            response = connection.getresponse()
            self.send_response(response.status)
            for name in ('Content-Type', 'Location'):
                if value := response.getheader(name):
                    self.send_header(name, value)
            self.send_header('Connection', 'close')
            self.end_headers()
            sent = True
            remaining = 5_000_000
            while remaining and (chunk := response.read1(min(65536, remaining))):
                remaining -= len(chunk)
                self.wfile.write(chunk)
                self.wfile.flush()
        except ValueError:
            if not sent: self.send_error(403)
        except (OSError, http.client.HTTPException):
            if not sent: self.send_error(502)
        finally:
            if connection is not None: connection.close()
            self.close_connection = True

    def do_CONNECT(self):
        if os.environ.get('REPAIR_WEB_PROXY') != '1':
            self.send_error(403)
            return
        upstream = None
        sent = False
        try:
            if any(ord(c) <= 32 or ord(c) == 127 for c in self.path):
                raise ValueError('INVALID_CONNECT_AUTHORITY')
            url = urlsplit('https://' + self.path)
            if (not url.hostname or url.port != 443 or url.username is not None
                    or url.password is not None or url.path or url.query or url.fragment):
                raise ValueError('PUBLIC_HTTPS_PORT_REQUIRED')
            upstream = open_public_socket(url.hostname, 443)
            self.send_response(200, 'Connection established')
            self.end_headers()
            self.wfile.flush()
            sent = True
            self.connection.settimeout(30)
            upstream.settimeout(30)
            deadline, remaining = time.monotonic() + 60, 16 * 1024 * 1024
            while remaining > 0 and time.monotonic() < deadline:
                ready, _, _ = select.select([self.connection, upstream], [], [], 30)
                if not ready: break
                for source in ready:
                    chunk = source.recv(min(65536, remaining))
                    if not chunk: return
                    remaining -= len(chunk)
                    target = upstream if source is self.connection else self.connection
                    target.sendall(chunk)
        except ValueError:
            if not sent: self.send_error(403)
        except OSError:
            if not sent: self.send_error(502)
        finally:
            if upstream is not None: upstream.close()
            self.close_connection = True
