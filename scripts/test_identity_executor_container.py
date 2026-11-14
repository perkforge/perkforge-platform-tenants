#!/usr/bin/env python3
"""Run ONLY in isolated built fixture image, network=none, synthetic mounts."""
import hashlib,json,os,pathlib,ssl,subprocess,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import unquote,urlsplit
state={'calls':[],'groups':{'tenants':{'id':10,'name':'tenants','path':'tenants','full_path':'tenants','parent_id':None,'visibility':'private','request_access_enabled':False}}}
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def reply(self,n,b):self.send_response(n);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(b).encode())
 def do_GET(self):
  state['calls'].append(('GET',self.path))
  if self.headers.get('PRIVATE-TOKEN')!='SYNTHETIC-GROUP-TOKEN':return self.reply(403,{})
  p=unquote(urlsplit(self.path).path)
  if p=='/api/v4/version':return self.reply(200,{'version':'19.4.2-ee'})
  key=p.removeprefix('/api/v4/groups/');g=next((v for k,v in state['groups'].items() if k==key or str(v['id'])==key),None)
  self.reply(200 if g else 404,g or {})
 def do_POST(self):
  state['calls'].append(('POST',self.path))
  if self.headers.get('PRIVATE-TOKEN')!='SYNTHETIC-GROUP-TOKEN':return self.reply(403,{})
  b=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  assert b['parent_id']==10 and b['path']=='portal' and b['visibility']=='private'
  g=b|{'id':11,'full_path':'tenants/portal'};state['groups']['tenants/portal']=g;self.reply(201,g)
srv=ThreadingHTTPServer(('127.0.0.1',0),Handler);tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.load_cert_chain('/credentials/ca.crt','/fixture/key');srv.socket=tls.wrap_socket(srv.socket,server_side=True);threading.Thread(target=srv.serve_forever,daemon=True).start()
rev=json.loads(pathlib.Path('/opt/revisions.json').read_text())
data={'gitlab_group_run':True,'gitlab_group_scope':'gitlab-enrollment-group-foundation-v1','gitlab_group_context':'portal','gitlab_group_source_revision':rev['enrollment'],'gitlab_group_allow_parent_create':False,'gitlab_group_expected_parent_id':10,'gitlab_native_origin':'https://localhost:'+str(srv.server_port),'gitlab_native_ca_file':'/credentials/ca.crt'}
def run(value,hash_override=None):
 raw=json.dumps(value).encode();pathlib.Path('/inputs/inputs.yaml').write_bytes(raw)
 cmd=['/opt/perkforge/bin/reconcile-identity','--context','portal','--enrollment-revision',rev['enrollment'],'--platform-revision',rev['platform'],'--invocation','f'*64,'--inputs','/inputs/inputs.yaml','--inputs-sha256',hash_override or hashlib.sha256(raw).hexdigest(),'--credentials','/credentials','--receipts','/receipts']
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
 assert 'SYNTHETIC-GROUP-TOKEN' not in p.stdout+p.stderr
 return p
try:
 for invalid in (data|{'group_prior':{}},data|{'gitlab_native_origin':"{{ lookup('pipe','false') }}"}):
  p=run(invalid);assert p.returncode!=0 and not state['calls'],p.stdout+p.stderr
 p=run(data,'0'*64);assert p.returncode!=0 and not state['calls']
 pathlib.Path('/receipts').chmod(0o770)
 p=run(data);assert p.returncode!=0 and not state['calls'],p.stdout+p.stderr
 pathlib.Path('/receipts').chmod(0o700)
 p=run(data);assert p.returncode==0,p.stdout+p.stderr
 receipt=json.loads(pathlib.Path('/receipts/portal/group.json').read_text());assert receipt['stage']=='group-ready' and receipt['group_id']==11
 n=sum(m=='POST' for m,_ in state['calls']);assert n==1
 p=run(data);assert p.returncode==0,p.stdout+p.stderr
 assert sum(m=='POST' for m,_ in state['calls'])==1
 assert not list(pathlib.Path('/tmp').glob('identity.*'))
 print('PASS: exact launcher TLS create, idempotent retry, injection/hash denials, receipt and staging cleanup; no external network.')
finally:srv.shutdown();srv.server_close()
