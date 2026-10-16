# UI 远程重建验证记录（2026-10-16）

从 GitHub 的 `codex/ui-development` 分支独立浅克隆，以已发布提交 `d077d8db6539b2b3161ca0e7dfa2f5639b32303e` 为基线，创建全新 Python 3.12.4 虚拟环境，仅按 `.[web,web-test]` 安装公开依赖。未复制旧工作树的 `.env`、解释器、私有样例、运行状态或未跟踪文件。Node.js 使用 24.11.0；JS/WASM 使用仓库版本，无需 npm 安装。

默认空工作台、公共 IFC 渲染、真实 HTTP 上传、源下载和请求准备均通过。真实模型执行始终关闭，未新增 Provider 调用，未运行全仓库 Preflight，原 Repair 工作树与进程未作更改。此前真实联调结果仍以[工作台说明](../../ui/ifc-viewer/README.md)及[主计划](../plans/repair-ui-plan.md)为准，本次重建不增加真实 Repair 成功案例。

## 发现并修复

- Web extra 漏掉启动即需要的 `lxml`，新环境报 `ModuleNotFoundError`。补入与既有依赖一致的 `lxml>=5,<6`，未加入可选向量模型或完整研究环境。
- 启动器修改端口后，来源校验仍固定默认端口，导致新端口提交被拒绝。现按配置只允许 localhost / 127.0.0.1 上的网页和 API 端口；测试同时确认陌生端口和外部来源继续被拒绝。

## 验证范围

- 100 项 Node 检查、91 项相关 Python 检查通过，无跳过。Python 检查在新虚拟环境中离线执行。
- 专用 Edge 配置与 SwiftShader 验证空工作台初始化；从远程 LFS 取回的 case-002 公共 IFC2X3 显示 295 个对象、214 个有网格的构件。解析诊断保留，不据此宣称任意 IFC 完整保真。
- 网页 4278 代理 API 4280：上传 201、请求准备 201、源下载逐字节一致；执行请求返回 503 / `REPAIR_EXECUTION_NOT_ENABLED`，符合默认禁用的预期。
- `pip check` 通过，用户 site-packages 关闭，Web 模块来自独立克隆。没有安装 pyparsing、向量检索模型或复制原机私有缓存来补足测试。
- 只从远程恢复两个限定测试需要的公开 IFC，没有扫描或下载整套数据。

## 重新检出与启动

```powershell
$env:GIT_LFS_SKIP_SMUDGE='1'
git clone --single-branch --branch codex/ui-development https://github.com/770122whrt/text2IFC.git text2IFC-ui
Set-Location text2IFC-ui
git config core.longpaths true
Remove-Item Env:GIT_LFS_SKIP_SMUDGE -ErrorAction SilentlyContinue
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[web,web-test]"
$env:IFC_VIEWER_PORT='4278'
$env:TEXT2IFC_API_PORT='4280'
$env:TEXT2IFC_UI_LIVE='0'
node ui/ifc-viewer/launcher.mjs start
```

访问 `http://127.0.0.1:4278/ifc-viewer/`，点击“打开 IFC”选择自己的 IFC2X3。停止时在同一目录、保留端口变量，运行 `node ui/ifc-viewer/launcher.mjs stop`。

限定测试额外需要两个具体公共 LFS 文件：

```powershell
git lfs pull --include="dataset/processed/ifc-repair/repair-comparison/development/case-001/public/model.ifc,dataset/processed/ifc-repair/repair-comparison/development/case-002/public/model.ifc" --exclude=""
node --test ui/ifc-viewer/tests/*.test.mjs ui/prototype/tests/*.test.mjs
.\.venv\Scripts\python.exe -m pytest tests/web tests/ifc_repair/test_orchestrator_terminal_matrix.py tests/ifc_repair/test_clarification_state.py ui/ifc-viewer/tests/native_geometry_test.py -q --tb=short --basetemp=.tmp/rebuild-check
```

## 私有资源和恢复边界

网页与默认 API 不需要旧目录的私有 174 样例、Provider 密钥、历史任务和实验数据。复看旧真实案例、截图及调试材料时，从用户私有备份恢复。向量检索模型和数据库需要另行配置，本次没有准备或验收；LFS 指针也不是实际 IFC 文件。

旧 UI 工作树现存普通文件另有私有归档、逐文件 SHA-256 清单和独立解压校验；Git 历史、本机持有且当前 UI 提交引用的 LFS 对象、对话快照及移交说明独立保存。本机未持有的 LFS 对象列入缺失清单，没有为备份下载整套数据。私有备份包含凭据和研究资产，不上传公共仓库。
