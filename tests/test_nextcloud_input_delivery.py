"""Exercise real gates/TLS with synthetic credentials and a fake API; no cluster access."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PLAY=ROOT/'ansible/deliver-nextcloud-inputs.yaml'


class InputDelivery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.cert=Path(cls.tmp.name)
        def openssl(*args):subprocess.run(['openssl',*args],cwd=cls.cert,check=True,capture_output=True)
        openssl('req','-x509','-newkey','rsa:2048','-nodes','-days','3','-keyout','ca.key','-out','ca.crt','-subj','/CN=Synthetic CA')
        for name,host in [('tls','nextcloud.perkforge.home.arpa'),('wrong','wrong.invalid')]:
            openssl('req','-newkey','rsa:2048','-nodes','-keyout',name+'.key','-out',name+'.csr','-subj','/CN='+host)
            (cls.cert/'extensions').write_text('subjectAltName=DNS:'+host+'\nextendedKeyUsage=serverAuth\nbasicConstraints=critical,CA:FALSE\n')
            openssl('x509','-req','-in',name+'.csr','-CA','ca.crt','-CAkey','ca.key','-CAcreateserial','-days','2','-out',name+'.crt','-extfile','extensions')
        openssl('x509','-req','-in','tls.csr','-CA','ca.crt','-CAkey','ca.key','-CAcreateserial','-days','2','-out','cn-only.crt')

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def run_play(self,extra,environment=None):
        with tempfile.TemporaryDirectory() as d:
            return subprocess.run(['ansible-playbook','-i','localhost,',str(PLAY),*extra],text=True,capture_output=True,
                env={**os.environ,'KUBECONFIG':'/dev/null','ANSIBLE_LOCAL_TEMP':d+'/local','ANSIBLE_REMOTE_TEMP':d+'/remote',**(environment or {})})

    def test_default_and_check_modes_touch_no_api_or_private_file(self):
        for args in [[],['--check'],['--check','-e','nextcloud_inputs_apply=true']]:
            result=self.run_play(args)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('changed=0',result.stdout)

    def test_real_delivery_and_denials_never_print_or_overwrite_credentials(self):
        for scenario in ['valid','wrong-host','missing-san','wrong-key','bundled-signing-key','key-in-certificate','public-password','existing','wrong-cluster','server-reject']:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as d:
                p=Path(d);private=p/'inputs';private.mkdir(mode=0o700)
                for name,value in {'admin-username':b'owner-admin','admin-password':b'synthetic-admin-password-123456','db-password':b'synthetic-db-password-123456',
                                   'tls.crt':(self.cert/({'wrong-host':'wrong.crt','missing-san':'cn-only.crt'}.get(scenario,'tls.crt'))).read_bytes(),
                                   'tls.key':(self.cert/('ca.key' if scenario=='wrong-key' else 'tls.key')).read_bytes()}.items():
                    f=private/name;f.write_bytes(value);f.chmod(0o600)
                if scenario=='public-password':(private/'admin-password').chmod(0o644)
                if scenario=='bundled-signing-key':
                    (private/'tls.key').write_bytes((private/'tls.key').read_bytes()+(self.cert/'ca.key').read_bytes())
                if scenario=='key-in-certificate':
                    (private/'tls.crt').write_bytes((private/'tls.crt').read_bytes()+(self.cert/'ca.key').read_bytes())
                tools=p/'bin';tools.mkdir()
                fake=r'''#!/usr/bin/env python3
import base64,json,os,sys,yaml
from pathlib import Path
a=sys.argv[1:];tool=Path(sys.argv[0]).name
if tool=='git':
 if 'status' in a:pass
 elif 'rev-parse' in a:print('a'*40)
 elif 'ls-remote' in a:print('a'*40+'\trefs/tags/v1.2.3')
 else:sys.exit(90)
elif tool=='gh':
 print('v1.2.3\tfalse\tfalse' if a[0]=='release' else 'a'*40)
else:
 if 'kube-system' in a:print('wrong' if os.environ['SCENARIO']=='wrong-cluster' else 'synthetic-cluster')
 elif 'namespace' in a:print(json.dumps({'metadata':{'labels':{'platform.perkforge.io/nextcloud-runtime':'true','pod-security.kubernetes.io/enforce':'restricted','pod-security.kubernetes.io/enforce-version':'v1.36'}}}))
 elif 'get' in a:print('secret/nextcloud-admin' if os.environ['SCENARIO']=='existing' else '')
 elif 'create' in a:
  obj=yaml.safe_load(sys.stdin.read());name=obj['metadata']['name']
  assert obj['kind']=='Secret' and obj['metadata']['namespace']=='tenant-home-nextcloud'
  assert name in ['nextcloud-admin','nextcloud-db-app','nextcloud-tls']
  if name=='nextcloud-admin':assert base64.b64decode(obj['data']['password'])==b'synthetic-admin-password-123456'
  if name=='nextcloud-db-app':assert base64.b64decode(obj['data']['username'])==b'nextcloud'
  mode='dry-run' if '--dry-run=server' in a else 'create'
  with open(os.environ['CALLS'],'a') as f:f.write(mode+':'+name+'\n')
  if os.environ['SCENARIO']=='server-reject' and name=='nextcloud-db-app':sys.exit(1)
  print('validated' if mode=='dry-run' else 'created')
 else:sys.exit(91)
'''
                for name in ['git','gh','kubectl']:
                    f=tools/name;f.write_text(fake);f.chmod(0o755)
                variables={'nextcloud_inputs_apply':True,'enrollment_tag':'v1.2.3','nextcloud_private_dir':str(private),
                           'nextcloud_ingress_ca_file':str(self.cert/'ca.crt'),'target_kubeconfig':'/synthetic/kubeconfig',
                           'target_context':'synthetic','expected_cluster_uid':'synthetic-cluster'}
                log=p/'calls'
                result=self.run_play(['-e',json.dumps(variables)],{'PATH':str(tools)+':'+os.environ['PATH'],'SCENARIO':scenario,'CALLS':str(log)})
                self.assertEqual(result.returncode==0,scenario=='valid',result.stdout+result.stderr)
                output=result.stdout+result.stderr
                self.assertNotIn('synthetic-admin-password-123456',output)
                self.assertNotIn('synthetic-db-password-123456',output)
                self.assertNotIn('BEGIN PRIVATE KEY',output)
                calls=log.read_text().splitlines() if log.exists() else []
                creates=[x for x in calls if x.startswith('create:')]
                if scenario=='valid':
                    self.assertEqual(len(calls),6)
                    self.assertEqual(len(creates),3)
                    self.assertTrue(all(x.startswith('dry-run:') for x in calls[:3]))
                else:self.assertEqual(creates,[])


if __name__=='__main__':unittest.main()
