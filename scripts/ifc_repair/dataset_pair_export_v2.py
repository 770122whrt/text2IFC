"""Export authoring profile 1.3 as an explicitly bound public profile 1.4.

The frozen 1.0 exporter still owns every sealed/native/EXPRESS/prompt/wall/mesh
authoring gate. This version adds the public axis glossary to requests and binds
the original bytes, decoded source body, transform program/prefix and final
bytes separately. IFC bytes and the six CSV columns retain their old contract.
"""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
from pathlib import Path
import shutil

from scripts.ifc_repair import dataset_pair_export as authoring
from scripts.ifc_repair import dataset_request_v4 as profile
from scripts.ifc_repair.dataset_batch.validation import sha256
from scripts.ifc_repair.repair_comparison.batch_cases import load_pair_candidates

SCHEMA = 'text2ifc/dataset-pair-export/1.1'
FIELDS = authoring.FIELDS
PROFILE_MODULE = Path(profile.__file__).resolve()


def text_sha256(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def transform_program_bindings():
    return {str(path): sha256(path) for path in (Path(__file__).resolve(), PROFILE_MODULE)}


def _transform():
    return {'authoring_request_profile': profile.SOURCE_PROFILE, 'request_profile': profile.PROFILE,
            'prefix_sha256': text_sha256(profile.PREFIX), 'program_sha256': transform_program_bindings(),
            'source_decoding': 'UTF-8-sig from bytes; body line endings retained',
            'output_encoding': 'UTF-8 without BOM',
            'scope': 'Fixed public coordinate/axis glossary prefix only; no object-specific private facts.'}


def _program_bindings(bindings):
    for path, digest in transform_program_bindings().items():
        authoring._bind(Path(path), bindings, digest)
    authoring._bind(Path(authoring.__file__).resolve(), bindings)


def _recheck(bindings):
    for value, expected in bindings.items():
        path = authoring._pair_safe_path(Path(value))
        authoring._require(path.is_file() and sha256(path) == authoring._digest(expected),
                           'EXPORT_SOURCE_BINDING_CHANGED:' + value)


def _render(request):
    original = request.read_bytes().decode('utf-8-sig')
    upgraded = profile.upgrade_request(original)
    authoring._require(profile.validate_request(upgraded, original) is True, 'REQUEST_TRANSFORM_INVALID')
    return upgraded.encode('utf-8'), text_sha256(original)


def check_pair_export_v2(public_root, evaluation_root):
    """Recheck full authoring gates and exact 1.4 prefix/source-body/final bytes."""
    source, public, evaluation = authoring._roots(public_root, evaluation_root)
    receipt = authoring._read(evaluation / 'export.json')
    authoring._require(not (evaluation / 'export-failed.json').exists(), 'FAILED_EXPORT_RECEIPT_PRESENT')
    authoring._require(receipt.get('schema_version') == SCHEMA and receipt.get('status') == 'complete'
        and receipt.get('source_root') == str(source) and receipt.get('public_root') == str(public)
        and receipt.get('evaluation_root') == str(evaluation)
        and receipt.get('authoring_request_profile') == profile.SOURCE_PROFILE
        and receipt.get('request_profile') == profile.PROFILE and receipt.get('transform') == _transform(),
        'EXPORT_RECEIPT_OR_TRANSFORM_BINDING_FAILED')
    provenance = receipt.get('pair_provenance')
    authoring._require(isinstance(provenance, list) and bool(provenance), 'EXPORT_PROVENANCE_INVALID')
    prepared, bindings = authoring._prepare(source, provenance, receipt.get('source_models'))
    _program_bindings(bindings)
    authoring._require(receipt.get('bound_hashes') == bindings, 'EXPORT_SOURCE_BINDING_SET_CHANGED')
    _recheck(bindings)
    candidates = load_pair_candidates(public)
    with authoring._file(public, 'inputs.csv').open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        authoring._require(tuple(reader.fieldnames or ()) == FIELDS, 'EXPORT_CSV_COLUMNS_CHANGED')
        rows = list(reader)
    allowed = {'inputs.csv', *[row[key] for row in rows for key in ('ifc_path', 'request_path')]}
    hashes = receipt.get('public_file_sha256')
    authoring._require(isinstance(hashes, dict) and authoring._public_files(public) == set(hashes) == allowed
        and len(allowed) == 2 * len(candidates) + 1 and len(provenance) == len(rows) == len(prepared)
        == receipt.get('pairs'), 'EXPORT_FILE_SET_OR_PAIR_COUNT_CHANGED')
    for relative, digest in hashes.items():
        authoring._require(sha256(authoring._file(public, relative)) == authoring._digest(digest),
                           'EXPORT_INPUT_BINDING_CHANGED:' + relative)
    for (pair, row, model, original), saved, public_row in zip(prepared, provenance, rows, strict=True):
        expected_row = {key: str(value) for key, value in row.items()}
        authoring._require(saved.get('public_row') == public_row == expected_row, 'EXPORT_MAPPING_CHANGED')
        rendered, body_hash = _render(original)
        request_path = authoring._file(public, row['request_path'])
        actual_bytes = request_path.read_bytes()
        final_hash = sha256(request_path)
        authoring._require(actual_bytes == rendered
            and profile.validate_request(actual_bytes.decode('utf-8'), original.read_bytes().decode('utf-8-sig')) is True,
            'REQUEST_TRANSFORM_BODY_CHANGED')
        authoring._require(saved.get('authoring_request_sha256') == pair['request_sha256']
            and saved.get('source_body_sha256') == body_hash
            and saved.get('public_request_sha256') == final_hash == hashes[row['request_path']]
            and hashes[row['ifc_path']] == pair['model_sha256'] == sha256(model),
            'REQUEST_TRANSFORM_HASH_BINDING_CHANGED')
    damages = {pair['damage_id'] for pair in provenance}
    sources = {pair['source_id'] for pair in provenance}
    authoring._require(len(damages) == receipt.get('distinct_damages')
        and len(sources) == receipt.get('source_models'), 'EXPORT_PROVENANCE_COUNT_CHANGED')
    _recheck(bindings)  # Keep the original exporter's final all-source check.
    return {'status': 'complete', 'pairs': len(candidates), 'distinct_damages': len(damages),
        'source_models': len(sources), 'public_root': str(public), 'evaluation_root': str(evaluation),
        'public_files': len(allowed), 'budget_levels': dict(Counter(c['level'] for c in candidates)),
        'task_kinds': dict(Counter(c['category'] for c in candidates)), 'provider_calls': 0,
        'live_stage_admission': False, 'authoring_request_profile': profile.SOURCE_PROFILE,
        'request_profile': profile.PROFILE, 'request_transforms_checked': len(candidates),
        'validation_scope': 'Full sealed authoring/export gates and saved native/EXPRESS evidence reused; '
            'fresh exact public request transform/body/prefix/hash, CSV and whitelist checks; no native rerun.'}


check_pair_export = check_pair_export_v2


def export_pairs(source_root, public_root, evaluation_root, pairs, *, source_models):
    """Create a new handoff; retain every partial output/error without retrying."""
    source, public, evaluation = authoring._roots(public_root, evaluation_root, source_root)
    for path in (public, evaluation):
        if path.exists():
            raise FileExistsError('NEW_OUTPUT_REQUIRED:' + str(path))
    prepared, bindings = authoring._prepare(source, pairs, source_models)
    _program_bindings(bindings)
    rendered = [_render(request) for _, _, _, request in prepared]
    transform = _transform()
    evaluation.mkdir(parents=True)
    public.mkdir(parents=True)
    try:
        hashes, provenance = {}, []
        for (pair, row, model, original), (request_bytes, body_hash) in zip(prepared, rendered, strict=True):
            model_copy = public / row['ifc_path']
            model_copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(authoring._pair_safe_path(model), model_copy)
            authoring._require(sha256(model_copy) == sha256(model) == pair['model_sha256'],
                               'SOURCE_OR_COPY_CHANGED_DURING_EXPORT')
            request_copy = public / row['request_path']
            request_copy.write_bytes(request_bytes)
            final_hash = sha256(request_copy)
            authoring._require(request_copy.read_bytes() == request_bytes
                and sha256(original) == pair['request_sha256'], 'SOURCE_OR_TRANSFORM_CHANGED_DURING_EXPORT')
            hashes[row['ifc_path']] = pair['model_sha256']
            hashes[row['request_path']] = final_hash
            provenance.append({**pair, 'authoring_request_sha256': pair['request_sha256'],
                'source_body_sha256': body_hash, 'public_request_sha256': final_hash,
                'public_row': {key: str(value) for key, value in row.items()}})
        with (public / 'inputs.csv').open('x', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(row for _, row, _, _ in prepared)
        hashes['inputs.csv'] = sha256(public / 'inputs.csv')
        authoring._require(len(load_pair_candidates(public)) == len(prepared), 'EXPORT_PAIR_ADAPTER_MISMATCH')
        _recheck(bindings)
        authoring._require(transform == _transform(), 'TRANSFORM_PROGRAM_CHANGED_DURING_EXPORT')
        authoring._write(evaluation / 'export.json', {'schema_version': SCHEMA, 'status': 'complete',
            'source_root': str(source), 'public_root': str(public), 'evaluation_root': str(evaluation),
            'source_models': source_models, 'pairs': len(prepared),
            'distinct_damages': len({p['damage_id'] for p, _, _, _ in prepared}), 'provider_calls': 0,
            'live_stage_admission': False, 'authoring_request_profile': profile.SOURCE_PROFILE,
            'request_profile': profile.PROFILE, 'transform': transform, 'pair_provenance': provenance,
            'bound_hashes': bindings, 'public_file_sha256': hashes, 'exporter_sha256': sha256(Path(__file__)),
            'scope': 'Exact IFC copies; public 1.3 text bodies prefixed with fixed 1.4 axis conventions. '
                'Original sealed native/prompt/wall/mesh evidence reused; final transformed text checked. '
                'No native rerun, system repair or human acceptance.'})
        return check_pair_export_v2(public, evaluation)
    except Exception as exc:
        authoring._write(evaluation / 'export-failed.json', {'schema_version': SCHEMA, 'status': 'failed',
            'error': f'{type(exc).__name__}: {exc}', 'provider_calls': 0, 'live_stage_admission': False,
            'scope': 'Partial outputs/receipts retained; no automatic deletion, overwrite or retry.'})
        raise
