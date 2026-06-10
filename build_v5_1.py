#!/usr/bin/env python3
"""
TwisterLab API v5.1.0 — Active Observability & Resilience Deploy Script
========================================================================
Builds and pushes a clean Docker image v5.1.0 to the local registry,
and deploys it to the EdgeServer with a RollingUpdate strategy and the
resilience kill-switch environment variable.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent
SRC = BASE / "src"

NEW_VERSION = "v5.1.0"
REGISTRY = "localhost:5000"
IMAGE = f"{REGISTRY}/twisterlab-api:{NEW_VERSION}"


def run(cmd, **kwargs):
    print(f"\n$ {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, **kwargs, shell=isinstance(cmd, str))
    if result.returncode != 0:
        print(f"[ERROR] Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result


def step1_build_dockerfile():
    print("\n" + "="*60)
    print("STEP 1: Write production Dockerfile")
    print("="*60)
    dockerfile = """FROM python:3.11-slim

LABEL maintainer="TwisterLab" version="{version}" description="TwisterLab API - Resilience & Observability v5.1.0"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Python deps
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
    numpy

# Copy consolidated source tree
COPY src/ ./src/

ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "twisterlab.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
""".format(version=NEW_VERSION)

    path = BASE / "Dockerfile.v5"
    path.write_text(dockerfile, encoding="utf-8")
    print(f"  ✅ Written: Dockerfile.v5")


def step2_build():
    print("\n" + "="*60)
    print(f"STEP 2: Build Docker image → {IMAGE}")
    print("="*60)
    run([
        "docker", "build",
        "-f", str(BASE / "Dockerfile.v5"),
        "-t", IMAGE,
        "-t", f"{REGISTRY}/twisterlab-api:latest",
        str(BASE)
    ])
    print(f"\n  ✅ Image built: {IMAGE}")


def step3_push():
    print("\n" + "="*60)
    print(f"STEP 3: Save and SCP image to EdgeServer")
    print("="*60)
    tar_path = BASE / "twisterlab-api-v5.tar"
    print(f"Saving image to tar: {tar_path}")
    run(["docker", "save", IMAGE, "-o", str(tar_path)])
    
    ssh_host = "twisterlab-ubuntu"
    remote_tar = "/tmp/twisterlab-api-v5.tar"
    print(f"Copying tar to {ssh_host}:{remote_tar} via SCP...")
    run(["scp", str(tar_path), f"{ssh_host}:{remote_tar}"])
    
    print("Importing image into k3s containerd...")
    import_cmd = (
        f"sudo k3s ctr images import {remote_tar} && "
        "echo '--- Available twisterlab images ---' && "
        "sudo k3s ctr images list | grep twisterlab && "
        f"rm -f {remote_tar}"
    )
    run(["ssh", ssh_host, import_cmd])
    
    # Cleanup local tar
    if tar_path.exists():
        tar_path.unlink()
    print("\n  ✅ Image successfully transferred and imported on EdgeServer.")



def step4_update_deployment():
    print("\n" + "="*60)
    print(f"STEP 4: Update Kubernetes deployment to {IMAGE}")
    print("="*60)
    
    # Update image
    run([
        "kubectl", "set", "image",
        "deployment/twisterlab",
        f"twisterlab={IMAGE}",
        "-n", "twisterlab"
    ])
    
    # Apply RollingUpdate strategy and MAESTRO_RESILIENCE_MODE kill-switch
    patch = {
        "spec": {
            "strategy": {
                "type": "RollingUpdate",
                "rollingUpdate": {
                    "maxSurge": 1,
                    "maxUnavailable": 0
                }
            },
            "template": {
                "metadata": {
                    "annotations": {
                        "kubectl.kubernetes.io/restartedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "twisterlab/build": NEW_VERSION,
                        "twisterlab/hotfix": "none"
                    }
                },
                "spec": {
                    "volumes": [
                        {
                            "name": "archives",
                            "persistentVolumeClaim": {"claimName": "twisterlab-archive-pvc"}
                        }
                    ],
                    "containers": [{
                        "name": "twisterlab",
                        "image": IMAGE,
                        "volumeMounts": [
                            {
                                "name": "archives",
                                "mountPath": "/app/archives"
                            }
                        ],
                        "env": [
                            {
                                "name": "MAESTRO_RESILIENCE_MODE",
                                "value": "db_hybrid"
                            }
                        ],
                        "resources": {
                            "requests": {"cpu": "500m", "memory": "512Mi"},
                            "limits":   {"cpu": "2000m", "memory": "1024Mi"}
                        }
                    }]
                }
            }
        }
    }
    patch_path = BASE / "deployment_patch_v5.json"
    patch_path.write_text(json.dumps(patch), encoding="utf-8")
    
    run([
        "kubectl", "patch", "deployment", "twisterlab",
        "-n", "twisterlab",
        "--type", "merge",
        "--patch-file", str(patch_path)
    ])
    
    print("\n  ✅ Deployment patched. Watching rollout...")
    run(["kubectl", "rollout", "status", "deployment/twisterlab", "-n", "twisterlab", "--timeout=120s"])


def step5_cleanup_configmaps():
    print("\n" + "="*60)
    print("STEP 5: Delete legacy hotfix ConfigMaps")
    print("="*60)
    stale_cms = [
        "ui-hotfix-v382",
        "api-hotfix-v1",
        "api-hotfix-v3",
        "db-hotfix-v1",
        "utils-hotfix-v2",
    ]
    for cm in stale_cms:
        result = subprocess.run(
            ["kubectl", "delete", "configmap", cm, "-n", "twisterlab", "--ignore-not-found"],
            capture_output=True, text=True
        )
        if "deleted" in result.stdout:
            print(f"  [DELETE] {cm}")
        else:
            print(f"  [SKIP]   {cm} (not found)")
    print("\n  ✅ Hotfix ConfigMaps removed.")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=" * 56)
    print(f"  TwisterLab API Build -- {NEW_VERSION}")
    print("  Resilience & Observability Update")
    print("=" * 56)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-push", action="store_true", help="Build but do not push or deploy")
    parser.add_argument("--skip-cleanup", action="store_true", help="Do not delete ConfigMaps at the end")
    args = parser.parse_args()

    step1_build_dockerfile()
    step2_build()

    if not args.skip_push:
        step3_push()
        step4_update_deployment()

    if not args.skip_cleanup and not args.skip_push:
        step5_cleanup_configmaps()

    print("\n" + "="*60)
    print("🚀 TwisterLab API v5.1.0 build & deploy complete!")
    print(f"   Image: {IMAGE}")
    print("   Strategy: RollingUpdate (maxSurge=1, maxUnavailable=0)")
    print("   Resilience Mode: db_hybrid (kill-switch support)")
    print("="*60)


if __name__ == "__main__":
    main()
