import os, re, shlex, subprocess, uuid, hmac
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT=Path(__file__).resolve().parent
WORK=Path(os.getenv("SPIDER_WORKSPACE","./workspace")).resolve()
TOKEN=os.getenv("SPIDER_API_TOKEN","")
IMAGE=os.getenv("SPIDER_RUNNER_IMAGE","spider-shell-runner:1.0")
TIMEOUT=min(max(int(os.getenv("SPIDER_TIMEOUT_SECONDS","8")),1),15)
if len(TOKEN)<24: raise RuntimeError("Set SPIDER_API_TOKEN (minimum 24 characters).")
WORK.mkdir(parents=True,exist_ok=True)
app=FastAPI(title="SPIDER SHELL",version="1.0.0")
app.mount("/static",StaticFiles(directory=ROOT/"static"),name="static")
ALLOW={"pwd","ls","echo","cat","mkdir","touch","python","python3","whoami","date"}
NAME=re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
class Request(BaseModel):
    command:str=Field(min_length=1,max_length=500)
def auth(value):
    if not value or not hmac.compare_digest(value,"Bearer "+TOKEN):
        raise HTTPException(401,"Unauthorized")
def parse(raw):
    try: p=shlex.split(raw)
    except ValueError: raise HTTPException(400,"Invalid syntax")
    if not p: raise HTTPException(400,"Empty command")
    if p==["help"]: return p
    if p[0] not in ALLOW: raise HTTPException(400,"Command not allowed. Type help.")
    if len(p)>12: raise HTTPException(400,"Too many arguments")
    for a in p[1:]:
        if a.startswith("-") or "/" in a or "\\" in a or not NAME.fullmatch(a):
            raise HTTPException(400,"Only simple workspace names are supported")
    if p[0] in {"python","python3"} and (len(p)!=2 or not p[1].endswith(".py")):
        raise HTTPException(400,"Usage: python script.py")
    return p
@app.get("/")
def home(): return FileResponse(ROOT/"static/index.html")
@app.get("/health")
def health(): return {"status":"ok","name":"SPIDER SHELL"}
@app.post("/api/run")
def run(body:Request,authorization:str|None=Header(default=None)):
    auth(authorization); p=parse(body.command)
    if p==["help"]: return {"output":"Allowed: pwd ls echo cat mkdir touch python script.py whoami date","exit_code":0}
    args=["docker","run","--rm","--name","spider-"+uuid.uuid4().hex[:12],"--network","none","--read-only","--cap-drop","ALL","--security-opt","no-new-privileges:true","--pids-limit","64","--memory","128m","--cpus","0.5","--user","10001:10001","--tmpfs","/tmp:rw,noexec,nosuid,size=16m","-v",f"{WORK}:/work:rw","-w","/work",IMAGE,*p]
    try:
        r=subprocess.run(args,capture_output=True,text=True,timeout=TIMEOUT,cwd=ROOT,env={"PATH":os.getenv("PATH","/usr/bin:/bin")})
        return {"output":(r.stdout+r.stderr)[-12000:] or "(no output)","exit_code":r.returncode}
    except subprocess.TimeoutExpired: raise HTTPException(408,"Command timed out")
    except FileNotFoundError: raise HTTPException(503,"Docker unavailable")
    except Exception: raise HTTPException(500,"Runner failed")
