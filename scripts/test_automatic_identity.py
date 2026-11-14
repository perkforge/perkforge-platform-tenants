#!/usr/bin/env python3
"""Offline render guards; synthetic digests are fixtures, never published images."""
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest
import yaml
ROOT = pathlib.Path(__file__).resolve().parents[1]

class AutomaticIdentity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.tmp.name)
        shutil.copytree(ROOT / 'ansible/automatic-identity', self.base / 'ansible/automatic-identity')
        (self.base / 'contracts').mkdir()
        self.selection = json.loads((ROOT / 'contracts/tenant-identity-v1.json').read_text())
        self.selection['platformRevision'] = 'a' * 40
        self.write_selection()
        self.out = self.base / 'output'
        self.inputs = {'automatic_identity_' + k:v for k,v in {
            'render':True, 'foundation_approved':True, 'output':str(self.out),
            'context':'portal','enrollment_revision':'b'*40,
            'image':'registry.example.test/reviewed/executor@sha256:'+'c'*64,
            'namespace':'tenant-identity','receipt_claim':'identity-receipts',
            'inputs_configmap':'portal-inputs-v1','credentials_secret':'portal-writer-v1',
            'worker_sa':'identity-worker','reconciler_sa':'identity-reconciler',
            'pull_secret':'registry1','source_name':'tenant-enrollments',
            'source_path':'./identity/portal/job','cpu_request':'100m','cpu_limit':'500m',
            'memory_request':'256Mi','memory_limit':'512Mi'}.items()}
    def tearDown(self): self.tmp.cleanup()
    def write_selection(self):
        (self.base / 'contracts/tenant-identity-v1.json').write_text(json.dumps(self.selection))
    def run_render(self, check=False):
        f=self.base/'inputs.json'; f.write_text(json.dumps(self.inputs))
        cmd=['ansible-playbook',str(self.base/'ansible/automatic-identity/render.yaml'),'-e','@'+str(f)]
        if check: cmd.append('--check')
        return subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    def test_defaults_and_check_inert(self):
        self.inputs['automatic_identity_render']=False
        self.assertEqual(self.run_render().returncode,0)
        self.assertFalse(self.out.exists())
        self.inputs['automatic_identity_render']=True
        self.assertEqual(self.run_render(True).returncode,0)
        self.assertFalse(self.out.exists())
    def test_missing_approval_image_and_revision_fail_before_output(self):
        for key,value in [('automatic_identity_foundation_approved',False),('automatic_identity_image','image:latest'),('automatic_identity_enrollment_revision','main'),('automatic_identity_worker_sa',''),('automatic_identity_context','unknown')]:
            with self.subTest(key=key):
                old=self.inputs[key]; self.inputs[key]=value
                self.assertNotEqual(self.run_render().returncode,0)
                self.assertFalse(self.out.exists()); self.inputs[key]=old
        self.selection['platformRevision']=None; self.write_selection()
        self.assertNotEqual(self.run_render().returncode,0); self.assertFalse(self.out.exists())
    def test_native_manifest_and_revision_identity(self):
        r=self.run_render(); self.assertEqual(r.returncode,0,r.stdout)
        job=yaml.safe_load((self.out/'job/job.yaml').read_text())
        spec=job['spec']; pod=spec['template']['spec']
        self.assertEqual(spec['backoffLimit'],0); self.assertNotIn('ttlSecondsAfterFinished',spec)
        self.assertFalse(pod['automountServiceAccountToken']); self.assertEqual(pod['restartPolicy'],'Never')
        self.assertEqual(pod['volumes'][2]['persistentVolumeClaim']['claimName'],'identity-receipts')
        k=yaml.safe_load((self.out/'reconcile.yaml').read_text())['spec']
        self.assertTrue(k['wait']); self.assertFalse(k['force']); self.assertFalse(k['prune'])
        old=job['metadata']['name']; self.assertEqual(self.run_render().returncode,0)
        self.assertEqual(yaml.safe_load((self.out/'job/job.yaml').read_text())['metadata']['name'],old)
        self.inputs['automatic_identity_enrollment_revision']='d'*40
        self.assertEqual(self.run_render().returncode,0)
        self.assertNotEqual(yaml.safe_load((self.out/'job/job.yaml').read_text())['metadata']['name'],old)
        build=subprocess.run(['kubectl','kustomize',str(self.out/'job')],capture_output=True,text=True)
        self.assertEqual(build.returncode,0,build.stderr)
    def test_existing_roots_unselected(self):
        for path in (ROOT/'clusters').rglob('*.yaml'):
            self.assertNotIn('automatic-identity',path.read_text())

if __name__ == '__main__': unittest.main()
