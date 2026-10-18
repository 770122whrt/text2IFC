"""Method-neutral local file tools and an explicitly offline command backend."""
from __future__ import annotations

from pathlib import Path

from .contracts import relative_path, safe_path
from .process_control import run_offline
from .budget import positive

# Identical protocol for A and C; no IFC methods, tutorials, or domain helpers.
TOOLS = [
    {'name': 'list_files', 'arguments': {'pattern': 'string (optional)'}},
    {'name': 'read_file', 'arguments': {'path': 'string', 'offset': 'integer (optional)', 'limit': 'integer (optional)'}},
    {'name': 'write_file', 'arguments': {'path': 'string', 'text': 'string'}},
    {'name': 'replace_text', 'arguments': {'path': 'string', 'old': 'string', 'new': 'string'}},
    {'name': 'execute', 'arguments': {'argv': 'array of strings', 'timeout_s': 'number (optional)'}},
    {'name': 'ask_user', 'arguments': {'question': 'string'}},
    {'name': 'submit', 'arguments': {'path': 'string'}},
]


class NeutralTools:
    def __init__(self, workspace: Path, *, tool_seconds: float):
        self.workspace = safe_path(workspace)
        self.tool_seconds = tool_seconds

    def path(self, value, *, write=False):
        relative = relative_path(value)
        path = safe_path(self.workspace / relative)
        if not path.is_relative_to(self.workspace):
            raise ValueError('PATH_OUTSIDE_WORKSPACE')
        if write and relative != 'model.ifc' and not relative.startswith(('work/', 'output/')):
            raise ValueError('PATH_NOT_WRITABLE')
        return path

    def list_files(self, pattern='**/*'):
        if '..' in pattern or ':' in pattern or pattern.startswith(('/', '\\')):
            raise ValueError('INVALID_PATTERN')
        files = [p.relative_to(self.workspace).as_posix() for p in self.workspace.glob(pattern) if safe_path(p).is_file()]
        return {'files': sorted(files)[:1000], 'truncated': len(files) > 1000}

    def read_file(self, path, offset=0, limit=65536):
        if type(offset) is not int or offset < 0 or type(limit) is not int or not 0 < limit <= 65536:
            raise ValueError('INVALID_READ_RANGE')
        with self.path(path).open(encoding='utf-8') as handle:
            # Offsets are Unicode characters, not bytes; preserve Chinese text.
            handle.read(offset)
            text = handle.read(limit + 1)
        return {'text': text[:limit], 'offset': offset, 'next_offset': offset + min(len(text), limit), 'truncated': len(text) > limit}

    def write_file(self, path, text):
        if not isinstance(text, str):
            raise ValueError('TEXT_REQUIRED')
        target = self.path(path, write=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        return {'path': path, 'characters': len(text)}

    def replace_text(self, path, old, new):
        target = self.path(path, write=True)
        text = target.read_text(encoding='utf-8')
        if not isinstance(old, str) or not old or text.count(old) != 1:
            raise ValueError('REPLACEMENT_MUST_MATCH_EXACTLY_ONCE')
        return self.write_file(path, text.replace(old, new, 1))

    def execute(self, argv, timeout_s=None):
        timeout = self.tool_seconds if timeout_s is None else timeout_s
        if not positive(timeout):
            raise ValueError('INVALID_TOOL_TIMEOUT')
        return run_offline(argv, self.workspace, min(timeout, self.tool_seconds))
