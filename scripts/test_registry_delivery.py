"""Offline Ansible gate/input tests using disposable dummy credentials only."""
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import yaml
ROOT = Path(__file__).resolve().parents[1]

class RegistryDeliveryTests(unittest.TestCase):
    def run_play(self, path, extra=None):
        with tempfile.TemporaryDirectory() as temp:
            return subprocess.run(['ansible-playbook', '-i', 'localhost,', str(path), *(extra or [])],
                capture_output=True, text=True, env={**os.environ, 'ANSIBLE_LOCAL_TEMP': temp+'/local',
                'ANSIBLE_REMOTE_TEMP':temp+'/remote', 'ANSIBLE_NOCOLOR':'1'})

    def test_default_and_check_mode_do_not_read_files_or_api(self):
        play=ROOT/'ansible/deliver-portal-registry.yaml'
        for args in [[], ['--check'], ['--check','-e','portal_registry_apply=true']]:
            result=self.run_play(play,args)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('changed=0',result.stdout)
            self.assertNotIn('dummy-registry-password',result.stdout)

    def test_real_input_validation_accepts_only_private_ghcr_file(self):
        token=base64.b64encode(b'dummy-user:dummy-registry-password').decode()
        good={'auths':{'ghcr.io':{'auth':token}}}
        cases=[(good,'0600',False,True),(good,'0644',False,False),(good,'0600',True,False),
               ({'auths':{'registry1.dso.mil':{'auth':token}}},'0600',False,False),
               ({'auths':{'ghcr.io':{'auth':token}},'credsStore':'dummy'},'0600',False,False),
               ({'auths':{'ghcr.io':{'auth':'invalid'}}},'0600',False,False),
               ({'auths':{'ghcr.io':{'auth':base64.b64encode(b'user:').decode()}}},'0600',False,False)]
        for data,mode,symlink,expected in cases:
            with self.subTest(mode=mode,symlink=symlink,expected=expected), tempfile.TemporaryDirectory() as temp:
                tmp=Path(temp); credential=tmp/'input.json';credential.write_text(json.dumps(data));credential.chmod(int(mode,8))
                selected=credential
                if symlink:
                    selected=tmp/'link.json';selected.symlink_to(credential)
                play=tmp/'test.yaml';play.write_text(yaml.safe_dump([{'hosts':'localhost','connection':'local','gather_facts':False,
                    'vars':{'portal_registry_file':str(selected)},'tasks':[{'name':'Test dummy inputs only', 'no_log':True,
                    'block':[{'ansible.builtin.include_tasks':str(ROOT/'ansible/portal-registry-input.yaml')}]}]}]))
                result=self.run_play(play)
                self.assertEqual(result.returncode==0,expected,result.stdout+result.stderr)
                self.assertNotIn(token,result.stdout+result.stderr)
                self.assertNotIn('dummy-registry-password',result.stdout+result.stderr)

    def test_delivery_is_scoped_private_stdin_and_requires_release_and_uid(self):
        play=yaml.safe_load((ROOT/'ansible/deliver-portal-registry.yaml').read_text())[0]
        self.assertFalse(play['vars']['portal_registry_apply'])
        gate=play['tasks'][1];self.assertTrue(gate['no_log'])
        self.assertEqual(gate['when'],'portal_registry_apply | bool and not ansible_check_mode')
        tasks=gate['block'];self.assertEqual(tasks[0]['ansible.builtin.include_tasks'],'verify-release.yaml')
        delivery=tasks[-1];command=delivery['ansible.builtin.command']
        self.assertEqual(command['argv'][-2:],['-f','-'])
        manifest=delivery['vars']['portal_registry_manifest']
        self.assertEqual(manifest['metadata'],{'name':'portal-registry-existing','namespace':'tenant-portal'})
        self.assertEqual(manifest['type'],'kubernetes.io/dockerconfigjson')
        self.assertNotIn('auth', ' '.join(command['argv']))
        self.assertIn('expected_cluster_uid', str(tasks[3]))

if __name__=='__main__': unittest.main()
