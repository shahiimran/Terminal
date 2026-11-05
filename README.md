# SPIDER SHELL

A Termux-inspired browser cloud-shell prototype.

## Security model
- FastAPI API protected by a required bearer token (at least 24 chars).
- Each command runs in a fresh Docker container.
- Network disabled; root filesystem read-only; all capabilities dropped.
- No-new-privileges, PID/memory/CPU limits, timeout, non-root user.
- Only a small allowlist of commands; commands are passed as argv (never shell=True).
- Persistent single-user workspace mounted at /work.

> Single-user prototype only. Do not expose publicly until adding per-user authentication, rate limits, quotas, audit logs and stronger isolation (rootless Docker or microVMs). Docker alone is not a complete security boundary.

## Local setup
```bash
docker build -t spider-shell-runner:1.0 ./runner
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export SPIDER_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export SPIDER_WORKSPACE=./workspace
uvicorn app:app --host 127.0.0.1 --port 8000
```
Open http://127.0.0.1:8000 and enter the token. Use HTTPS for remote access. Never commit the token.

## Commands
`help`, `pwd`, `ls`, `echo`, `cat`, `mkdir`, `touch`, `python script.py`, `whoami`, `date`.

No arbitrary Bash, package installation, SSH or multi-user accounts in v1.