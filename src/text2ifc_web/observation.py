"""Passive Provider call observation: return the original object unchanged, never retry."""
class ObservedProvider:
    def __init__(self, wrapped, emit):
        self.wrapped=wrapped
        self.emit=emit

    def __getattr__(self, name):
        value=getattr(self.wrapped,name)
        if name not in ('generate_live','generate_candidate') or not callable(value):
            return value
        def call(**kwargs):
            state=kwargs.get('state') or {}
            event={'stage':str(state.get('stage','provider')),'attempt':state.get('attempt'),'kind':'provider_call'}
            self._notify({**event,'action':'started'})
            try:
                result=value(**kwargs)
            except Exception as error:
                self._notify({**event,'action':'failed','error_type':type(error).__name__})
                raise
            output=getattr(result,'output',result)
            metadata=getattr(output,'metadata',{}) or {}
            usage={k:v for k,v in (metadata.get('usage') or {}).items() if type(v) in (int,float)}
            self._notify({**event,'action':'completed','usage':usage})
            return result
        return call

    def _notify(self, event):
        try:self.emit(event)
        except Exception:pass
