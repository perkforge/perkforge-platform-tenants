"""Real Ansible with synthetic credentials and CLI state; never a live cluster."""
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAY = ROOT / 'ansible/deliver-nextcloud-registry.yaml'


class RegistryDelivery(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.private = self.root / 'private'
        self.private.mkdir(mode=0o700)
        self.secret = 'synthetic-read-only-package-token'
        self.auth = base64.b64encode(('fixture-user:' + self.secret).encode()).decode()
        self.config = self.private / 'dockerconfigjson'
        self.config.write_text(json.dumps({'auths': {'ghcr.io': {'auth': self.auth}}}) + '\n')
        self.config.chmod(0o600)
        self.state = self.root / 'state.json'
        self.state.write_text(json.dumps({'objects': {}, 'calls': [], 'writes': [], 'scenario': ''}))
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        stub = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
p=Path(os.environ['REGISTRY_FIXTURE_STATE']);s=json.loads(p.read_text())
a=sys.argv[1:];tool=Path(sys.argv[0]).name;s['calls'].append([tool]+a)
code=0;out='';scenario=s['scenario']
if tool=='git':
 if 'status' in a:out=' M dirty' if scenario=='dirty' else ''
 elif 'rev-parse' in a:out='a'*40
 elif 'ls-remote' in a:out='a'*40+'\trefs/tags/v1.2.3'
 else:code=90
elif tool=='gh':
 out='v1.2.3\tfalse\tfalse' if a[0]=='release' else 'a'*40
 if scenario=='unpublished':code=1
elif tool=='kubectl':
 assert a[:4]==['--kubeconfig','/fixture/kubeconfig','--context','fixture']
 if 'kube-system' in a:out='wrong' if scenario=='wrong-cluster' else 'fixture-cluster'
 elif 'namespace' in a:
  labels={'platform.perkforge.io/nextcloud-runtime':'true','pod-security.kubernetes.io/enforce':'restricted','pod-security.kubernetes.io/enforce-version':'v1.36'}
  if scenario=='wrong-namespace':labels['platform.perkforge.io/nextcloud-runtime']='false'
  out=json.dumps({'metadata':{'labels':labels}})
 elif 'get' in a:
  assert a[4:9]==['-n','tenant-home-nextcloud','get','secret','nextcloud-registry-existing']
  if scenario=='read-error':code=1
  else:out=json.dumps(s['objects']['registry']) if 'registry' in s['objects'] else ''
 elif 'create' in a:
  obj=json.load(sys.stdin)
  assert obj['kind']=='Secret' and obj['metadata']['name']=='nextcloud-registry-existing'
  assert obj['metadata']['namespace']=='tenant-home-nextcloud'
  if '--dry-run=server' in a:
   if scenario=='server-reject':code=1
  elif 'registry' in s['objects']:code=1
  else:
   s['objects']['registry']=obj;s['writes'].append('registry')
   if scenario=='uncertain-create':code=1
   if scenario=='readback-mismatch':s['objects']['registry']['type']='Opaque'
 else:code=91
else:code=92
p.write_text(json.dumps(s));print(out);sys.exit(code)
'''
        for tool in ['git', 'gh', 'kubectl']:
            path = self.bin / tool
            path.write_text(stub)
            path.chmod(0o700)
        self.env = {**os.environ, 'PATH': str(self.bin) + ':' + os.environ['PATH'],
                    'KUBECONFIG': '/dev/null', 'REGISTRY_FIXTURE_STATE': str(self.state),
                    'ANSIBLE_LOCAL_TEMP': str(self.root / 'local'),
                    'ANSIBLE_REMOTE_TEMP': str(self.root / 'remote')}
        self.variables = {
            'nextcloud_registry_apply': True,
            'nextcloud_registry_approval': 'nextcloud-registry-delivery-v1',
            'nextcloud_registry_read_only_confirmed': True,
            'nextcloud_registry_config_file': str(self.config),
            'enrollment_tag': 'v1.2.3', 'target_kubeconfig': '/fixture/kubeconfig',
            'target_context': 'fixture', 'expected_cluster_uid': 'fixture-cluster'}

    def state_value(self):
        return json.loads(self.state.read_text())

    def scenario(self, value):
        state = self.state_value()
        state['scenario'] = value
        self.state.write_text(json.dumps(state))

    def run_play(self, extra=None, check=False, success=True):
        result = subprocess.run(
            ['ansible-playbook', '-i', 'localhost,', str(PLAY), '-e',
             json.dumps({**self.variables, **(extra or {})})] + (['--check'] if check else []),
            env=self.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        for sensitive in [self.secret, self.auth, base64.b64encode(self.config.read_bytes()).decode()
                          if self.config.is_file() else self.secret]:
            self.assertNotIn(sensitive, result.stdout + result.stderr)
            self.assertNotIn(sensitive, json.dumps(self.state_value()['calls']))
        return result

    def test_default_and_check_are_noncontacting_even_with_missing_inputs(self):
        self.config.unlink()
        self.run_play({'nextcloud_registry_apply': False})
        self.run_play(check=True)
        self.assertEqual(self.state_value()['calls'], [])

    def test_missing_approval_and_read_only_confirmation_stop_before_contact(self):
        for extra in [{'nextcloud_registry_approval': 'UNAPPROVED'},
                      {'nextcloud_registry_read_only_confirmed': False}]:
            self.run_play(extra, success=False)
        self.assertEqual(self.state_value()['calls'], [])

    def test_create_validate_readback_and_exact_reuse(self):
        self.run_play()
        state = self.state_value()
        self.assertEqual(state['writes'], ['registry'])
        obj = state['objects']['registry']
        self.assertTrue(obj['immutable'])
        self.assertEqual(obj['type'], 'kubernetes.io/dockerconfigjson')
        self.assertEqual(base64.b64decode(obj['data']['.dockerconfigjson']), self.config.read_bytes())
        creates = [c for c in state['calls'] if c[0] == 'kubectl' and 'create' in c]
        self.assertEqual(len(creates), 2)
        self.assertIn('--dry-run=server', creates[0])
        self.assertIn('changed=0', self.run_play().stdout)
        self.assertEqual(self.state_value()['writes'], ['registry'])

    def test_existing_foreign_mutable_wrong_type_or_mismatch_is_never_adopted(self):
        self.run_play()
        original = self.state_value()
        for field in ['label', 'mutable', 'type', 'data', 'extra-data', 'controller', 'deleting']:
            with self.subTest(field=field):
                state = json.loads(json.dumps(original))
                obj = state['objects']['registry']
                if field == 'label':obj['metadata']['labels'] = {}
                if field == 'mutable':obj['immutable'] = False
                if field == 'controller':obj['metadata']['ownerReferences'] = [{'kind': 'Other', 'name': 'other', 'uid': 'fixture'}]
                if field == 'deleting':obj['metadata']['deletionTimestamp'] = '2026-01-01T00:00:00Z'
                if field == 'type':obj['type'] = 'Opaque'
                if field == 'data':obj['data']['.dockerconfigjson'] = 'different'
                if field == 'extra-data':obj['data']['extra'] = 'different'
                self.state.write_text(json.dumps(state))
                self.run_play(success=False)
                self.assertEqual(self.state_value()['writes'], ['registry'])

    def test_file_mode_parent_mode_symlink_and_missing_refused(self):
        self.config.chmod(0o644)
        self.run_play(success=False)
        self.config.chmod(0o600)
        self.private.chmod(0o755)
        self.run_play(success=False)
        self.private.chmod(0o700)
        alias = self.private / 'link'
        alias.symlink_to(self.config)
        self.run_play({'nextcloud_registry_config_file': str(alias)}, success=False)
        self.run_play({'nextcloud_registry_config_file': str(self.private / 'missing')}, success=False)
        self.assertFalse(any(c[0] == 'kubectl' for c in self.state_value()['calls']))

    def test_malformed_or_multiregistry_configs_refused_before_cluster(self):
        cases = ['not json', [], {}, {'auths': {}},
                 {'auths': {'ghcr.io': {'auth': self.auth}, 'docker.io': {'auth': self.auth}}},
                 {'auths': {'ghcr.io': {'identitytoken': self.secret}}},
                 {'auths': {'ghcr.io': {'auth': 'invalid!'}}},
                 {'auths': {'ghcr.io': {'auth': base64.b64encode(b'fixture-user:token\n').decode()}}},
                 {'auths': {'ghcr.io': {'auth': base64.b64encode(b'no-colon').decode()}}},
                 {'auths': {'ghcr.io': {'auth': self.auth}}, 'credsStore': 'desktop'}]
        for value in cases:
            with self.subTest(shape=type(value).__name__):
                self.config.write_text(json.dumps(value))
                self.run_play(success=False)
        self.assertFalse(any(c[0] == 'kubectl' for c in self.state_value()['calls']))

    def test_release_cluster_namespace_and_server_denials_create_nothing(self):
        for scenario in ['dirty', 'unpublished', 'wrong-cluster', 'wrong-namespace',
                         'read-error', 'server-reject']:
            with self.subTest(scenario=scenario):
                self.scenario(scenario)
                self.run_play(success=False)
                self.assertEqual(self.state_value()['writes'], [])

    def test_uncertain_create_is_not_retried_and_later_repeat_reuses(self):
        self.scenario('uncertain-create')
        self.run_play(success=False)
        self.assertEqual(self.state_value()['writes'], ['registry'])
        self.scenario('')
        self.assertIn('changed=0', self.run_play().stdout)
        self.assertEqual(self.state_value()['writes'], ['registry'])

    def test_post_create_mismatch_fails_without_repair_or_deletion(self):
        self.scenario('readback-mismatch')
        self.run_play(success=False)
        self.assertEqual(self.state_value()['writes'], ['registry'])
        calls = self.state_value()['calls']
        self.assertFalse(any(x in c for c in calls for x in ['delete', 'patch', 'apply', 'replace']))


if __name__ == '__main__':
    unittest.main()
