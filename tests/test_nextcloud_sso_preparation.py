import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]

class SsoPreparation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.env = dict(os.environ, ANSIBLE_LOCAL_TEMP=str(self.directory / 'ansible'),
                        ANSIBLE_REMOTE_TEMP=str(self.directory / 'remote'))

    def run_play(self, inputs=None, check=False, success=True):
        args = ['ansible-playbook', str(ROOT / PLAY), '-e', json.dumps(inputs or {})]
        if check:
            args.append('--check')
        result = subprocess.run(args, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def test_default_and_check_do_not_read_inputs_or_write_output(self):
        self.run_play()
        self.run_play({FLAG: True, OUTPUT: str(self.directory / 'check')}, check=True)
        self.assertFalse((self.directory / 'check').exists())

    def test_exact_boundary_render_and_conflict_refusal(self):
        cert, key = self.directory / 'ca.pem', self.directory / 'key.pem'
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                        '-keyout', str(key), '-out', str(cert), '-days', '1',
                        '-subj', '/CN=Offline fixture'], check=True, capture_output=True)
        import hashlib
        output = self.directory / 'boundary'
        inputs = {FLAG: True, OUTPUT: str(output), 'nextcloud_sso_issuer_ipv4': '192.168.100.10',
                  'nextcloud_sso_ca_file': str(cert),
                  'nextcloud_sso_ca_sha256': hashlib.sha256(cert.read_bytes()).hexdigest(),
                  'nextcloud_sso_delivery_contract': True,
                  'nextcloud_sso_image': 'ghcr.io/perkforge/nextcloud-sso:35.0.2-oidc8.13.0@sha256:'+'a'*64}
        self.run_play(inputs)
        policy, ca = list(yaml.safe_load_all((output / 'boundary.yaml').read_text()))
        self.assertEqual(policy['spec']['egress'], [{'to': [{'ipBlock': {'cidr': '192.168.100.10/32'}}],
                                                   'ports': [{'protocol': 'TCP', 'port': 443}]}])
        self.assertEqual(ca['data']['ca.crt'].strip(), cert.read_text().strip())
        policy_contract = yaml.safe_load((output / 'runtime-policy.yaml').read_text())
        self.assertEqual(len(policy_contract['spec']['validations']),3)
        images = next(v['expression'] for v in policy_contract['spec']['variables'] if v['name'] == 'images')
        self.assertEqual(json.loads(images), [inputs['nextcloud_sso_image']])
        active = next(p for p in yaml.safe_load_all((ROOT/'tenants/nextcloud/foundation/runtime-policy.yaml').read_text()) if p['kind']=='ValidatingAdmissionPolicy' and p['metadata']['name']=='nextcloud-app-pod-templates')
        self.assertEqual(policy_contract['spec']['validations'], active['spec']['validations'])
        self.assertIn('m.readOnly',policy_contract['spec']['validations'][2]['expression'])
        self.run_play(inputs, success=False)
        self.run_play(dict(inputs, nextcloud_sso_issuer_ipv4='0.0.0.0'), success=False)
        self.run_play(dict(inputs, nextcloud_sso_issuer_ipv4='192.168.999.1'), success=False)
        self.run_play(dict(inputs, nextcloud_sso_ca_sha256='0'*64), success=False)
        self.run_play(dict(inputs, nextcloud_sso_ca_file=str(key)), success=False)

    def test_source_policy_keeps_shared_volume_and_mount_contract(self):
        policy = next(p for p in yaml.safe_load_all((ROOT/'tenants/nextcloud/foundation/runtime-policy.yaml').read_text())
                      if p['kind']=='ValidatingAdmissionPolicy' and p['metadata']['name']=='nextcloud-app-pod-templates')
        def normalized(value):
            return ' '.join(value.split())
        volume = (ROOT/'tenants/nextcloud/sso/volume-extension.txt').read_text()
        mounts = (ROOT/'tenants/nextcloud/sso/mount-expression.txt').read_text()
        self.assertIn(normalized(volume), normalized(policy['spec']['validations'][1]['expression']))
        self.assertEqual(normalized(mounts), normalized(policy['spec']['validations'][2]['expression']))

    def test_unselected(self):
        resources = yaml.safe_load((ROOT / 'tenants/nextcloud/foundation/kustomization.yaml').read_text())['resources']
        self.assertFalse(any('sso' in x for x in resources))
        self.assertNotIn('nextcloud-oidc-issuer', str(resources))

PLAY = 'tenants/nextcloud/sso/prepare.yaml'
FLAG = 'nextcloud_sso_render'
OUTPUT = 'nextcloud_sso_output'
