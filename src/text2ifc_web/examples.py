"""Read-only, exact-file catalog for local demonstrations. Never starts a Repair run."""
from pathlib import Path
import json
from .contracts import WebError

class Examples:
    def __init__(self,root=None):self.root=Path(root).resolve() if root else None
    def all(self):
        path=self.root/'catalog.json' if self.root else None
        if path is None or not path.is_file():return []
        data=json.loads(path.read_text(encoding='utf-8'))
        return [self._public(e) for e in data.get('examples',[]) if e.get('evidence_class')=='archived_live' and e.get('archived_success') is True]
    def _public(self,entry):
        e=dict(entry);ident=e['id']
        e['input_url']=f'/api/examples/{ident}/input';e['result_url']=f'/api/examples/{ident}/result'
        return e
    def get(self,ident):
        if not ident or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in ident):raise WebError('EXAMPLE_NOT_FOUND',404)
        for item in self.all():
            if item['id']==ident:return item
        raise WebError('EXAMPLE_NOT_FOUND',404)
    def resource(self,ident,role):
        self.get(ident)
        if role not in ('input','result'):raise WebError('EXAMPLE_RESOURCE_NOT_FOUND',404)
        path=self.root/ident/(role+'.ifc')
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(self.root):raise WebError('EXAMPLE_RESOURCE_NOT_FOUND',404)
        return path
