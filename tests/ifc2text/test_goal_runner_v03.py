"""Focused executable-entry tests, not a replacement for a genuine Provider run."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from text2ifc_compiler import compile_document

ROOT = Path(__file__).resolve().parents[2]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / 'ifc2text' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prepare_public_command_counts_all_described_classes(tmp_path, monkeypatch):
    document = json.loads((ROOT / 'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    source = tmp_path / 'source.ifc'
    assert compile_document(document, source).success
    before = source.read_bytes()
    output = tmp_path / 'prepared'
    monkeypatch.setattr(sys, 'argv', ['prepare_hierarchical.py', str(source), '--output-dir', str(output)])
    assert load_script('prepare_hierarchical').main() == 0
    manifest = json.loads((output / 'prepared.json').read_text(encoding='utf-8'))
    assert manifest['direct_ifc_counts']['slabs'] == 1
    assert manifest['direct_ifc_counts']['coverings'] == 1
    assert manifest['source_unchanged'] is True
    assert source.read_bytes() == before


def test_offline_guard_allows_stdlib_socketpair_but_blocks_client_connections():
    import socket
    import pytest
    guard = load_script('validate_goal').OfflineRecorder()
    with guard.network_guard():
        left, right = socket.socketpair()
        try:
            left.send(b'x')
            assert right.recv(1) == b'x'
        finally:
            left.close()
            right.close()
        assert guard.network_attempts == 0
        with socket.socket() as client:
            with pytest.raises(RuntimeError, match='NETWORK_FORBIDDEN'):
                client.connect(('127.0.0.1', 12345))
        assert guard.network_attempts == 1
