# SPIDER SHELL

Termux-inspired browser cloud-shell prototype. Current code version: **1.1.0**.

## v1.1 features
- Mobile-friendly browser terminal UI.
- Bearer-token protected API.
- Upload and download files (2 MB per upload).
- Workspace file listing.
- Restricted command allowlist and Python script execution.
- Each command runs in a disposable, network-disabled Docker container with read-only root, dropped capabilities, non-root user, CPU/memory/PID limits and timeout.

## Important deployment/security note
This is a **single-user prototype**, not a public multi-user cloud shell. Do not expose it to the public internet yet. Before public launch, add per-user authentication and isolated workspaces, rate limits, storage quotas, audit logs, secure secret management, HTTPS, and stronger isolation (prefer rootless Docker or microVMs). Do not mount the Docker socket into an untrusted web container. A standard managed web host may not provide a Docker daemon for nested container execution; use a dedicated, hardened Linux VM/host for the runner or a separate isolated execution service.

The current shell is intentionally restricted; it is not full Termux. Arbitrary Bash, APT, unrestricted PIP installation, SSH, and multi-user accounts are not enabled.

## Local development
1. Install Python 3.11+ and Docker Engine.
2. Build runner: `docker build -t spider-shell-runner:1.1 ./runner`
3. Install dependencies: `pip install -r requirements.txt`
4. Set a strong token: `export SPIDER_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"`
5. Start API: `uvicorn app:app --host 127.0.0.1 --port 8000`
6. Open `http://127.0.0.1:8000`.

Environment variables: `SPIDER_API_TOKEN` (required, 24+ chars), `SPIDER_WORKSPACE` (default ./workspace), `SPIDER_RUNNER_IMAGE` (default spider-shell-runner:1.1), `SPIDER_TIMEOUT_SECONDS` (1–15 seconds).

Never commit API tokens or private workspace files to GitHub.