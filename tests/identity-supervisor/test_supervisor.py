#!/usr/bin/env python3
"""Isolated cached maintained-image supervision/lock regression; no network/providers."""
import json,os,pathlib,subprocess,tempfile,time,shutil
IMAGE='registry1.dso.mil/ironbank/opensource/ansible/ansible@sha256:3308322cc09f20a813c00e9087c166a3d97dbb7789c059f1020f3c0b092fdf02'
PYTHON='/home/python/python-env/bin/python3'
SOURCE=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(tempfile.mkdtemp(prefix='supervisor-fixture-'))
results=[]
def run(name,code=None,expect=0,probe=False,observer=False):
 d=ROOT/name;d.mkdir(mode=0o700);w=d/'tmp';w.mkdir(mode=0o700)
 script=d/'case.py';script.write_text(code or '');script.chmod(0o644)
 cmd=['podman','run','--rm','--pull=never','--network=none','--read-only','--userns=keep-id:uid=1001,gid=1001','--user','1001:1001','--cap-drop=ALL','--security-opt=no-new-privileges','--cpus=0.5','--memory=512m','--pids-limit=64','-e','PYTHONDONTWRITEBYTECODE=1','-v',str(w)+':/tmp:rw','-v',str(script)+':/audit/case.py:ro','-v',str(SOURCE/'guard.py')+':/audit/guard.py:ro','-v',str(SOURCE/'probe.py')+':/audit/probe.py:ro','--entrypoint',PYTHON if observer else '/usr/bin/timeout',IMAGE]
 if observer:cmd += ['/audit/case.py']
 else:cmd += ['--signal=TERM','--kill-after=1s','2s',PYTHON,'/audit/probe.py' if probe else '/audit/case.py']
 start=time.monotonic();p=subprocess.run(cmd,text=True,capture_output=True,timeout=25);elapsed=time.monotonic()-start
 assert p.returncode==expect,(name,p.returncode,p.stdout,p.stderr)
 if probe:
  r=json.loads(p.stdout);assert r['pid']>1 and r['result']=='lock-verified',r
 if observer:assert json.loads(p.stdout)['live_after_kill']==[],p.stdout
 results.append({'case':name,'exit':p.returncode,'seconds':round(elapsed,3),'stdout':p.stdout.strip()})
try:
 run('normal',"import os;print('child_pid',os.getpid());assert os.getpid()>1")
 run('failure','raise SystemExit(23)',expect=23)
 run('term_timeout','import time;time.sleep(30)',expect=124)
 run('native_flock',probe=True)
 run('pid1_resistant_tree',"import os,signal,time\nsignal.signal(signal.SIGTERM,signal.SIG_IGN)\np=os.fork()\nprint('pid',os.getpid(),'child',p,flush=True)\ntime.sleep(30)",expect=137)
 run('group_cleanup_observer',r'''import os,subprocess,time,json
python='/home/python/python-env/bin/python3'
payload="import os,signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);c=os.fork();print(os.getpid(),flush=True);time.sleep(30)"
p=subprocess.Popen(['/usr/bin/timeout','--signal=TERM','--kill-after=1s','2s',python,'-c',payload],stdout=subprocess.PIPE,text=True)
pids=[int(p.stdout.readline()),int(p.stdout.readline())]
rc=p.wait(timeout=10)
assert rc==-9,rc
live=[]
for pid in pids:
 try:
  state=open('/proc/'+str(pid)+'/stat').read().split(') ',1)[1].split()[0]
  if state not in ('Z','X'):live.append([pid,state])
 except FileNotFoundError:pass
assert not live,live
print(json.dumps({'timeout_return':rc,'children':pids,'live_after_kill':live}))
''',observer=True)
 print(json.dumps({'image':IMAGE,'production_equivalent':['timeout','--signal=TERM','--kill-after=10s','270s'],'tests':results},indent=2))
finally:shutil.rmtree(ROOT)
