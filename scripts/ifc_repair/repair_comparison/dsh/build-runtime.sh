#!/usr/bin/env bash
# Run only in the explicitly authorized builder container, never on the host.
set -euo pipefail
test -f /.dockerenv
test -r /export/source.tar
test -d /export
if test "${DSH_BUILD_DEADLINE_WRAPPED:-}" != 1; then
    remaining=$(( $(date -d "$(cat /export/build-started.txt)" +%s) + 3600 - $(date +%s) ))
    test "$remaining" -gt 0
    exec timeout --signal=TERM --kill-after=15s "$remaining" env DSH_BUILD_DEADLINE_WRAPPED=1 bash /build-runtime.sh
fi
exec > >(tee -a /export/build.log) 2>&1
export DEBIAN_FRONTEND=noninteractive
export LEFTHOOK=0
export DSH_BUILD_CLIENT_PROFILE=official
export DSH_CLIENT_COMMIT_HASH=4878cdabd87d4041bdaff61d04c966883b9fd07a
export CI=true
unset DEEPSEEK_API_KEY OPENAI_API_KEY ANTHROPIC_API_KEY DSH_HOME
printf 'Build started: %s\n' "$(date -u +%FT%TZ)"
if ! test -x /opt/build-venv/bin/uv; then
    apt-get update
    apt-get install -y --no-install-recommends python3-venv python3-pip musl-tools patchelf
    python3 -m venv /opt/build-venv
    /opt/build-venv/bin/python -m pip install --disable-pip-version-check uv==0.11.23
fi
export PATH="/opt/build-venv/bin:$PATH"
if ! command -v pnpm >/dev/null; then npm install --global pnpm@11.7.0; fi
mkdir -p /build/source
if ! test -f /build/source/.archive-restored; then
    # Git archive preserves Unix modes/symlinks and avoids Windows checkout CRLF.
    # This literal destination is inside the dedicated build volume, not /input.
    test ! -L /build/source
    test "$(readlink -f /build/source)" = /build/source
    rm -rf -- /build/source
    mkdir /build/source
    tar -C /build/source -xf /export/source.tar
    touch /build/source/.archive-restored
fi
cd /build/source
node --version
pnpm --version
python --version
uv --version
test "$(node -p 'JSON.parse(require("node:fs").readFileSync("package.json")).version')" = '0.2.0-rc.1'
pnpm install --frozen-lockfile
pnpm exec tsx scripts/build-exe-for-python-sdk.ts --targets=node24-linux-x64
python scripts/build-python-release.py --package sdk --output-dir /export/wheels
python scripts/build-python-release.py --package runtime --platform linux-x64 --runtime-exe dist-exe/deepseek-harness-sdk-runtime-linux-x64 --output-dir /export/wheels
sha256sum /export/wheels/*.whl > /export/wheel-sha256.txt
printf 'Build completed: %s\n' "$(date -u +%FT%TZ)"
