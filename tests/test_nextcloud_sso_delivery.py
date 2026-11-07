"""Actual Ansible delivery against a synthetic kubectl, with no API access."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class SsoDelivery(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.d=Path(self.tmp.name)
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=Fixture',
                        '-keyout',str(self.d/'key'),'-out',str(self.d/'ca')],check=True,capture_output=True)
        (self.d/'secret').write_text('fixture-existing-client-secret');(self.d/'secret').chmod(0o600)
        self.state=self.d/'state';self.state.write_text(json.dumps({'objects':{},'calls':[],'writes':[]}))
        script=self.d/'kubectl';script.write_text('''#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
p=Path(os.environ['DELIVERY_FIXTURE_STATE']);s=json.loads(p.read_text());a=sys.argv[1:];s['calls'].append(a)
if 'jsonpath={.metadata.uid}' in a:out='cluster-id'
elif 'namespace' in a:out=json.dumps({'metadata':{'labels':{'platform.perkforge.io/nextcloud-runtime':'true','pod-security.kubernetes.io/enforce':'restricted'}}})
elif 'get' in a:
 i=a.index('get');key=a[i+1]+'/'+a[i+2];out=json.dumps(s['objects'][key]) if key in s['objects'] else ''
elif 'create' in a:
 obj=json.load(sys.stdin);key=obj['kind']+'/'+obj['metadata']['name'];s['objects'][key]=obj;s['writes'].append(key);out='created'
else:raise RuntimeError('unknown fixture command')
p.write_text(json.dumps(s));print(out)
''');script.chmod(0o700)
        self.env=dict(os.environ,PATH=str(self.d)+':'+os.environ['PATH'],DELIVERY_FIXTURE_STATE=str(self.state),
                      ANSIBLE_LOCAL_TEMP=str(self.d/'local'),ANSIBLE_REMOTE_TEMP=str(self.d/'remote'))
        self.v={'nextcloud_sso_deliver':True,'nextcloud_sso_delivery_approval':'nextcloud-sso-delivery-v1',
                'nextcloud_sso_secret_file':str(self.d/'secret'),'nextcloud_sso_ca_file':str(self.d/'ca'),
                'nextcloud_sso_ca_sha256':hashlib.sha256((self.d/'ca').read_bytes()).hexdigest(),
                'target_kubeconfig':'/fixture/config','target_context':'fixture','expected_cluster_uid':'cluster-id'}
    def run_play(self,extra=None,check=False,success=True):
        result=subprocess.run(['ansible-playbook',str(ROOT/'tenants/nextcloud/sso/deliver.yaml'),'-e',json.dumps({**self.v,**(extra or {})})]+(['--check'] if check else []),env=self.env,capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode==0,success,result.stdout+result.stderr)
        self.assertNotIn('fixture-existing-client-secret',result.stdout+result.stderr)
        return result
    def test_default_check_no_api_and_missing_approval(self):
        self.run_play({'nextcloud_sso_deliver':False});self.run_play(check=True)
        self.run_play({'nextcloud_sso_delivery_approval':'UNAPPROVED'},success=False)
        self.assertEqual(json.loads(self.state.read_text())['calls'],[])
    def test_delivery_reuse_and_foreign_credential_refusal(self):
        self.run_play();s=json.loads(self.state.read_text())
        self.assertEqual(s['writes'],['Secret/nextcloud-oidc','ConfigMap/nextcloud-oidc-ca'])
        self.assertTrue(s['objects']['Secret/nextcloud-oidc']['immutable'])
        self.assertIn('changed=0',self.run_play().stdout)
        (self.d/'secret').write_text('different-private-fixture-value')
        self.run_play(success=False)
        self.assertEqual(json.loads(self.state.read_text())['writes'],s['writes'])
