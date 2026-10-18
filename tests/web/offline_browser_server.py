"""Explicit offline-only browser UAT service. Not imported by product launchers."""
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT))
from tests.web.test_native_chain import NativeFactory
from text2ifc_web.app import create_app
import uvicorn

if __name__=='__main__':
    root=Path(sys.argv[1]).resolve()
    if not root.is_relative_to(ROOT/'.tmp'):
        raise ValueError('Offline UAT storage must be inside this workspace .tmp')
    factory=NativeFactory('window',clarify=True)
    factory.evidence_class='offline_fixture'
    with ThreadPoolExecutor(max_workers=1) as executor:
        app=create_app(root,api_factory=factory,executor=executor,allowed_origins=('http://127.0.0.1:4191',))
        uvicorn.run(app,host='127.0.0.1',port=4190,log_level='warning')
