# SPIDER SHELL v2.0.0

Browser-based, mobile-friendly development workspace.

## v2.0 features
- Terminal interface.
- Workspace file manager: list, upload (5 MB), download, edit, save and delete.
- Run saved Python, Node.js and Bash scripts.
- Restricted Git commands: status, log, diff, init.
- Disposable Docker execution: no network, read-only root, dropped capabilities, non-root user, PID/memory/CPU limits and timeout.
- Bearer-token API authentication.

## Limitations and deployment security
Single-user prototype, not public multi-user cloud shell and not full Termux. No arbitrary interactive shell, package installation, SSH, background jobs or multi-user isolation. Do not expose publicly until adding user accounts, isolated per-user storage/runners, quotas, rate limits, audit logs, HTTPS and a reviewed sandbox boundary (prefer microVMs/rootless containers). Never mount Docker socket into an untrusted app container.

Managed web hosting may not expose Docker for nested execution. Use a dedicated hardened Linux host or separate isolated runner service.

## Local setup
1. Install Python 3.11+ and Docker Engine.
2. Build: docker build -t spider-shell-runner:2.0 ./runner
3. Install: pip install -r requirements.txt
4. Set SPIDER_API_TOKEN to a random secret of at least 24 characters.
5. Start: uvicorn app:app --host 127.0.0.1 --port 8000
6. Open http://127.0.0.1:8000

Environment: SPIDER_API_TOKEN (required), SPIDER_WORKSPACE (default ./workspace), SPIDER_RUNNER_IMAGE (default spider-shell-runner:2.0), SPIDER_TIMEOUT_SECONDS (1–20).

Never commit API tokens or private workspace files to GitHub.
