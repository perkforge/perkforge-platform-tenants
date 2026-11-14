"""Offline physical Portal source gates; no Kubernetes API or real credentials."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]

class PortalPhysical(unittest.TestCase):
    def run_play(self, path, inputs=None, check=False, success=True):
        args = ['ansible-playbook', '-i', 'localhost,', str(ROOT/path), '-e', json.dumps(inputs or {})]
        if check: args.append('--check')
        result = subprocess.run(args, text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def test_default_and_check_gates(self):
        for path, flag in [('tenants/portal/sso/prepare.yaml','portal_sso_render'),
                           ('ansible/configure-portal-identity.yaml','portal_identity_apply'),
                           ('ansible/prepare-local-portal.yaml','portal_foundation_apply'),
                           ('ansible/deliver-portal-inputs.yaml','portal_inputs_apply')]:
            self.run_play(path)
            self.run_play(path, {flag: True}, check=True)
        self.run_play('ansible/configure-portal-identity.yaml',
                      {'identity_url': 'https://unexpected.invalid/auth'}, success=False)

    def test_admin_identity_policy_is_explicit_and_default_off(self):
        self.run_play('ansible/configure-portal-identity.yaml', {'portal_identity_access_policy':'platform-admins'})
        self.run_play('ansible/configure-portal-identity.yaml', {'portal_identity_access_policy':'typo'}, success=False)
        admin=yaml.safe_load((ROOT/'tenants/portal/identity/client-platform-admins.yaml').read_text())
        legacy=yaml.safe_load((ROOT/'tenants/portal/identity/client.yaml').read_text())
        legacy['protocolMappers']=[m for m in legacy['protocolMappers'] if m['name']!='portal-api-role']
        self.assertEqual(admin,legacy)
        play=yaml.safe_load((ROOT/'ansible/configure-portal-identity.yaml').read_text())[0]
        self.assertEqual(play['vars']['portal_identity_access_policy'],'platform-admins')
        role=play['tasks'][-1]['block'][-1]
        self.assertEqual(role['when'],"portal_identity_access_policy == 'tenant-reader'")

    def test_review_output_and_invalid_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); cert=root/'ca.pem'; key=root/'key.pem'
            subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1',
                            '-subj','/CN=Offline only','-keyout',str(key),'-out',str(cert)],
                           check=True, capture_output=True)
            output=root/'review'
            args={'portal_sso_render':True, 'portal_sso_output':str(output),
                  'portal_sso_issuer_ipv4':'192.168.100.10', 'portal_sso_ca_file':str(cert),
                  'portal_sso_ca_sha256':hashlib.sha256(cert.read_bytes()).hexdigest()}
            path='tenants/portal/sso/prepare.yaml'
            self.run_play(path,args)
            policy,ca=list(yaml.safe_load_all((output/'boundary.yaml').read_text()))
            self.assertEqual(policy['metadata']['namespace'],'tenant-portal')
            app=json.loads((ROOT/'scripts/fixtures/portal-v2.0.0-deployment.json').read_text())
            labels=app['spec']['template']['metadata']['labels']
            for key,value in policy['spec']['podSelector']['matchLabels'].items():
                self.assertEqual(labels[key],value)
            self.assertEqual(policy['spec']['podSelector'],{'matchLabels':{'app.kubernetes.io/name':'perkforge-portal'}})
            self.assertEqual(policy['spec']['egress'],[{'to':[{'ipBlock':{'cidr':'192.168.100.10/32'}}], 'ports':[{'protocol':'TCP','port':443}]}])
            self.assertEqual(ca['metadata']['name'],'portal-identity-ca')
            self.assertEqual(ca['data']['ca.crt'],cert.read_text().strip())
            self.run_play(path,args,success=False)
            for change in [{'portal_sso_issuer_ipv4':'0.0.0.0'}, {'portal_sso_issuer_ipv4':'192.168.999.1'}, {'portal_sso_issuer_ipv4':'192.168.001.1'},
                           {'portal_sso_ca_sha256':'0'*64},{'portal_sso_ca_file':str(key)}]:
                self.run_play(path,{**args,'portal_sso_output':str(root/'invalid'),**change},success=False)
                self.assertFalse((root/'invalid').exists())

    def test_source_contract(self):
        policy=next(yaml.safe_load_all((ROOT/'tenants/portal/foundation/deployment-policy.yaml').read_text()))
        expr=' '.join(v['expression'] for v in policy['spec']['validations'])
        for required in ['storage.perkforge.io/worker', 'node-role.kubernetes.io/control-plane',
                         'node-role.kubernetes.io/master', 'DoesNotExist', 'platform-admins',
                         'https://portal.perkforge.home.arpa', 'https://keycloak.perkforge.home.arpa/auth/realms/perkforge',
                         "quantity('25m')", "quantity('64Mi')", "quantity('250m')", "quantity('192Mi')"]:
            self.assertIn(required,expr)
        self.assertNotIn('cks-worker',expr)
        self.assertNotIn('ipBlock',(ROOT/'tenants/portal/foundation/network.yaml').read_text())
        for cluster in ['local','dev']:
            objects=yaml.safe_load_all(subprocess.check_output(['kubectl','kustomize',str(ROOT/'clusters'/cluster)],text=True))
            for obj in objects: self.assertTrue(obj['spec']['suspend'])
        client=yaml.safe_load((ROOT/'tenants/portal/identity/client.yaml').read_text())
        self.assertEqual(client['redirectUris'],['https://portal.perkforge.home.arpa/auth/callback'])
        self.assertEqual(client['webOrigins'],['https://portal.perkforge.home.arpa'])
        self.assertFalse(client['fullScopeAllowed'])
        self.assertFalse(client['directAccessGrantsEnabled'])
        binding=list(yaml.safe_load_all((ROOT/'tenants/portal/foundation/enrollment-rbac.yaml').read_text()))[1]
        self.assertEqual(binding['subjects'],[{'kind':'ServiceAccount','name':'tenant-enrollment-admin','namespace':'flux-system'}])

if __name__=='__main__': unittest.main()
