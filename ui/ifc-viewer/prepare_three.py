"""Install only pinned public Three.js browser modules; no IFC is transmitted."""
from pathlib import Path
import io,tarfile,urllib.request,json
HERE=Path(__file__).parent/'vendor'
URL='https://registry.npmjs.org/three/-/three-0.186.0.tgz'
with urllib.request.urlopen(URL,timeout=45) as response: payload=response.read(20*1024*1024)
with tarfile.open(fileobj=io.BytesIO(payload),mode='r:gz') as package:
    wanted={'package/build/three.core.js':'three.core.js','package/build/three.module.js':'three.module.js','package/examples/jsm/controls/OrbitControls.js':'OrbitControls.js','package/LICENSE':'THREE-LICENSE.txt'}
    HERE.mkdir(parents=True,exist_ok=True)
    for source,dest in wanted.items():
        data=package.extractfile(source).read().decode('utf-8')
        if dest=='OrbitControls.js':data=data.replace("from 'three';","from './three.module.js';")
        (HERE/dest).write_text(data,encoding='utf-8')
(HERE/'package.json').write_text('{"type":"module","private":true}\n')
print(json.dumps({'three':'0.186.0','public_package':URL,'modules':list(wanted.values()),'IFC_uploaded':False}))
