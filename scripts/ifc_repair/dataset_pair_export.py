"""Export sealed dataset-authoring cases as public IFC/request pairs.

The authoring side may inspect private receipts and reference hashes. Exported
inputs contain only exact copies of each pair's two public files and inputs.csv.
Checks here reuse saved receipts; they never open IFC or rerun native/mesh work.
"""
from __future__ import annotations

from collections import Counter
import csv
import json
from pathlib import Path
import re
import shutil

import ifcopenshell

from scripts.ifc_repair.dataset_batch.engine import verify_seal
from scripts.ifc_repair.dataset_batch.validation import sha256
from scripts.ifc_repair.repair_comparison.batch_cases import (
    _identifier, _pair_safe_path, load_pair_candidates,
)
from scripts.ifc_repair.repair_comparison.budget import budget_level_for_primary_targets
from scripts.ifc_repair.repair_comparison.contracts import relative_path


SCHEMA = 'text2ifc/dataset-pair-export/1.0'
FIELDS = ('case_id', 'ifc_path', 'request_path', 'level', 'primary_target_count', 'task_kind')
PAIR_FIELDS = ('case_id', 'source_id', 'damage_id', 'locator_mode', 'case_path',
               'request_relative_path', 'model_sha256', 'request_sha256',
               'primary_target_count', 'task_kind')
PRIVATE_WORDS = re.compile(r'original|gold|reference|mutation|private|pristine|ground[_-]?truth', re.I)
CLASSES = {'door': 'IfcDoor', 'window': 'IfcWindow', 'beam': 'IfcBeam', 'column': 'IfcColumn'}
CHECKS = {'private/prompt-check.json', 'private/wall-check.json', 'private/mesh-check.json'}
MAX_IFC_BYTES = 20_000_000


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _digest(value):
    _require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value), 'INVALID_INPUT_DIGEST')
    return value


def _read(path):
    path = _pair_safe_path(Path(path))
    _require(path.is_file(), 'METADATA_MISSING:' + str(path))
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    _require(isinstance(value, dict), 'METADATA_OBJECT_REQUIRED:' + str(path))
    return value


def _relative(value):
    result = relative_path(value)
    _require(result == value and all(part and part == part.strip()
             and not part.endswith(('.', ' ')) for part in value.split('/')), 'INVALID_RELATIVE_PATH')
    return result


def _file(root, relative):
    path = _pair_safe_path(root / _relative(relative))
    _require(path.is_relative_to(root) and path.is_file(), 'BOUND_FILE_MISSING:' + relative)
    return path


def _disjoint(*roots):
    for index, first in enumerate(roots):
        for second in roots[index + 1:]:
            _require(not first.is_relative_to(second) and not second.is_relative_to(first),
                     'ROOTS_MUST_NOT_CONTAIN_EACH_OTHER')


def _roots(public_root, evaluation_root, source_root=None):
    public, evaluation = (_pair_safe_path(Path(path)) for path in (public_root, evaluation_root))
    batch = public.parent
    _require(public == batch / 'public' and evaluation == batch / 'private/evaluation',
             'BATCH_ROOT_LAYOUT_REQUIRED')
    source = _pair_safe_path(Path(source_root)) if source_root is not None else batch / 'private/production'
    _require(source == batch / 'private/production', 'BATCH_ROOT_LAYOUT_REQUIRED')
    _disjoint(source, public, evaluation)
    return source, public, evaluation


def _bind(path, bindings, expected=None):
    path = _pair_safe_path(path)
    _require(path.is_file(), 'BOUND_FILE_MISSING:' + str(path))
    actual = sha256(path)
    if expected is not None:
        _require(actual == _digest(expected), 'SOURCE_HASH_BINDING_FAILED:' + str(path))
    key = str(path)
    _require(key not in bindings or bindings[key] == actual, 'SOURCE_CHANGED_DURING_ADMISSION:' + key)
    bindings[key] = actual
    return actual


def _native(receipt):
    _require(receipt.get('passed') is True and type(receipt.get('finding_count')) is int
             and receipt['finding_count'] == 0 and receipt.get('express_rules') is True
             and receipt.get('schema') == 'IFC2X3'
             and receipt.get('ifcopenshell_version') == ifcopenshell.version, 'NATIVE_RECEIPT_INVALID')


def _targets(meta, mutation):
    deletions, changes = mutation.get('deletions'), mutation.get('property_changes')
    _require(isinstance(deletions, list) and isinstance(changes, list), 'MUTATION_TARGETS_INVALID')
    deleted, properties = set(), set()
    counts = Counter()
    for row in deletions:
        _require(isinstance(row, dict) and isinstance(row.get('guid'), str) and row['guid']
                 and row.get('ifc_class') in CLASSES.values(), 'MUTATION_TARGETS_INVALID')
        _require(row['guid'] not in deleted, 'DUPLICATE_DELETED_TARGET')
        deleted.add(row['guid'])
        counts[next(key for key, cls in CLASSES.items() if cls == row['ifc_class'])] += 1
    for row in changes:
        _require(isinstance(row, dict) and isinstance(row.get('guid'), str) and row['guid']
                 and row.get('ifc_class') in CLASSES.values(),
                 'MUTATION_TARGETS_INVALID')
        _require(row['guid'] not in deleted, 'PROPERTY_TARGET_WAS_DELETED')
        properties.add(row['guid'])
    declared = meta.get('deleted_counts')
    _require(isinstance(declared, dict) and set(declared) <= set(CLASSES)
             and all(type(n) is int and n >= 0 for n in declared.values())
             and all(declared.get(key, 0) == counts[key] for key in CLASSES), 'DELETED_COUNTS_MISMATCH')
    _require(type(meta.get('property_changes')) is int and meta['property_changes'] == len(changes),
             'PROPERTY_CHANGE_COUNT_MISMATCH')
    count = len(deleted | properties)
    _require(count > 0, 'NO_PRIMARY_TARGETS')
    for field, expected in (('primary_target_count', count), ('property_target_count', len(properties))):
        _require(field not in meta or type(meta[field]) is int and meta[field] == expected,
                 'DECLARED_TARGET_COUNT_MISMATCH')
    kind = 'mixed' if deletions and changes else 'geometry' if deletions else 'property'
    level = budget_level_for_primary_targets(count)
    _require('level' not in meta or meta['level'] == level, 'REVIEWED_LEVEL_MISMATCH')
    return count, kind, level


def _case(source_root, pair, bindings):
    """Check every applicable request and the sealed authoring receipts once."""
    folder = _pair_safe_path(source_root / pair['case_path'])
    model = _file(folder, 'public/model.ifc')
    _require(0 < model.stat().st_size < MAX_IFC_BYTES, 'PUBLIC_MODEL_SIZE_LIMIT')
    seal_path = _file(folder, 'private/seal.json')
    seal = _read(seal_path)
    _require(seal.get('schema_version') == 'text2ifc/ifc-repair-dataset-seal/1.0'
             and isinstance(seal.get('sha256'), dict) and bool(seal['sha256']), 'CASE_SEAL_INVALID')
    # Validate paths before verify_seal reads them, including all private evidence.
    for relative, expected in seal['sha256'].items():
        _file(folder, relative)
        _digest(expected)
    _require(verify_seal(folder), 'CASE_SEAL_INVALID:' + pair['case_path'])
    _bind(seal_path, bindings)
    for relative, expected in seal['sha256'].items():
        _bind(_file(folder, relative), bindings, expected)
    meta = _read(_file(folder, 'case.json'))
    _require(meta.get('schema_version') == 'text2ifc/ifc-repair-dataset-case/1.1'
             and meta.get('status') == 'passed' and meta.get('machine_validated') is True
             and meta.get('source_unchanged') is True and meta.get('private_identity_leakage') is False,
             'CASE_STATE_INVALID')
    _require(all(meta.get(flag) is True for flag in ('information_sufficient', 'wall_check_passed',
                 'independent_mesh_check_passed')), 'CASE_CHECK_STATE_INVALID')
    evidence = meta.get('additional_evidence')
    _require(isinstance(evidence, list) and CHECKS <= set(evidence), 'CHECKS_NOT_SEALED')
    model_hash = _bind(model, bindings, _digest(meta.get('damaged_sha256')))
    source_folder = source_root / 'sources' / pair['source_id']
    reference = _file(source_folder, 'private/reference.ifc')
    _require(0 < reference.stat().st_size < MAX_IFC_BYTES, 'REFERENCE_SIZE_LIMIT')
    reference_hash = _bind(reference, bindings, _digest(meta.get('source_sha256')))
    source_json = _file(source_folder, 'private/source.json')
    _bind(source_json, bindings)
    source = _read(source_json)
    _require(source.get('source_id') == pair['source_id']
             and source.get('source_sha256') == reference_hash,
             'SOURCE_METADATA_BINDING_FAILED')
    source_validation = _file(source_folder, 'private/source-validation.json')
    _bind(source_validation, bindings)
    source_native = _read(source_validation)
    _native(source_native)
    _require(source_native.get('input_sha256') == reference_hash, 'SOURCE_NATIVE_HASH_MISMATCH')
    mutation = _read(_file(folder, 'private/mutation.json'))
    _require(mutation.get('schema_version') == 'text2ifc/ifc-repair-dataset-mutation/1.3'
             and mutation.get('prompt_profile') == 'text2ifc/dataset-request/1.3'
             and mutation.get('source_sha256') == reference_hash
             and mutation.get('damaged_sha256') == model_hash, 'MUTATION_BINDING_FAILED')
    _native(_read(_file(folder, 'private/validation.json')))
    _require(_read(_file(folder, 'private/preservation.json')).get('passed') is True,
             'PRESERVATION_RECEIPT_INVALID')
    count, kind, level = _targets(meta, mutation)
    templates, prompts = meta.get('prompt_templates'), _read(_file(folder, 'private/prompt-check.json'))
    _require(isinstance(templates, dict) and all(isinstance(value, dict)
             and type(value.get('applicable')) is bool for value in templates.values()), 'PROMPT_TEMPLATES_INVALID')
    active = {name for name, value in templates.items() if value['applicable']}
    _require('world' in active and active <= {'world', 'host_wall'} and active == set(prompts)
             and all(isinstance(value, dict) and value.get('passed') is True
                     and value.get('errors') == [] for value in prompts.values()), 'PROMPT_RECEIPT_INVALID')
    private_ids = {identity for row in mutation['deletions'] for identity in (row['guid'], row.get('opening_guid')) if identity}
    requests = {}
    for mode in active:
        path = _file(folder, f'public/request-{mode}.txt')
        request_hash = _bind(path, bindings, _digest(templates[mode].get('sha256')))
        text = path.read_text(encoding='utf-8-sig')
        _require(bool(text.strip()), 'EMPTY_PUBLIC_REQUEST')
        _require(not any(identity in text for identity in private_ids), 'DELETED_ID_IN_PUBLIC_REQUEST')
        requests[mode] = (path, request_hash)
    if 'primary_prompt' in meta:
        primary = meta['primary_prompt']
        _require(primary in active and 'public/request.txt' in seal['sha256'], 'PRIMARY_PROMPT_INVALID')
        _require(_bind(_file(folder, 'public/request.txt'), bindings) == requests[primary][1],
                 'PRIMARY_PROMPT_BINDING_FAILED')
    wall = _read(_file(folder, 'private/wall-check.json'))
    _require(wall.get('passed') is True and type(wall.get('applicable')) is bool
             and wall['applicable'] == meta.get('wall_check_applicable') and wall.get('errors') == [],
             'WALL_RECEIPT_INVALID')
    mesh = _read(_file(folder, 'private/mesh-check.json'))
    _require(mesh.get('passed') is True and mesh.get('errors') == [], 'MESH_RECEIPT_INVALID')
    # Where a wall receipt records its own inputs, bind those to the same bytes.
    if 'input_sha256' in wall:
        _require(wall['input_sha256'] == {'reference': reference_hash, 'damaged': model_hash},
                 'WALL_INPUT_BINDING_FAILED')
    return {'model': model, 'model_sha256': model_hash, 'requests': requests,
            'primary_target_count': count, 'task_kind': kind, 'level': level}


def _prepare(source_root, pairs, source_models):
    _require(type(source_models) is int and source_models > 0, 'SOURCE_MODELS_MUST_BE_POSITIVE')
    pairs = list(pairs)
    _require(bool(pairs), 'NO_PUBLIC_PAIRS')
    identifiers, modes, damage_bindings, case_damage = set(), set(), {}, {}
    normalized = []
    for value in pairs:
        _require(isinstance(value, dict) and set(PAIR_FIELDS) <= set(value), 'PAIR_FIELDS_MISSING')
        pair = {key: value[key] for key in PAIR_FIELDS}
        key = _identifier(pair['case_id'])
        _require(len(key) <= 101 and not PRIVATE_WORDS.search(key), 'PUBLIC_CASE_ID_INVALID')
        _identifier(pair['source_id'], 'INVALID_SOURCE_ID')
        _identifier(pair['damage_id'], 'INVALID_DAMAGE_ID')
        _require(key.casefold() not in identifiers, 'DUPLICATE_CASE_ID')
        identifiers.add(key.casefold())
        mode = pair['locator_mode']
        _require(mode in {'world', 'host_wall'}, 'INVALID_LOCATOR_MODE')
        mode_key = (pair['damage_id'].casefold(), mode)
        _require(mode_key not in modes, 'DUPLICATE_DAMAGE_LOCATOR_MODE')
        modes.add(mode_key)
        relative = _relative(pair['case_path'])
        parts = relative.split('/')
        _require(len(parts) == 4 and parts[:3] == ['sources', pair['source_id'], 'cases'], 'CASE_PATH_INVALID')
        _identifier(parts[3], 'INVALID_DAMAGE_FOLDER')
        _require(pair['request_relative_path'] == f'public/request-{mode}.txt', 'REQUEST_PATH_INVALID')
        _digest(pair['model_sha256'])
        _digest(pair['request_sha256'])
        _require(type(pair['primary_target_count']) is int and pair['primary_target_count'] > 0,
                 'INVALID_PRIMARY_TARGET_COUNT')
        _require(pair['task_kind'] in {'geometry', 'property', 'mixed'}, 'INVALID_TASK_KIND')
        binding = (relative.casefold(), pair['source_id'].casefold(), pair['model_sha256'])
        damage = pair['damage_id'].casefold()
        _require(damage not in damage_bindings or damage_bindings[damage] == binding, 'DAMAGE_ID_BINDING_MISMATCH')
        damage_bindings[damage] = binding
        _require(relative.casefold() not in case_damage or case_damage[relative.casefold()] == damage,
                 'CASE_DAMAGE_ID_BINDING_MISMATCH')
        case_damage[relative.casefold()] = damage
        normalized.append(pair)
    _require(len({pair['source_id'].casefold() for pair in normalized}) == source_models,
             'SOURCE_MODEL_COUNT_MISMATCH')
    bindings, cases, output = {}, {}, []
    for pair in normalized:
        relative = pair['case_path']
        if relative not in cases:
            cases[relative] = _case(source_root, pair, bindings)
        case = cases[relative]
        _require(pair['model_sha256'] == case['model_sha256'], 'PAIR_MODEL_BINDING_FAILED')
        _require(pair['locator_mode'] in case['requests'], 'REQUEST_MODE_NOT_APPLICABLE')
        request, request_hash = case['requests'][pair['locator_mode']]
        _require(pair['request_sha256'] == request_hash, 'PAIR_REQUEST_BINDING_FAILED')
        _require(pair['primary_target_count'] == case['primary_target_count']
                 and pair['task_kind'] == case['task_kind'], 'PAIR_TARGET_METADATA_MISMATCH')
        row = {'case_id': pair['case_id'], 'ifc_path': f"cases/{pair['case_id']}/model.ifc",
               'request_path': f"cases/{pair['case_id']}/request.txt", 'level': case['level'],
               'primary_target_count': pair['primary_target_count'], 'task_kind': pair['task_kind']}
        output.append((pair, row, case['model'], request))
    return output, bindings


def _public_files(public):
    files = set()
    for entry in public.rglob('*'):
        path = _pair_safe_path(entry)
        if path.is_file():
            files.add(path.relative_to(public).as_posix())
        else:
            _require(path.is_dir(), 'UNSUPPORTED_PUBLIC_ENTRY')
    return files


def _write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def check_pair_export(public_root, evaluation_root):
    """Check saved mapping, exact CSV file whitelist and public byte hashes.

    This public handoff check does not revalidate upstream cases or native IFC.
    """
    source, public, evaluation = _roots(public_root, evaluation_root)
    receipt = _read(evaluation / 'export.json')
    _require(receipt.get('schema_version') == SCHEMA and receipt.get('status') == 'complete'
             and receipt.get('source_root') == str(source) and receipt.get('public_root') == str(public)
             and receipt.get('evaluation_root') == str(evaluation), 'EXPORT_RECEIPT_BINDING_FAILED')
    candidates = load_pair_candidates(public)
    with _file(public, 'inputs.csv').open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        _require(tuple(reader.fieldnames or ()) == FIELDS, 'EXPORT_CSV_COLUMNS_CHANGED')
        rows = list(reader)
    allowed = {'inputs.csv', *[Path(case[field]).relative_to(public).as_posix()
                              for case in candidates for field in ('model_path', 'request_path')]}
    hashes = receipt.get('public_file_sha256')
    _require(isinstance(hashes, dict) and _public_files(public) == set(hashes) == allowed
             and len(allowed) == 2 * len(candidates) + 1, 'EXPORT_FILE_SET_CHANGED')
    for relative, expected in hashes.items():
        _require(sha256(_file(public, relative)) == _digest(expected), 'EXPORT_INPUT_BINDING_CHANGED:' + relative)
    provenance = receipt.get('pair_provenance')
    _require(isinstance(provenance, list) and len(provenance) == len(rows) == receipt.get('pairs'),
             'EXPORT_PAIR_COUNT_CHANGED')
    _require(all(isinstance(pair, dict) and pair.get('public_row') == row
                 for pair, row in zip(provenance, rows, strict=True)), 'EXPORT_MAPPING_CHANGED')
    damages = {pair.get('damage_id') for pair in provenance}
    sources = {pair.get('source_id') for pair in provenance}
    _require(None not in damages and None not in sources and len(damages) == receipt.get('distinct_damages')
             and len(sources) == receipt.get('source_models'), 'EXPORT_PROVENANCE_COUNT_CHANGED')
    return {'status': 'complete', 'pairs': len(candidates), 'distinct_damages': len(damages),
            'source_models': len(sources), 'public_root': str(public), 'evaluation_root': str(evaluation),
            'public_files': len(allowed), 'budget_levels': dict(Counter(c['level'] for c in candidates)),
            'task_kinds': dict(Counter(c['category'] for c in candidates)), 'provider_calls': 0,
            'live_stage_admission': False,
            'validation_scope': 'saved export mapping, public whitelist/hash and CSV checks; no upstream/native/mesh revalidation'}


def export_pairs(source_root, public_root, evaluation_root, pairs, *, source_models):
    """Copy authored pairs from sealed cases; every output directory must be new.

    Roots are batch/private/production, batch/public and batch/private/evaluation.
    source_models counts represented mothers; the caller owns its per-mother quota.
    Failed partial outputs remain available with a private failure receipt.
    """
    source, public, evaluation = _roots(public_root, evaluation_root, source_root)
    _require(source.is_dir(), 'SOURCE_ROOT_MISSING')
    for path in (public, evaluation):
        if path.exists():
            raise FileExistsError('NEW_OUTPUT_REQUIRED:' + str(path))
    prepared, bindings = _prepare(source, pairs, source_models)
    evaluation.mkdir(parents=True)
    public.mkdir(parents=True)
    try:
        hashes, provenance = {}, []
        for pair, row, model, request in prepared:
            for original, field, expected in ((model, 'ifc_path', pair['model_sha256']),
                                               (request, 'request_path', pair['request_sha256'])):
                target = public / row[field]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(_pair_safe_path(original), target)
                _require(sha256(_pair_safe_path(target)) == sha256(_pair_safe_path(original)) == expected,
                         'SOURCE_OR_COPY_CHANGED_DURING_EXPORT')
                hashes[row[field]] = expected
            provenance.append({**pair, 'public_row': {key: str(value) for key, value in row.items()}})
        with (public / 'inputs.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(row for _, row, _, _ in prepared)
        hashes['inputs.csv'] = sha256(public / 'inputs.csv')
        _require(len(load_pair_candidates(public)) == len(prepared), 'EXPORT_PAIR_ADAPTER_MISMATCH')
        # Recheck every public source and all bound sealed/private metadata after
        # the final copy, so an earlier pair cannot drift while later ones copy.
        for path, expected in bindings.items():
            _require(sha256(_pair_safe_path(Path(path))) == expected, 'SOURCE_CHANGED_DURING_EXPORT:' + path)
        receipt = {'schema_version': SCHEMA, 'status': 'complete', 'source_root': str(source),
                   'public_root': str(public), 'evaluation_root': str(evaluation), 'source_models': source_models,
                   'pairs': len(prepared), 'distinct_damages': len({p['damage_id'] for p, _, _, _ in prepared}),
                   'provider_calls': 0, 'live_stage_admission': False, 'pair_provenance': provenance,
                   'bound_hashes': bindings, 'public_file_sha256': hashes, 'exporter_sha256': sha256(Path(__file__)),
                   'scope': 'Exact public byte copies; prior sealed native/prompt/wall/mesh receipts reused; no native rerun, system repair or human acceptance.'}
        _write(evaluation / 'export.json', receipt)
        return check_pair_export(public, evaluation)
    except Exception as exc:
        _write(evaluation / 'export-failed.json', {'schema_version': SCHEMA, 'status': 'failed',
               'error': f'{type(exc).__name__}: {exc}', 'provider_calls': 0, 'live_stage_admission': False,
               'scope': 'Partial outputs retained; use new destinations for a retry.'})
        raise
