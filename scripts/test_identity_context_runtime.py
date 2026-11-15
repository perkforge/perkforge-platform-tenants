import contextlib,copy,io,pathlib,runpy,unittest,tempfile,subprocess
from finite_identity import render
from identity_foundation import build
from private_receipts import plan,guard
from identity_context_binding import derive
from identity_context_fixture import alternate
from test_private_receipts import Private
with contextlib.redirect_stdout(io.StringIO()):F=runpy.run_path(str(pathlib.Path(__file__).with_name('identity_foundation_cases.py')))
class Contexts(unittest.TestCase):
 def fixture(self):return alternate(F['D'],F['I'],F['custody'])
 def test_names_and_credential_boundaries(self):
  d,i,c=self.fixture();b=derive('atlas');g=render(d);o=build(d,F['network'],c,i)
  self.assertEqual(g['receipt-intent.yaml']['metadata']['namespace'],b['writer_namespace']);self.assertEqual(g['receipt-intent.yaml']['metadata']['name'],b['evidence_name'])
  for phase in ('foundation','memberships','attest'):
   pod=g[phase+'/job.yaml']['spec']['template']['spec'];ns=b['attestor_namespace'] if phase=='attest' else b['writer_namespace']
   self.assertEqual(g[phase+'/job.yaml']['metadata']['namespace'],ns)
   self.assertEqual([v['secret']['secretName'] for v in pod['volumes'] if 'secret' in v],[d['attestorSecret'] if phase=='attest' else d['writerSecret']])
  self.assertEqual(plan(i)['pod']['metadata']['namespace'],b['writer_namespace'])
  stores=[x for x in o if x['kind']=='SecretStore'];self.assertEqual({x['metadata']['name'] for x in stores},{b['writer_eso_role'],b['reader_eso_role'],b['eso_role']})
  self.assertFalse(any(x['metadata'].get('namespace') in ('tenant-identity-writer','tenant-identity-attestor') for x in o))
  self.assertTrue({b['declaration_policy'],b['evidence_policy']} <= {x['metadata']['name'] for x in o if x['kind']=='ValidatingAdmissionPolicy'})
 def test_cross_context_fail_closed(self):
  for mutation in ('digest','input-digest','receipt-namespace','receipt-name','source-namespace','initializer','custody'):
   d,i,c=self.fixture()
   if mutation=='digest':d['contextDigest']=derive('portal')['digest']
   if mutation=='input-digest':d['phaseInputs']['attest']['identity']['identity_context_digest']=derive('portal')['digest']
   if mutation=='receipt-namespace':d['phaseInputs']['attest']['identity']['identity_receipt_namespace']='tenant-identity-writer'
   if mutation=='receipt-name':d['phaseInputs']['attest']['identity']['identity_receipt_name']='portal-identity-evidence'
   if mutation=='source-namespace':d['sourceBundle']['configMaps'][0]['metadata']['namespace']='tenant-identity-writer'
   if mutation=='initializer':i.pop('context');i.pop('contextDigest')
   if mutation=='custody':c['keycloak']['record']='identity/keycloak/portal-membership-reader-v1'
   with self.assertRaises(ValueError,msg=mutation):build(d,F['network'],c,i)
 def test_missing_abi_and_unknown_overrides(self):
  d,i,c=self.fixture();d.pop('contextDigest')
  with self.assertRaises(ValueError):render(d)
  d,i,c=self.fixture();d['writerNamespace']='foreign'
  with self.assertRaises(ValueError):render(d)
 def test_pinned_bundle_selects_canonical_context(self):
  from identity_source_bundle import bundle,PLATFORM,PREFIX,EXECUTOR
  from identity_context_binding import CONTRACT_BYTES
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);en=root/'en';pf=root/'pf'
   for repo in (en,pf):
    repo.mkdir();subprocess.run(['git','init','-q',str(repo)],check=True)
   for f in EXECUTOR:
    p=en/'executor'/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('synthetic executor\n')
   for f in PLATFORM:
    p=pf/PREFIX/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('synthetic adapter\n')
   p=pf/PREFIX/'enrollment/identity_context.py';p.write_bytes(CONTRACT_BYTES)
   p=pf/'big-bang-bootstrap/configuration/authorization/contexts/atlas.yaml';p.parent.mkdir(parents=True);p.write_text('context: atlas\n')
   revs=[]
   for repo in (en,pf):
    subprocess.run(['git','-C',str(repo),'add','.'],check=True)
    subprocess.run(['git','-C',str(repo),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','synthetic fixture'],check=True)
    revs.append(subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip())
   b=bundle(en,revs[0],pf,revs[1],'atlas');self.assertEqual([c['metadata']['namespace'] for c in b['configMaps']],['tenant-identity-atlas-writer','tenant-identity-atlas-attestor'])
   self.assertTrue(any(x['path'].endswith('/contexts/atlas.yaml') for x in b['items']));self.assertFalse(any(x['path'].endswith('/contexts/portal.yaml') for x in b['items']))
   with self.assertRaises((ValueError,IndexError,subprocess.CalledProcessError)):bundle(en,revs[0],pf,revs[1],'foreign')
 def test_foreign_claim_namespace(self):
  i,cluster,pvc,pv=Private().fixture();b=derive('atlas');i.update(context='atlas',contextDigest=b['digest'])
  with self.assertRaises(ValueError):guard(i,cluster,pvc,pv,[])
  pvc['metadata']['namespace']=b['writer_namespace'];pv['spec']['claimRef']['namespace']=b['writer_namespace'];self.assertTrue(guard(i,cluster,pvc,pv,[]))
if __name__=='__main__':unittest.main()
