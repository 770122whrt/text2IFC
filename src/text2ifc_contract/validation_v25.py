"""BIM JSON 2.5 preserves 2.4 geometry and adds explicit non-layered material lists."""
from jsonschema import Draft202012Validator

from .schema import load_schema_v25
from .validation import _normalize_error, _sort_issues
from .validation_v2 import _semantic_issues
from .part_appearance import validate_part_appearance_document
from .basic_railing import validate_basic_railing


def validate_v25_document(document):
    structural = [i for e in Draft202012Validator(load_schema_v25()).iter_errors(document) for i in _normalize_error(e)]
    if structural:
        return _sort_issues(structural)
    issues = _semantic_issues(document, extended=True)
    paths = {f'/entities/{i}/attributes/Representation/kind' for i, e in enumerate(document['entities'])
             if e['attributes'].get('Representation', {}).get('kind') == 'basic_railing'}
    issues = [i for i in issues if not (i.code == 'UNSUPPORTED_GEOMETRY_KIND' and i.path in paths)]
    for index, record in enumerate(document['entities']):
        rep = record['attributes'].get('Representation', {})
        if rep.get('kind') == 'basic_railing':
            issues.extend(validate_basic_railing(rep, record['ifc_class'], f'/entities/{index}/attributes/Representation'))
    return _sort_issues([*issues, *validate_part_appearance_document(document)])
