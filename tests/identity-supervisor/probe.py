import sys,os,tempfile,pathlib,subprocess,fcntl,json,stat
sys.path.insert(0,"/audit");import guard
os.umask(0o077);w=pathlib.Path(tempfile.mkdtemp(dir="/tmp"));t=w/"token";t.write_text("synthetic-not-a-provider-token");receipt=w/"receipt"
s=os.stat("/tmp");result={"pid":os.getpid(),"tmpOwner":s.st_uid,"tmpGroup":s.st_gid,"tmpMode":oct(stat.S_IMODE(s.st_mode))}
try:guard.verify(str(t),str(receipt),prepare=True)
except Exception:result["result"]="ancestor-denied";print(json.dumps(result));sys.exit(0)
f=os.open(str(receipt)+".lock",os.O_RDWR);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);os.environ["PERKFORGE_GROUP_LOCK_OWNER"]=str(os.getpid())
p=subprocess.run([sys.executable,"/audit/guard.py","--token",str(t),"--receipt",str(receipt),"--require-locked"],capture_output=True)
result["result"]="lock-verified" if p.returncode==0 else "lock-denied";print(json.dumps(result))
