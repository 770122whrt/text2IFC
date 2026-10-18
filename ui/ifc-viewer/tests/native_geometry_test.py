"""Focused geometry export contracts, not repair acceptance tests."""
import importlib.util
import unittest
from pathlib import Path
import numpy as np
SPEC=importlib.util.spec_from_file_location('native_geometry',Path(__file__).parents[1]/'native_geometry.py')
module=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

class NativeGeometryTests(unittest.TestCase):
    def test_triangle(self):
        self.assertTrue(module.mesh_is_valid(np.array([[0,0,0],[1,0,0],[0,1,0]]),np.array([[0,1,2]])))
    def test_empty(self):
        self.assertFalse(module.mesh_is_valid(np.empty((0,3)),np.empty((0,3),dtype=int)))
    def test_nonfinite(self):
        self.assertFalse(module.mesh_is_valid(np.array([[0,0,0],[1,0,0],[0,float('nan'),0]]),np.array([[0,1,2]])))
    def test_outside_vertex(self):
        self.assertFalse(module.mesh_is_valid(np.zeros((3,3)),np.array([[0,1,4]])))

if __name__=='__main__':unittest.main()
