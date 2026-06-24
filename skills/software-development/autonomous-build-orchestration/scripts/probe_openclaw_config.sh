#!/usr/bin/env bash
# Verify host access to the OpenClaw live config path.
# Run this at the start of any session that needs to inspect or migrate
# /docker/openclaw-xr8h/data/.openclaw/openclaw.json.
set -euo pipefail

CONFIG="/docker/openclaw-xr8h/data/.openclaw/openclaw.json"

echo "== OpenClaw config probe =="
if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: $CONFIG not found"
    exit 1
fi

ls -la "$CONFIG"
python3 - <<PY
import json
import re
with open("$CONFIG") as f:
    data=json.load(f)
secret_paths=[]
for path,val in json_walk(data):
    k=path.split(".")[-1]
    if any(x in k.lower() for x in ["token","key","secret","password"]):
        secret_paths.append(path)
def json_walk(obj, prefix=""):
    if isinstance(obj, dict):
        for k,v in obj.items():
            yield from json_walk(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            yield from json_walk(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj
print(f"Secret-like paths: {len(secret_paths)}")
for p in secret_paths:
    print(f"  {p}")
print(f"Primary model: {data.get('agents',{}).get('defaults',{}).get('model',{}).get('primary')}")
PY

echo "Probe OK"
