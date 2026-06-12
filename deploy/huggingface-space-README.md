---
title: CAPScore Agent
emoji: 🛡️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 8000
pinned: false
license: mit
---

# CAPScore Agent

Verifiable due diligence for the agent economy — CROO Hackathon 2026.

This Space runs the single-container build (FastAPI serves both the dashboard
and the REST API). To deploy:

1. Create a **Docker** Space at https://huggingface.co/new-space
2. Copy this file as the Space's `README.md` (the YAML header above is required).
3. Push the repository contents (root `Dockerfile`, `api/`, `frontend/`).
4. Add Space **Secrets**: `ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY`,
   `OPENAI_MODEL=gpt-4o-mini`.

The app will be live at `https://<user>-capscore-agent.hf.space`.
Set `CAPSCORE_PUBLIC_BASE_URL` to that URL after the first build.
