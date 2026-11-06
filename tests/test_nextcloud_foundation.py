"""Offline boundary and renderer tests; synthetic addresses, no Kubernetes API."""
import os
import json
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class NextcloudFoundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.objects = list(yaml.safe_load_all(subprocess.check_output(['kubectl', 'kustomize', str(ROOT/'tenants/nextcloud/foundation')], text=True)))

    def test_unselected_paused_candidate(self):
        for cluster in ['local','dev']:
            built = subprocess.check_output(['kubectl','kustomize',str(ROOT/'clusters'/cluster)],text=True)
            self.assertNotIn('nextcloud',built)
        selected = list(yaml.safe_load_all(subprocess.check_output(['kubectl','kustomize',str(ROOT/'tenants/nextcloud')],text=True)))
        self.assertTrue(all(x['spec']['suspend'] for x in selected))
        source = next(x for x in selected if x['kind']=='GitRepository')
        self.assertEqual(source['spec']['ref'],{'tag':'UNCONFIGURED'})

    def test_scoped_authority_and_storage(self):
        self.assertFalse(any(x['kind'] in {'ClusterRole','ClusterRoleBinding','AuthenticationConfiguration'} for x in self.objects))
        for x in self.objects:
            if x['kind']=='Role':
                if x['metadata']['name']=='platform-cnpg-databases':
                    self.assertEqual(x['metadata']['namespace'],'tenant-home-nextcloud')
                    self.assertEqual(hashlib.sha256(json.dumps(x['rules'],sort_keys=True).encode()).hexdigest(),'2d012e57b53caf7e0fbc55b66bd5cb3c1e65a2992cb3ae14076b8152c0d33499')
                    continue
                for rule in x['rules']:
                    self.assertNotIn('*',str(rule))
                    self.assertFalse(set(rule['resources']) & {'namespaces','roles','rolebindings','networkpolicies','serviceaccounts'})
                    if 'secrets' in rule['resources']:
                        self.assertEqual(x['metadata']['namespace'],'tenant-home-nextcloud-release')
                    if set(rule['resources']) & {'clusters','persistentvolumeclaims'}:
                        self.assertNotIn('delete',rule['verbs'])
        budget = next(x for x in self.objects if x['kind']=='ResourceQuota' and x['metadata']['name']=='nextcloud-budget')
        self.assertEqual(budget['spec']['hard']['requests.storage'],'48Gi')
        self.assertEqual(budget['spec']['hard']['persistentvolumeclaims'],'2')
        for x in self.objects:
            if x['kind']=='ServiceAccount':self.assertFalse(x['automountServiceAccountToken'])

    def test_operator_authority_is_only_the_existing_platform_identity(self):
        owned=[x for x in self.objects if x['metadata']['name']=='platform-cnpg-databases']
        self.assertEqual({x['kind'] for x in owned},{'Role','RoleBinding'})
        self.assertTrue(all(x['metadata']['namespace']=='tenant-home-nextcloud' for x in owned))
        binding=next(x for x in owned if x['kind']=='RoleBinding')
        self.assertEqual(binding['subjects'],[{'kind':'ServiceAccount','name':'platform-cnpg','namespace':'cnpg-system'}])
        self.assertEqual(binding['roleRef'],{'apiGroup':'rbac.authorization.k8s.io','kind':'Role','name':'platform-cnpg-databases'})
        self.assertFalse(any(x['kind']=='RoleBinding' and any(v.get('name') in ['nextcloud-deployer','nextcloud-reconciler'] for v in x.get('subjects',[])) and x['roleRef']['name']=='platform-cnpg-databases' for x in self.objects))

    def test_nextcloud_only_root_selects_published_web_stage_without_portal(self):
        built=subprocess.check_output(['kubectl','kustomize',str(ROOT/'clusters/local-nextcloud')],text=True)
        selected=list(yaml.safe_load_all(built))
        self.assertNotIn('portal',built)
        self.assertEqual({x['kind'] for x in selected},{'GitRepository','HelmRepository','Kustomization'})
        self.assertTrue(all(not x['spec']['suspend'] for x in selected))
        source=next(x for x in selected if x['kind']=='GitRepository')
        evidence=json.loads((ROOT/'release-evidence.json').read_text())['dependencies']['nextcloud']
        self.assertEqual(source['spec']['ref'],{'tag':evidence['tag']})
        self.assertEqual(source['spec']['url'],'https://github.com/'+evidence['repository']+'.git')
        app=os.environ.get('NEXTCLOUD_APP_CHECKOUT')
        if app:
            head=subprocess.check_output(['git','-C',app,'rev-parse','HEAD'],text=True).strip()
            self.assertEqual(head,evidence['resolvedCommit'])
            releases=list(yaml.safe_load_all((Path(app)/'gitops/base/releases.yaml').read_text()))
            self.assertEqual({r['metadata']['name']:r['spec']['suspend'] for r in releases},{'nextcloud-data':False,'nextcloud':False})
            values=yaml.safe_load((Path(app)/'gitops/base/app-values.yaml').read_text())
            self.assertTrue(values['cronjob']['enabled'])
            self.assertEqual(values['cronjob']['type'], 'sidecar')
        self.assertNotIn('secretRef',source['spec'])
        child=next(x for x in selected if x['kind']=='Kustomization')
        self.assertEqual(child['spec']['path'],'./gitops/clusters/local')
        self.assertEqual(child['spec']['targetNamespace'],'tenant-home-nextcloud-config')
        self.assertFalse(child['spec']['prune'])

    def test_no_default_api_or_internet_egress(self):
        policies=[x for x in self.objects if x['kind']=='NetworkPolicy']
        self.assertTrue(any(x['metadata']['name']=='default-deny' and not x['spec'].get('ingress') and not x['spec'].get('egress') for x in policies))
        for x in policies:
            self.assertNotIn('ipBlock',str(x))
            self.assertNotIn('port: 443',yaml.safe_dump(x))

    def test_api_renderer_is_bounded_offline_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)/'api.yaml'
            def run(cidrs,check=False):
                args=['ansible-playbook','-i','localhost,',str(ROOT/'ansible/render-nextcloud-api-policy.yaml'),'-e',json.dumps({'nextcloud_api_reviewed':True,'nextcloud_api_cidrs':cidrs,'nextcloud_api_output':str(dest)})]
                if check:args+=['--check']
                return subprocess.run(args,env={**os.environ,'KUBECONFIG':'/dev/null'},capture_output=True,text=True)
            self.assertEqual(run(['203.0.113.10/32'],True).returncode,0)
            self.assertFalse(dest.exists())
            self.assertNotEqual(run(['0.0.0.0/0']).returncode,0)
            self.assertNotEqual(run(['999.0.0.1/32']).returncode,0)
            self.assertEqual(run(['203.0.113.10/32']).returncode,0)
            result=yaml.safe_load(dest.read_text())
            self.assertEqual(result['spec']['podSelector']['matchLabels'],{'cnpg.io/cluster':'nextcloud-db'})
            before=dest.read_bytes()
            self.assertNotEqual(run(['203.0.113.11/32']).returncode,0)
            self.assertEqual(dest.read_bytes(),before)


if __name__=='__main__': unittest.main()
