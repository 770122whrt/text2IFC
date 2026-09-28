"""BIM JSON 2.6: additive parameterized door/window components."""
from jsonschema import Draft202012Validator

from .schema import load_schema_v26
from .validation import _normalize_error, _sort_issues
from .validation_v2 import _semantic_issues
from .part_appearance import validate_part_appearance_document
from .basic_railing import validate_basic_railing
from .component_geometry import validate_components


def validate_v26_document(document):
    structural = [i for e in Draft202012Validator(load_schema_v26()).iter_errors(document) for i in _normalize_error(e)]
    if structural:
        return _sort_issues(structural)
    issues = _semantic_issues(document, extended=True)
    paths = {f'/entities/{i}/attributes/Representation/kind' for i,e in enumerate(document['entities'])
             if e['attributes'].get('Representation',{}).get('kind') in {'component_geometry','basic_railing'}}
    issues = [i for i in issues if not (i.code == 'UNSUPPORTED_GEOMETRY_KIND' and i.path in paths)]
    for index, record in enumerate(document['entities']):
        rep = record['attributes'].get('Representation',{})
        validator = {'component_geometry':validate_components, 'basic_railing':validate_basic_railing}.get(rep.get('kind'))
        if validator:
            issues.extend(validator(rep,record['ifc_class'],f'/entities/{index}/attributes/Representation'))
    return _sort_issues([*issues, *validate_part_appearance_document(document)])
