"""Extend frozen 1.1 matching/material/wall checks with complete filling geometry."""
import ifcopenshell

from . import precision_compare_v11 as previous
from .precision_compare_v10 import _summarize
from .filling_compare_v12 import compare_filling_geometry

VERSION='text2ifc/ifc2text-roundtrip-compare/1.2'


def compare_roundtrip(source_path,candidate_path,*,original_source_path=None):
    report=previous.compare_roundtrip(source_path,candidate_path,original_source_path=original_source_path)
    report['measurement_schema_version']=report['schema_version']
    report['schema_version']=VERSION
    if 'categories' not in report:
        return report
    source=ifcopenshell.open(str(source_path));candidate=ifcopenshell.open(str(candidate_path))
    for category,cls,prefix in [('doors','IfcDoor','D'),('windows','IfcWindow','N')]:
        # Observation 0.2 and its frozen 1.1 matcher enumerate each class by STEP
        # order. Resolve their existing labels; do not re-match by parts or shape.
        left={f'{prefix}{n:03d}':e for n,e in enumerate(sorted(source.by_type(cls),key=lambda e:e.id()),1)}
        right={f'{prefix}{n:03d}':e for n,e in enumerate(sorted(candidate.by_type(cls),key=lambda e:e.id()),1)}
        for row in report['categories'][category]['matched']:
            detail=compare_filling_geometry(left[row['source']],right[row['candidate']])
            row['filling_geometry']=detail
            if detail['unassessed']:
                report['unassessed'].append({'category':category,'source':row['source'],'candidate':row['candidate'],
                                            'fields':['complete_filling_body_geometry']})
            else:
                row['geometry_outside_tolerance']|=not detail['pass']
    file_status={k:report['status'].get(k) for k in ('files_readable','geometry_processable')}
    _summarize(report);report['status'].update(file_status)
    return report
