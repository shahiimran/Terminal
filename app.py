import os, re, shlex, subprocess, uuid, hmac
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT=Path(__file__).resolve().parent
WORK=Path(os.getenv("SPIDER_WORKSPACE","./workspace")).resolve()
TOKEN=os.getenv("SPIDER_API_TOKEN","")
IMAGE=os.getenv("SPIDER_RUNNER_IMAGE","spider-shell-runner:2.0")
TIMEOUT=min(max(int(os.getenv("SPIDER_TIMEOUT_SECONDS","10")),1),20)
MAX_UPLOAD=5*1024*1024
MAX_TEXT=512*1024
if len(TOKEN)<24: raise RuntimeError("Set SPIDER_API_TOKEN (minimum 24 characters).")
WORK.mkdir(parents=True,exist_ok=True)
app=FastAPI(title="SPIDER SHELL",version="2.0.0")
app.mount("/static",StaticFiles(directory=ROOT/"static"),name="static")
ALLOW={"pwd","ls","echo","cat","mkdir","touch","python","python3","node","bash","whoami","date","git"}
NAME=re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
class Command(BaseModel):
    command:str=Field(min_length=1,max_length=500)
class TextFile(BaseModel):
    name:str=Field(min_length=1,max_length=100)
    content:str=Field(max_length=MAX_TEXT)
def auth(value):
    if not value or not hmac.compare_digest(value,"Bearer "+TOKEN):
        raise HTTPException(401,"Unauthorized")
def safe_file(name):
    if not NAME.fullmatch(name) or name in {".",".."} or name.startswith("."):
        raise HTTPException(400,"Use a simple visible file name.")
    p=WORK/name
    if p.is_symlink(): raise HTTPException(400,"Symlinks are not accepted.")
    return p
def parse(raw):
    try: p=shlex.split(raw)
    except ValueError: raise HTTPException(400,"Invalid syntax")
    if not p: raise HTTPException(400,"Empty command")
    if p==["help"]: return p
    if p[0] not in ALLOW: raise HTTPException(400,"Command not enabled. Type help.")
    if len(p)>12: raise HTTPException(400,"Too many arguments")
    for a in p[1:]:
        if a.startswith("-") or "/" in a or "\\" in a or not NAME.fullmatch(a):
            raise HTTPException(400,"Only simple workspace file names are supported")
    if p[0] in {"python","python3"} and (len(p)!=2 or not p[1].endswith(".py")):
        raise HTTPException(400,"Usage: python main.py")
    if p[0]=="node" and (len(p)!=2 or not p[1].endswith(".js")):
        raise HTTPException(400,"Usage: node app.js")
    if p[0]=="bash" and (len(p)!=2 or not p[1].endswith(".sh")):
        raise HTTPException(400,"Usage: bash task.sh")
    if p[0]=="git" and (len(p)<2 or p[1] not in {"status","log","diff","init"}):
        raise HTTPException(400,"Allowed Git commands: status, log, diff, init")
    return p
@app.get("/")
def home(): return FileResponse(ROOT/"static/index.html")
@app.get("/health")
def health(): return {"status":"ok","name":"SPIDER SHELL","version":"2.0.0"}
@app.post("/api/run")
def run(body:Command,authorization:str|None=Header(default=None)):
    auth(authorization); p=parse(body.command)
    if p==["help"]:
        return {"output":"Commands: pwd ls echo cat mkdir touch python main.py node app.js bash task.sh git status|log|diff|init whoami date","exit_code":0}
    args=["docker","run","--rm","--name","spider-"+uuid.uuid4().hex[:12],"--network","none","--read-only","--cap-drop","ALL","--security-opt","no-new-privileges:true","--pids-limit","64","--memory","256m","--cpus","0.75","--user","10001:10001","--tmpfs","/tmp:rw,noexec,nosuid,size=24m","-v",f"{WORK}:/work:rw","-w","/work",IMAGE,*p]
    try:
        r=subprocess.run(args,capture_output=True,text=True,timeout=TIMEOUT,cwd=ROOT,env={"PATH":"/usr/local/bin:/usr/bin:/bin","HOME":"/tmp"})
        return {"output":(r.stdout+r.stderr)[-16000:] or "(no output)","exit_code":r.returncode}
    except subprocess.TimeoutExpired: raise HTTPException(408,"Command timed out")
    except FileNotFoundError: raise HTTPException(503,"Docker unavailable")
    except Exception: raise HTTPException(500,"Runner failed")
@app.get("/api/files")
def files(authorization:str|None=Header(default=None)):
    auth(authorization)
    return {"files":[{"name":p.name,"size":p.stat().st_size} for p in sorted(WORK.iterdir()) if p.is_file() and not p.is_symlink() and not p.name.startswith(".")][:300]}
@app.get("/api/file/{name}")
def read_file(name:str,authorization:str|None=Header(default=None)):
    auth(authorization); p=safe_file(name)
    if not p.is_file(): raise HTTPException(404,"File not found")
    if p.stat().st_size>MAX_TEXT: raise HTTPException(413,"File too large for editor")
    try: content=p.read_text(encoding="utf-8")
    except UnicodeDecodeError: raise HTTPException(415,"Binary file cannot be edited")
    return {"name":p.name,"content":content}
@app.put("/api/file")
def save_file(body:TextFile,authorization:str|None=Header(default=None)):
    auth(authorization); p=safe_file(body.name); p.write_text(body.content,encoding="utf-8")
    return {"saved":p.name,"size":p.stat().st_size}
@app.delete("/api/file/{name}")
def delete_file(name:str,authorization:str|None=Header(default=None)):
    auth(authorization); p=safe_file(name)
    if not p.is_file(): raise HTTPException(404,"File not found")
    p.unlink(); return {"deleted":name}
@app.post("/api/upload")
async def upload(file:UploadFile=File(...),authorization:str|None=Header(default=None)):
    auth(authorization); p=safe_file(Path(file.filename or "").name); data=await file.read(MAX_UPLOAD+1)
    if len(data)>MAX_UPLOAD: raise HTTPException(413,"Maximum upload size is 5 MB")
    p.write_bytes(data); return {"uploaded":p.name,"size":len(data)}
@app.get("/api/download/{name}")
def download(name:str,authorization:str|None=Header(default=None)):
    auth(authorization); p=safe_file(name)
    if not p.is_file(): raise HTTPException(404,"File not found")
    return FileResponse(p,filename=p.name)
