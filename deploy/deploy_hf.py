#!/usr/bin/env python3
"""
Deploy CAPScore to a Hugging Face Docker Space.

Usage:
    HF_TOKEN=hf_xxx python deploy/deploy_hf.py [space_name]

Requires: pip install huggingface_hub
Reads optional secrets from the environment (or .env) and sets them as Space
secrets: ANTHROPIC_API_KEY, OPENAI_API_KEY, OPENAI_MODEL.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from huggingface_hub import HfApi, add_space_secret, create_repo, upload_folder

REPO_ROOT = Path(__file__).resolve().parent.parent

SPACE_README = """---
title: CAPScore Agent
emoji: 🛡️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 8000
pinned: false
license: mit
---

# CAPScore Agent — Verifiable Due Diligence for the Agent Economy

CROO Hackathon 2026. FastAPI serves both the dashboard (at `/`) and the REST API
(`/health`, `/jobs/...`). Submit a GitHub repo or agent listing and receive a
judging-aligned scorecard plus a verifiable proof pack (SHA-256 hash, manifest,
attestation, execution log).
"""

IGNORE = [
    ".git/*", ".git", ".venv/*", ".venv", "runs/*", "runs",
    "node_modules/*", "**/node_modules/*", ".env", "*.pyc", "__pycache__/*",
    "**/__pycache__/*", "*.egg-info/*", "**/*.egg-info/*",
]


def _load_env_file() -> None:
    env = REPO_ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def main() -> int:
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("ERROR: HF_TOKEN not set", file=sys.stderr)
        return 1

    _load_env_file()
    space_name = sys.argv[1] if len(sys.argv) > 1 else "capscore-agent"

    api = HfApi(token=token)
    user = api.whoami()["name"]
    repo_id = f"{user}/{space_name}"
    print(f"[hf] deploying to Space: {repo_id}")

    create_repo(repo_id, repo_type="space", space_sdk="docker",
                token=token, exist_ok=True)

    # Write the Space README (with required YAML frontmatter) then upload.
    readme = REPO_ROOT / "README.md"
    original = readme.read_text(encoding="utf-8") if readme.exists() else ""
    backup = None
    try:
        backup = original
        readme.write_text(SPACE_README, encoding="utf-8")
        upload_folder(
            repo_id=repo_id, repo_type="space", folder_path=str(REPO_ROOT),
            token=token, ignore_patterns=IGNORE,
            commit_message="Deploy CAPScore single-container build",
        )
    finally:
        if backup is not None:
            readme.write_text(backup, encoding="utf-8")

    # Set Space secrets (never committed to git).
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENAI_MODEL",
                "ANTHROPIC_MODEL"):
        val = os.environ.get(key)
        if val:
            add_space_secret(repo_id, key, val, token=token)
            print(f"[hf] set secret: {key}")

    url = f"https://{user.replace('_', '-')}-{space_name}.hf.space"
    print(f"[hf] done. Building... will be live at: {url}")
    print(f"[hf] check: {url}/health")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
