#!/usr/bin/env bash
# Invoked inside a resource-limited installer; no repository or credentials mount.
set -euo pipefail
test -f /.dockerenv
export DEBIAN_FRONTEND=noninteractive
unset DEEPSEEK_API_KEY OPENAI_API_KEY ANTHROPIC_API_KEY DSH_HOME
if test "${1:-}" = common; then
    apt-get update
    apt-get install -y --no-install-recommends libgomp1 libstdc++6 libatomic1
    python -m venv /opt/venv
    /opt/venv/bin/python -m pip install --disable-pip-version-check ifcopenshell==0.8.5
    mkdir -p /workspace /state
    chown 10001:10001 /workspace /state
    /opt/venv/bin/python -c 'import ifcopenshell; print(ifcopenshell.version)'
elif test "${1:-}" = dsh; then
    /opt/venv/bin/python -m pip install --disable-pip-version-check /wheels/*.whl
    /opt/venv/bin/python -c 'import deepseek_harness_runtime; print(deepseek_harness_runtime.bundled_runtime_path())'
else
    exit 2
fi
/opt/venv/bin/python -m pip check
/opt/venv/bin/python -m pip freeze
