"""Automatic IFC2X3 -> bounded damaged IFC + public requests + self-check report."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / '.deps/python312')]

from scripts.ifc_repair.dataset_batch.pilot import main


if __name__ == '__main__':
    raise SystemExit(main())
