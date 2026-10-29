"""TEST ONLY: real Ansible task files against a disposable loopback HTTPS API."""
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import ssl
import subprocess
import tempfile
import threading
import unittest
from urllib.parse import urlsplit, parse_qs
import yaml


class PortalIdentityAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=localhost',
                        '-addext','subjectAltName=DNS:localhost','-keyout',str(self.work/'key.pem'),'-out',str(self.work/'ca.pem')],
                       check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.state = {'client': None, 'role': None, 'mappings': {}, 'writes': [], 'requests': 0}
        state = self.state
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def reply(self,code,body=None):
                data=json.dumps(body).encode() if body is not None else b''
                self.send_response(code);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(data)
            def do_GET(self):
                state['requests']+=1; path=urlsplit(self.path).path
                if path.endswith('/clients'): return self.reply(200,[state['client']] if state['client'] else [])
                if path.endswith('/client-secret'): return self.reply(200,{'value':state['client']['secret']})
                if path.endswith('/groups'): return self.reply(200,[{'id':'platform-id','path':'/platform'}])
                if path.endswith('/groups/platform-id/children'): return self.reply(200,[{'id':'admins-id','path':'/platform/admins'}])
                if path.endswith('/roles/tenant-reader'): return self.reply(200 if state['role'] else 404,state['role'])
                if '/scope-mappings/' in path or '/role-mappings/' in path: return self.reply(200,state['mappings'].get(path,[]))
                return self.reply(404)
            def do_POST(self):
                state['requests']+=1; path=urlsplit(self.path).path;raw=self.rfile.read(int(self.headers.get('Content-Length','0')))
                if path.endswith('/protocol/openid-connect/token'):
                    values=parse_qs(raw.decode())
                    if values.get('password')!=['synthetic-bootstrap-secret']: return self.reply(401)
                    return self.reply(200,{'access_token':'synthetic-admin-session'})
                body=json.loads(raw);state['writes'].append((path,deepcopy(body)))
                if path.endswith('/clients'):
                    state['client']={**body,'id':'portal-client-id'}
                    state['client']['attributes'].update({'backchannel.logout.session.required':'true','backchannel.logout.revoke.offline.tokens':'false','realm_client':'false'})
                    for mapper in state['client']['protocolMappers']:mapper['config'].setdefault('userinfo.token.claim','false')
                    for i,m in enumerate(state['client']['protocolMappers']):m['id']=str(i)
                    return self.reply(201)
                if path.endswith('/clients/portal-client-id/roles'):
                    state['role']={**body,'id':'reader-id','clientRole':True,'composite':False,'containerId':'portal-client-id'}
                    return self.reply(201)
                if '/scope-mappings/' in path or '/role-mappings/' in path:
                    state['mappings'][path]=body;return self.reply(204)
                return self.reply(404)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.load_cert_chain(self.work/'ca.pem',self.work/'key.pem')
        server.socket=tls.wrap_socket(server.socket,server_side=True)
        self.thread=threading.Thread(target=server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        self.repo=Path(__file__).resolve().parents[1]
        (self.work/'ansible').mkdir();(self.work/'tenants').symlink_to(self.repo/'tenants',target_is_directory=True)
        for name in ['bootstrap-password','client-secret']:
            p=self.work/name;p.write_text('synthetic-bootstrap-secret' if name=='bootstrap-password' else 'synthetic-portal-secret');p.chmod(0o600)
        url=f'https://localhost:{server.server_port}/auth'
        # Only the fixture wrapper supplies the loopback URL. Production endpoint
        # assertions and release gates are tested separately; never relaxed there.
        wrapper=[{'name':'isolated synthetic client tasks','hosts':'localhost','connection':'local','gather_facts':False,
                  'vars':{'identity_url':url,'portal_api':url+'/admin/realms/perkforge','identity_private_dir':str(self.work),'portal_private_dir':str(self.work)},
                  'module_defaults':{'ansible.builtin.uri':{'validate_certs':True,'ca_path':str(self.work/'ca.pem'),'follow_redirects':'none','use_proxy':False,'use_netrc':False}},
                  'tasks':[{'name':'private fixture tasks','no_log':True,'block':[
                    {'ansible.builtin.include_tasks':str(self.repo/'ansible'/name)}
                    for name in ['portal-identity-inputs.yaml','portal-identity-client.yaml','portal-identity-role.yaml']]}]}]
        (self.work/'ansible/test.yaml').write_text(yaml.safe_dump(wrapper,sort_keys=False))

    def run_play(self):
        result=subprocess.run(['ansible-playbook','-i','localhost,',str(self.work/'ansible/test.yaml')],capture_output=True,text=True,timeout=60,
            env={**os.environ,'ANSIBLE_LOCAL_TEMP':str(self.work/'local'),'ANSIBLE_REMOTE_TEMP':str(self.work/'remote')})
        for marker in ['synthetic-bootstrap-secret','synthetic-portal-secret','synthetic-admin-session']:
            self.assertNotIn(marker,result.stdout+result.stderr)
        return result

    def test_create_idempotent_mapping_and_refuse_unowned_or_drifted_client(self):
        first=self.run_play();self.assertEqual(first.returncode,0,first.stdout+first.stderr)
        writes=deepcopy(self.state['writes']);self.assertEqual(len(writes),4)
        self.assertTrue(all('/users' not in path and '/members' not in path for path,_ in writes))
        self.assertEqual([p for p,_ in writes if '/groups/' in p],['/auth/admin/realms/perkforge/groups/admins-id/role-mappings/clients/portal-client-id'])
        second=self.run_play();self.assertEqual(second.returncode,0,second.stdout+second.stderr)
        self.assertEqual(self.state['writes'],writes);self.assertIn('changed=0',second.stdout)
        self.state['client']['attributes']={}
        refused=self.run_play();self.assertNotEqual(refused.returncode,0);self.assertEqual(self.state['writes'],writes)
        self.state['client']['attributes']={'perkforge-managed-by':'platform-tenants/local-portal'}
        refused=self.run_play();self.assertNotEqual(refused.returncode,0);self.assertEqual(self.state['writes'],writes)

    def test_remaining_role_and_mapping_guards_reject_drift_without_writes(self):
        first=self.run_play();self.assertEqual(first.returncode,0,first.stdout+first.stderr)
        writes=deepcopy(self.state['writes']);role=deepcopy(self.state['role'])
        for field,value in [('clientRole',False),('composite',True),('containerId','wrong-client-id')]:
            self.state['role']=deepcopy(role);self.state['role'][field]=value
            result=self.run_play();self.assertNotEqual(result.returncode,0);self.assertEqual(self.state['writes'],writes)
        self.state['role']=deepcopy(role)
        mappings=deepcopy(self.state['mappings'])
        for path in mappings:
            self.state['mappings']=deepcopy(mappings);self.state['mappings'][path].append({'name':'unexpected-role'})
            result=self.run_play();self.assertNotEqual(result.returncode,0);self.assertEqual(self.state['writes'],writes)

    def test_exposed_input_refused_before_any_authentication(self):
        (self.work/'client-secret').chmod(0o644)
        result=self.run_play();self.assertNotEqual(result.returncode,0);self.assertEqual(self.state['requests'],0)

if __name__ == '__main__':
    unittest.main()
