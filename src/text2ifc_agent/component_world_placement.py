"""Check an explicitly requested world pose using public component geometry.

IfcOpenShell supplies local geometry; the shared placement contract composes the
candidate's complete parent chain. No source IFC or candidate geometry is used to
decide how large an orientation error is. Shape fidelity is a separate gate.
"""
import copy

import ifcopenshell.geom
import numpy as np

from text2ifc_contract.placement import world_transform_for


def component_world_placement_issues(candidate, element_id, expected_pose, representation):
    context = {'element_id': element_id,
               'path': f'/entities/{element_id}/attributes/ObjectPlacement',
               'target_entity_ids': [element_id], 'linear_tolerance_mm': 1.0}
    try:
        if expected_pose.get('relative_to') is not None:
            raise ValueError('Expected component placement must explicitly describe the world frame.')
        for key in ('origin', 'axis', 'ref_direction'):
            value = np.asarray(expected_pose[key], dtype=float)
            if value.shape != (3,) or not np.isfinite(value).all():
                raise ValueError('Expected component pose requires three finite coordinates per vector.')
        wanted = np.asarray(world_transform_for({'entities': [
            {'id': 'root', 'attributes': {}},
            {'id': 'wanted', 'attributes': {'ObjectPlacement': {**expected_pose, 'relative_to': 'root'}}},
        ]}, 'wanted'), dtype=float)
        actual = np.asarray(world_transform_for(candidate, element_id), dtype=float)
        for matrix in (wanted, actual):
            rotation = matrix[:3, :3]
            if (not np.isfinite(matrix).all() or not np.allclose(rotation.T@rotation, np.eye(3), atol=1e-9, rtol=0)
                    or not np.isclose(np.linalg.det(rotation), 1., atol=1e-9, rtol=0)):
                raise ValueError('Component placement is not a finite rigid frame.')
        from text2ifc_compiler.bootstrap import build_ifc_v2
        reference = build_ifc_v2({'schema_version': 'bim-json/2.6', 'entities': [
            {'id': 'project', 'ifc_class': 'IfcProject', 'attributes': {'Name': 'Public pose reference'}},
            {'id': 'product', 'ifc_class': 'IfcWindow',
             'attributes': {'Representation': copy.deepcopy(representation)}},
        ], 'relationships': []}).ifc_file
        settings = ifcopenshell.geom.settings()
        settings.set('mesher-linear-deflection', 0.0001)
        shape = ifcopenshell.geom.create_shape(settings, reference.by_type('IfcWindow')[0])
        points = np.asarray(shape.geometry.verts, dtype=float).reshape(-1, 3)*1000.
        if not len(points) or not np.isfinite(points).all():
            raise ValueError('Public component has no finite measured geometry.')
        expected_world = points@wanted[:3, :3].T+wanted[:3, 3]
        actual_world = points@actual[:3, :3].T+actual[:3, 3]
        error = float(np.linalg.norm(expected_world-actual_world, axis=1).max())
        if error > 1.0+1e-6:
            return [{**context, 'code': 'COMPONENT_WORLD_PLACEMENT_MISMATCH',
                     'message': 'Requested component world pose differs over the public component geometry.',
                     'sampled_placement_displacement_mm': error,
                     'expected_world_matrix': wanted.tolist(), 'actual_world_matrix': actual.tolist()}]
    except (AttributeError, KeyError, TypeError, ValueError, RuntimeError, IndexError) as error:
        return [{**context, 'code': 'COMPONENT_WORLD_PLACEMENT_UNASSESSED', 'message': str(error)}]
    return []
