#!/usr/bin/env python3
"""Explicit isolated cached-image fixture; synthetic provider APIs only, no deployment."""
import pathlib,tempfile,subprocess,sys,json,shutil,os,argparse
parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true');parser.add_argument('--platform',type=pathlib.Path);parser.add_argument('--output',type=pathlib.Path);parser.add_argument('--supervised-source',type=pathlib.Path);parser.add_argument('--atomic-writer',action='store_true');args=parser.parse_args()
if not args.run:print('INERT: explicit --run required; cached image only.');raise SystemExit(0)
if not args.platform or not args.output:raise SystemExit('Explicit platform checkout and fresh output directory required.')
R=pathlib.Path(__file__).resolve().parents[1];P=args.platform;sys.path.insert(0,str(R/'scripts'));from identity_source_bundle import bundle,PLATFORM,PREFIX,source
rev='a8862222d1da8f1247ea865b137a0dc5a5e820ab';er=subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD'],text=True).strip();root=args.output.resolve();root.mkdir(mode=0o700,exist_ok=False);pf=root/'platform-fixture';pf.mkdir()
for path in [PREFIX+x for x in PLATFORM]+[PREFIX+'enrollment/identity_context.py']:
 f=pf/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(source(P,rev,path))
canonical='big-bang-bootstrap/configuration/authorization/contexts/portal.yaml';f=pf/canonical.replace('portal.yaml','atlas.yaml');f.parent.mkdir(parents=True);f.write_bytes(source(P,rev,canonical).replace(b'portal',b'atlas'))
subprocess.run(['git','init','-q',str(pf)],check=True);subprocess.run(['git','-C',str(pf),'add','.'],check=True);subprocess.run(['git','-C',str(pf),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','synthetic atlas canonical policy plus exact reviewed adapters'],check=True);pr=subprocess.check_output(['git','-C',str(pf),'rev-parse','HEAD'],text=True).strip();b=bundle(R,er,pf,pr,'atlas')
for n in ('opt','fixture','credentials','api','inputs','evidence','receipts'):(root/n).mkdir(mode=0o700)
if args.atomic_writer:
 from atomic_writer_fixture import publish
 publish(root/'opt',{item['path']:b['configMaps'][0]['data'][item['key']] for item in b['items']})
else:
 for item in b['items']:
  f=root/'opt'/item['path'];f.parent.mkdir(parents=True,exist_ok=True);f.write_text(b['configMaps'][0]['data'][item['key']]);f.chmod(0o755)
subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-keyout',str(root/'fixture/key'),'-out',str(root/'fixture/ca.crt'),'-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
if args.atomic_writer:publish(root/'api',{'token':'OFFLINE-API','ca.crt':(root/'fixture/ca.crt').read_bytes()})
else:
 (root/'api/token').write_text('OFFLINE-API');shutil.copyfile(root/'fixture/ca.crt',root/'api/ca.crt')
t=(R/'scripts/test_native_finite_container.py').read_text().replace('tenant-identity-writer','tenant-identity-atlas-writer').replace('portal','atlas')
t=t.replace("d['identity_invocation']=invocation(d)","import sys;sys.path.insert(0,'/opt/platform/big-bang-bootstrap/configuration/packages/gitlab/enrollment');from identity_context import derive\nd['identity_context_digest']=derive('atlas')['digest']\nd['identity_invocation']=invocation(d)")
if args.atomic_writer:
 def replace_once(text,old,new):
  if text.count(old)!=1:raise ValueError('AtomicWriter fixture seam drift')
  return text.replace(old,new)
 helper=(R/'scripts/atomic_writer_fixture.py').read_text()
 t=helper+'\n'+t
 t=replace_once(t," for f in P('/credentials').iterdir():f.unlink()",'')
 t=replace_once(t," for n,b in creds.items():(P('/credentials')/n).write_text(b)\n (P('/credentials')/'lab-ca.crt').write_bytes(P('/fixture/ca.crt').read_bytes())", " publish('/credentials',dict(creds,**{'lab-ca.crt':P('/fixture/ca.crt').read_bytes()}))")
 t=replace_once(t,"P('/inputs/inputs.json').write_bytes(raw)","publish('/inputs',{'inputs.json':raw})")
 t=replace_once(t,"P('/identity-evidence/receipt.json').write_text(state['data']['receipt.json'])","publish('/identity-evidence',{'receipt.json':state['data']['receipt.json']})")
if args.supervised_source:
 spec=__import__('importlib.util',fromlist=['']).spec_from_file_location('runtime_profile',args.supervised_source/'scripts/finite_identity.py');runtime=__import__('importlib.util',fromlist=['']).module_from_spec(spec);spec.loader.exec_module(runtime)
 needle="cmd=['bash','/opt/perkforge/bin/launch',"
 assert t.count(needle)==1,'exact launcher fixture seam required'
 t=t.replace(needle,'cmd='+repr(runtime.SUPERVISOR)+'+[')
 (root/'private-tmp').mkdir(mode=0o700)
(root/'fixture/test.py').write_text(t);(root/'fixture/test.py').chmod(0o755)
(root/'fixture-meta.json').write_text(json.dumps({'runtimeSource':er,'canonicalABI':rev,'syntheticPlatformCommit':pr,'bundleSHA':b['sha256'],'scope':'synthetic atlas canonical policy, actual reviewed adapter and launcher code'},indent=2))
cmd=['podman','run','--pull=never','--rm','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--userns=keep-id:uid=1001,gid=1001','--user=1001:1001','--cpus=0.5','--memory=512m','--tmpfs','/tmp:rw,size=134217728,mode=1777']
if args.supervised_source:
 cmd=cmd[:-2];cmd+=['-v',str(root/'private-tmp')+':/tmp:rw']
for local,remote,mode in [('opt','/opt','ro'),('fixture','/fixture','ro'),('credentials','/credentials','rw'),('api','/identity-api','rw'),('inputs','/inputs','rw'),('evidence','/identity-evidence','rw'),('receipts','/receipts','rw')]:cmd+=['-v',str(root/local)+':'+remote+':'+mode]
cmd+=['--entrypoint','/home/python/python-env/bin/python3','registry1.dso.mil/ironbank/opensource/ansible/ansible@sha256:3308322cc09f20a813c00e9087c166a3d97dbb7789c059f1020f3c0b092fdf02','/fixture/test.py']
print('Synthetic fixture path',root,flush=True);p=subprocess.run(cmd,capture_output=True,text=True,timeout=300);(root/'result.txt').write_text(p.stdout+p.stderr);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)
