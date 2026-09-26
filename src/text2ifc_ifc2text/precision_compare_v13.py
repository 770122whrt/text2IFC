"""Use complete world opening solids instead of frame-dependent profile sizes."""
import ifcopenshell
from .precision_compare_v12 import compare_roundtrip as previous
from .precision_compare_v10 import _summarize
from .opening_compare_v13 import compare_opening_geometry


def compare_roundtrip(source_path,candidate_path,*,original_source_path=None):
    report=previous(source_path,candidate_path,original_source_path=original_source_path)
    report['schema_version']='text2ifc/ifc2text-roundtrip-compare/1.3'
    if 'categories' not in report:
        return report
    source=ifcopenshell.open(str(source_path));candidate=ifcopenshell.open(str(candidate_path))
    left={f'O{n:03d}':e for n,e in enumerate(sorted(source.by_type('IfcOpeningElement'),key=lambda e:e.id()),1)}
    right={f'O{n:03d}':e for n,e in enumerate(sorted(candidate.by_type('IfcOpeningElement'),key=lambda e:e.id()),1)}
    for row in report['categories']['openings']['matched']:
        detail=compare_opening_geometry(left[row['source']],right[row['candidate']])
        row['opening_geometry']=detail
        # Preserve the old numeric result for diagnosis. An opening has no
        # OverallWidth/Height semantic requirement; these were profile-axis sizes.
        row['profile_dimension_deltas_mm']=dict(row['nominal_dimension_deltas_mm'])
        row['profile_dimensions_used_for_geometry_verdict']=False
        row['geometry_outside_tolerance']=not detail['pass']
        if detail['unassessed']:
            report['unassessed'].append({'category':'openings','source':row['source'],'candidate':row['candidate'],
                                        'fields':['complete_opening_body_geometry']})
    file_status={k:report['status'].get(k) for k in ('files_readable','geometry_processable')}
    _summarize(report);report['status'].update(file_status)
    return report
