import copy,json,subprocess,unittest,tempfile,pathlib,yaml
from test_identity_foundation import F
from identity_foundation import build as foundation
from identity_gitops_ownership import build,sha

def sample():
 objects=foundation(F['D'],F['network'],F['custody'])
 selection={'scope':'identity-foundation-gitops-v1','foundationSHA256':sha(objects),'runtimeNamespaces':['tenant-identity-writer','tenant-identity-attestor'],'controlNamespace':'flux-system','platformServiceAccount':'platform-reconciler','sourceName':'platform-config','sourceNamespace':'flux-system','sourcePath':'./generated/identity-foundation','namePrefix':'identity-foundation'}
 return objects,selection
class Ownership(unittest.TestCase):
 def test_default_inert(self):
  r=subprocess.run(['python3','scripts/identity_gitops_ownership.py'],capture_output=True,text=True);self.assertEqual(r.returncode,0);self.assertIn('INERT',r.stdout)
 def test_exact_scope_and_exclusions(self):
  objects,c=sample();p=build(objects,c)
  self.assertEqual(len(p['bootstrapGuards']),4)
  rules=[r for o in p['bootstrapGrants'] for r in o.get('rules',[])]
  self.assertTrue(all('create' not in r['verbs'] and 'delete' not in r['verbs'] and 'secrets' not in r['resources'] for r in rules))
  es=[r for r in rules if 'escalate' in r['verbs']];self.assertEqual(sum(len(r['resourceNames']) for r in es),7)
  self.assertTrue(all('identity-declaration-reconciler' not in r['resourceNames'] for r in es))
  self.assertTrue(all(not any(x.startswith('identity-foundation-owned-') for x in r['resourceNames']) for r in rules))
  kinds=[o['kind'] for files in p['stages'].values() for o in files.values()]
  for kind in ['Secret','PersistentVolumeClaim','Namespace','Pod','Job']:self.assertNotIn(kind,kinds)
  self.assertFalse(p['reconciliations'][0]['spec']['prune']);self.assertFalse(p['reconciliations'][0]['spec']['force'])
  self.assertIn('healthCheckExprs',p['reconciliations'][0]['spec']);self.assertEqual(p['reconciliations'][1]['spec']['dependsOn'],[{'name':'identity-foundation-admission'}])
 def test_stage_kustomize_builds_and_no_existing_root_changes(self):
  objects,c=sample();p=build(objects,c)
  with tempfile.TemporaryDirectory() as tmp:
   for stage,files in p['stages'].items():
    d=pathlib.Path(tmp)/stage;d.mkdir()
    for name,o in files.items():(d/name).write_text(yaml.safe_dump(o))
    r=subprocess.run(['kubectl','kustomize',str(d)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
    self.assertEqual(len(list(yaml.safe_load_all(r.stdout))),len(files)-1)
  self.assertEqual(json.loads(pathlib.Path('declarations/identity/portal.json').read_text()),{'schemaVersion':1,'context':'portal','enabled':False})
 def test_foreign_and_escalating_inputs_denied(self):
  objects,c=sample()
  for mutate in [lambda x:x[0]['metadata'].update(name='foreign'),lambda x:next(o for o in x if o['kind']=='Role')['rules'][0]['verbs'].append('escalate')]:
   bad=copy.deepcopy(objects);mutate(bad)
   with self.assertRaises(ValueError):build(bad,c)
  bad=copy.deepcopy(objects);next(o for o in bad if o['kind']=='Role')['rules'][0]['verbs'].append('escalate');c['foundationSHA256']=sha(bad)
  with self.assertRaises(ValueError):build(bad,c)
 def test_bootstrap_authority_collision_denied(self):
  objects,c=sample();r=next(o for o in objects if o['kind']=='Role');old=r['metadata']['name'];ns=r['metadata']['namespace'];r['metadata']['name']=c['namePrefix']+'-owner'
  b=next(o for o in objects if o['kind']=='RoleBinding' and o['metadata']['namespace']==ns and o['roleRef']['name']==old);b['metadata']['name']=r['metadata']['name'];b['roleRef']['name']=r['metadata']['name']
  c['foundationSHA256']=sha(objects)
  with self.assertRaisesRegex(ValueError,'disjoint'):build(objects,c)
 def test_independent_context_namespace_selection(self):
  objects,c=sample();replacement={'tenant-identity-writer':'sample-identity-writer','tenant-identity-attestor':'sample-identity-attestor'}
  # Rendered object handoff, not a second tenant-name implementation.
  objects=json.loads(json.dumps(objects).replace('tenant-identity-writer','sample-identity-writer').replace('tenant-identity-attestor','sample-identity-attestor'))
  c['runtimeNamespaces']=list(replacement.values());c['namePrefix']='sample-identity';c['foundationSHA256']=sha(objects);p=build(objects,c)
  self.assertEqual({o['metadata']['namespace'] for o in p['bootstrapGrants'] if o['kind']=='Role'},set(c['runtimeNamespaces']+['flux-system']))
  self.assertTrue(all(o['metadata']['name'].startswith('sample-identity-') for o in p['bootstrapGuards']+p['bootstrapGrants']))
if __name__=='__main__':unittest.main()
