#!/usr/bin/env python3
"""
TwisterLab API v5.2.1 — Refined Orchestration Metadata
Improving agent descriptions to guide LLM planning precision.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent
SRC = BASE / "src"

NEW_VERSION = "v5.2.1"
REGISTRY = "localhost:5000"
IMAGE = f"{REGISTRY}/twisterlab-api:{NEW_VERSION}"

def run(cmd, **kwargs):
    print(f"\n$ {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, **kwargs, shell=isinstance(cmd, str))
    if result.returncode != 0:
        print(f"[ERROR] Command failed with exit code {result.returncode}")
    return result

def step1_build_dockerfile():
    dockerfile = """FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip install --no-cache-dir \\
    fastapi \\
    "uvicorn[standard]" \\
    pydantic \\
    pydantic-settings \\
    sqlalchemy \\
    asyncpg \\
    aiosqlite \\
    redis \\
    httpx \\
    requests \\
    psutil \\
    prometheus-client \\
    prometheus_fastapi_instrumentator \\
    "python-jose[cryptography]" \\
    "passlib[bcrypt]" \\
    websockets \\
    notion-client \\
    pandas \\
    numpy \\
    opentelemetry-api \\
    opentelemetry-sdk \\
    opentelemetry-instrumentation \\
    opentelemetry-instrumentation-fastapi \\
    opentelemetry-exporter-jaeger
COPY src/ ./src/
ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "twisterlab.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
"""
    path = BASE / "Dockerfile.v5.2.1"
    path.write_text(dockerfile, encoding="utf-8")

def step2_build():
    run(["docker", "build", "-f", "Dockerfile.v5.2.1", "-t", IMAGE, "."])

def step3_push():
    tar_path = BASE / "twisterlab-api-v5.2.1.tar"
    run(["docker", "save", IMAGE, "-o", str(tar_path)])
    ssh_host = "twisterlab-ubuntu"
    remote_tar = "/tmp/twisterlab-api-v5.2.1.tar"
    run(["scp", str(tar_path), f"{ssh_host}:{remote_tar}"])
    import_cmd = f"sudo k3s ctr images import {remote_tar} && rm -f {remote_tar}"
    run(["ssh", ssh_host, import_cmd])
    if tar_path.exists():
        tar_path.unlink()

def step4_update_deployment():
    run(["kubectl", "set", "image", "deployment/twisterlab", f"twisterlab={IMAGE}", "-n", "twisterlab"])
    patch = {"spec": {"template": {"metadata": {"annotations": {"twisterlab/build": NEW_VERSION, "kubectl.kubernetes.io/restartedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}}}}}
    run(["kubectl", "patch", "deployment", "twisterlab", "-n", "twisterlab", "--type", "merge", "-p", json.dumps(patch)])
    run(["kubectl", "rollout", "status", "deployment/twisterlab", "-n", "twisterlab", "--timeout=120s"])

def main():
    step1_build_dockerfile()
    step2_build()
    step3_push()
    step4_update_deployment()
    print(f"\n✅ TwisterLab API {NEW_VERSION} (Precision Metadata) deployed.")

if __name__ == "__main__":
    main()
