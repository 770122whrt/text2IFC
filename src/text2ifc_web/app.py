"""Independent ASGI application and reusable router for native Repair integration."""
from contextlib import asynccontextmanager
from pathlib import Path
import os
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import APIRouter, FastAPI, File, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .contracts import AnswerRequest, PrepareRequest, StartRequest, WebError
from .service import RepairService


API_VERSION = '0.1.0'


def create_router(service: RepairService, *, max_upload_bytes: int, examples_root=None):
    """Mount this router with prefix='/api' in a future combined application."""
    router = APIRouter()
    from .examples import Examples
    examples=Examples(examples_root)

    @router.get('/examples',tags=['examples'])
    def example_list():return {'examples':examples.all(),'execution':'read_only_history'}

    @router.get('/examples/{example_id}',tags=['examples'])
    def example_details(example_id: str):return examples.get(example_id)

    @router.get('/examples/{example_id}/{role}',tags=['examples'])
    def example_resource(example_id: str,role: str):
        return FileResponse(examples.resource(example_id,role),media_type='application/x-step',filename=example_id+'-'+role+'.ifc',headers={'Cache-Control':'no-store'})

    @router.get('/capabilities', tags=['service'])
    def capabilities():
        return {'api_version':API_VERSION, 'input_schemas':['IFC2X3'], 'selection_text':True, 'multiple_targets':True,'max_targets':16,
                'runtime':getattr(service,'runtime_status',{'enabled':service.execution_enabled}),
                'execution_enabled':service.execution_enabled, 'rework_enabled':False,
                'progress':'native_committed_boundaries','max_upload_bytes':max_upload_bytes,
                'execution_disabled_reason':None if service.execution_enabled else 'REPAIR_EXECUTION_NOT_ENABLED'}

    @router.post('/ifc-inputs', status_code=201, tags=['inputs'])
    def upload(file: Annotated[UploadFile, File(description='Unmodified IFC2X3 input file')]):
        try:
            data = file.file.read(max_upload_bytes+1)
            if len(data)>max_upload_bytes:
                raise WebError('IFC_UPLOAD_TOO_LARGE',413)
            return service.upload(file.filename,data)
        finally:
            file.file.close()

    @router.get('/ifc-inputs/{input_id}', tags=['inputs'])
    def input_metadata(input_id: str):
        return service.store.input(input_id)

    @router.get('/ifc-inputs/{input_id}/source', tags=['inputs'])
    def source(input_id: str):
        metadata = service.store.input(input_id)
        return FileResponse(service.store.source(input_id),media_type='application/x-step',filename=metadata['source_name'],headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

    @router.post('/repair-requests/prepare',status_code=201,tags=['requests'])
    def prepare(payload: PrepareRequest):
        return service.prepare(payload)

    @router.get('/repair-requests/{request_id}',tags=['requests'])
    def prepared(request_id: str):
        return service.read_prepared(request_id)

    @router.post('/repair-tasks',status_code=202,tags=['tasks'])
    def start(payload: StartRequest):
        return service.start(payload)

    @router.get('/repair-tasks/{task_id}',tags=['tasks'])
    def task(task_id: str):
        return service.task(task_id)

    @router.get('/repair-tasks/{task_id}/summary',tags=['tasks'])
    def summary(task_id: str):
        import json
        task=service.store.task(task_id)
        path=service.store.root/'summaries'/(task_id+'.json')
        if task['busy'] or not path.is_file():return {'available':False,'rows':[]}
        return {'available':True,**json.loads(path.read_text(encoding='utf-8'))}

    @router.get('/repair-tasks/{task_id}/events',tags=['tasks'])
    def events(task_id: str, after: Annotated[int, Query(ge=-1)] = -1, activity_after: Annotated[int, Query(ge=-1)] = -1):
        return service.events(task_id,after,activity_after)

    @router.post('/repair-tasks/{task_id}/answers',status_code=202,tags=['tasks'])
    def answer(task_id: str, payload: AnswerRequest):
        return service.answer(task_id,payload)

    @router.get('/repair-tasks/{task_id}/artifacts',tags=['artifacts'])
    def artifacts(task_id: str):
        return {'artifacts':[{k:v for k,v in item.items() if not k.startswith('_')} for item in service.artifacts(task_id)]}

    @router.get('/repair-tasks/{task_id}/artifacts/{artifact_id}',tags=['artifacts'])
    def artifact(task_id: str, artifact_id: str):
        item = service.artifact(task_id,artifact_id)
        suffix = Path(item['name']).suffix
        mime = {'.ifc':'application/x-step','.json':'application/json','.md':'text/plain','.txt':'text/plain','.sqlite':'application/octet-stream'}.get(suffix,'application/octet-stream')
        return FileResponse(item['_path'],filename=item['name'],media_type=mime,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

    return router


def create_app(storage_root: Path | str, *, api_factory=None, executor=None,
               rework_policy=None, max_upload_bytes=100*1024*1024, examples_root=None,
               allowed_hosts=('127.0.0.1','localhost'),
               allowed_origins=('http://127.0.0.1:4178','http://localhost:4178','http://127.0.0.1:4180','http://localhost:4180')) -> FastAPI:
    """Default is prepare-only. Explicit server-side dependency injection enables execution.

    No environment API key is automatically loaded. Configure a native RepairAPI factory
    only after the applicable stage admission and budget have been approved.
    """
    service = RepairService(storage_root,api_factory=api_factory,executor=executor,rework_policy=rework_policy)
    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            service.close()
    app = FastAPI(title='text2IFC Repair API',version=API_VERSION,lifespan=lifespan,
                  openapi_url='/api/openapi.json',docs_url='/api/docs',redoc_url=None)
    app.state.repair_service = service
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=list(allowed_hosts))

    @app.middleware('http')
    async def local_request_boundary(request: Request,call_next):
        origin = request.headers.get('origin')
        if origin and origin not in allowed_origins:
            return JSONResponse({'error':{'code':'ORIGIN_NOT_ALLOWED'}},status_code=403)
        if request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'error':{'code':'ORIGIN_NOT_ALLOWED'}},status_code=403)
        length = request.headers.get('content-length')
        if length:
            try:
                if int(length)<0 or int(length)>max_upload_bytes+65536:
                    return JSONResponse({'error':{'code':'REQUEST_TOO_LARGE'}},status_code=413)
            except ValueError:
                return JSONResponse({'error':{'code':'INVALID_CONTENT_LENGTH'}},status_code=400)
        response = await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Cache-Control']='no-store'
        return response

    @app.exception_handler(WebError)
    async def web_error(request,error):
        return JSONResponse({'error':{'code':error.code}},status_code=error.status)

    @app.get('/api/health',tags=['service'])
    def health():
        return {'service':'text2IFC-repair-api','api_version':API_VERSION,'pid':os.getpid(),
                'instance':os.environ.get('TEXT2IFC_API_INSTANCE','foreground'),
                'execution_enabled':service.execution_enabled,'rework_enabled':False}

    app.include_router(create_router(service,max_upload_bytes=max_upload_bytes,examples_root=examples_root),prefix='/api')
    return app
