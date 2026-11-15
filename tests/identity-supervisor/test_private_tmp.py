#!/usr/bin/env python3
"""Local cached-image init/main volume simulation; not a kubelet proof."""
import argparse,importlib.util,json,os,pathlib,subprocess,sys,tempfile
p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=pathlib.Path);a=p.parse_args()
sys.path.insert(0,str(a.source/'scripts'));import finite_identity as f
from identity_kubelet_preflight import CHECK
root=pathlib.Path(tempfile.mkdtemp(prefix='private-tmp-native-'));results=[]
base=['podman','run','--rm','--pull=never','--network=none','--read-only','--user','1001:1001','--cap-drop=ALL','--security-opt=no-new-privileges','--cpus=.5','--memory=512m']
def invoke(mount,command,args):
 return subprocess.run(base+['-v',str(mount)+':/work:rw','--entrypoint',command,f.IMAGE]+args,text=True,capture_output=True,timeout=30)
try:
 for case in ('success','foreign-file','existing-child','symlink','wrong-root-mode'):
  d=root/case;d.mkdir();os.chmod(d,0o2777)
  subprocess.run(['podman','unshare','chgrp','1001',str(d)],check=True)
  if case=='foreign-file':(d/'keep').write_text('keep')
  if case=='existing-child':(d/'private').mkdir(mode=0o700)
  if case=='symlink':(d/'private').symlink_to('/tmp')
  if case=='wrong-root-mode':os.chmod(d,0o777)
  r=invoke(d,'/home/python/python-env/bin/python3',['-c',f.TMP_INIT])
  assert (r.returncode==0)==(case=='success'),(case,r.returncode,r.stderr)
  if case=='foreign-file':assert (d/'keep').read_text()=='keep'
  if case=='symlink':assert (d/'private').is_symlink()
  if case=='success':
   verify="import os,stat; s=os.stat('/work/private'); assert (s.st_uid,s.st_gid,stat.S_IMODE(s.st_mode))==(1001,1001,448); assert not os.listdir('/work/private');print('private0700')"
   q=invoke(d,'/home/python/python-env/bin/python3',['-c',verify]);assert q.returncode==0,q.stderr
   main=subprocess.run(base+['-v',str(d/'private')+':/tmp:rw','--entrypoint',f.SUPERVISOR[0],f.IMAGE]+f.SUPERVISOR[1:-2]+['/home/python/python-env/bin/python3','-c',CHECK],text=True,capture_output=True,timeout=30)
   assert main.returncode==0 and main.stdout.strip()=='PrivateTemporaryWorkspaceVerified',(main.returncode,main.stderr)
   repeated=invoke(d,'/home/python/python-env/bin/python3',['-c',f.TMP_INIT]);assert repeated.returncode!=0
  results.append({'case':case,'exit':r.returncode})
 print(json.dumps({'result':'PASS','scope':'exact same-image UID1001 initializer with root2777 group1001 bind; no kubelet lifecycle claim','cases':results}))
finally:
 subprocess.run(['podman','unshare','rm','-rf','--',str(root)],check=True)
