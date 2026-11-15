import copy,json,pathlib,sys,unittest
from private_receipts import plan,guard,pending_guard,release_patch,cleanup_proof,BUDGET
class Private(unittest.TestCase):
 def fixture(self):
  i=dict(clusterUID='11111111-1111-4111-8111-111111111111',claim='identity-receipts',claimUID='22222222-2222-4222-8222-222222222222',pv='pvc-example',pvUID='33333333-3333-4333-8333-333333333333',volumeHandle='pvc-example',node='worker-2',pullSecret='private-registry',operatorUser='synthetic-operator')
  c={'metadata':{'uid':i['clusterUID']}};p={'metadata':{'name':i['claim'],'namespace':'tenant-identity-writer','uid':i['claimUID'],'labels':{'platform.perkforge.io/owner':'tenant-identity-foundation-v1'}},'spec':{'volumeName':i['pv'],'storageClassName':'longhorn','accessModes':['ReadWriteOnce'],'resources':{'requests':{'storage':'1Gi'}}},'status':{'phase':'Bound'}};v={'metadata':{'name':i['pv'],'uid':i['pvUID']},'spec':{'claimRef':{'name':i['claim'],'namespace':'tenant-identity-writer','uid':i['claimUID']},'csi':{'driver':'driver.longhorn.io','volumeHandle':i['volumeHandle']},'persistentVolumeReclaimPolicy':'Retain'}}
  return i,c,p,v
 def test_guards(self):
  i,c,p,v=self.fixture();self.assertTrue(guard(i,c,p,v,[]))
  for target in ('cluster','claim','pv'):
   cc,pp,vv=copy.deepcopy((c,p,v));{'cluster':cc,'claim':pp,'pv':vv}[target]['metadata']['uid']='foreign'
   with self.assertRaises(ValueError):guard(i,cc,pp,vv,[])
  pod={'metadata':{'namespace':'tenant-identity-writer'},'spec':{'volumes':[{'persistentVolumeClaim':{'claimName':i['claim']}}]}}
  with self.assertRaises(ValueError):guard(i,c,p,v,[pod])
 def test_plan(self):
  i,*_=self.fixture();o=plan(i);p=o['pod']['spec'];self.assertEqual(p['containers'][0]['resources'],BUDGET);self.assertFalse(p['automountServiceAccountToken']);self.assertEqual(p['activeDeadlineSeconds'],300);self.assertNotIn('secret',str(p['volumes']).lower());self.assertEqual(p['securityContext']['runAsUser'],1001)
 def test_wffc_release_and_cleanup(self):
  i,c,p,v=self.fixture();initial=dict(i,pv=None,pvUID=None,volumeHandle=None);pending=copy.deepcopy(p);pending['status']['phase']='Pending';pending['spec'].pop('volumeName');self.assertTrue(pending_guard(initial,c,pending,[]))
  h=plan(initial);self.assertEqual(plan(i)['pod']['metadata']['name'],h['pod']['metadata']['name'])
  pod=copy.deepcopy(h['pod']);pod['metadata']['uid']='44444444-4444-4444-8444-444444444444';pod['spec']['nodeName']=i['node'];pod['status']={'phase':'Running'}
  gate=copy.deepcopy(h['gate']);gate['metadata'].update(uid='55555555-5555-4555-8555-555555555555',resourceVersion='12')
  r=release_patch(initial,c,p,v,[pod],pod,gate);self.assertEqual(r['boundInputs'],i);self.assertEqual(r['patch'][0]['path'],'/metadata/uid')
  for change in ('foreign-consumer','gate-populated','helper-command','restored-claim'):
   pp,gg,pods,claim=copy.deepcopy((pod,gate,[pod],p))
   if change=='foreign-consumer':q=copy.deepcopy(pod);q['metadata']['uid']='other';pods.append(q)
   elif change=='gate-populated':gg['data']={'approval.json':'old'}
   elif change=='helper-command':pp['spec']['containers'][0]['command']=['false']
   else:claim['spec']['dataSource']={'name':'foreign','kind':'VolumeSnapshot'}
   with self.assertRaises(ValueError):release_patch(initial,c,claim,v,pods,pp,gg)
  lh={'metadata':{'name':i['volumeHandle']},'spec':{'nodeID':''},'status':{'state':'detached'}}
  self.assertTrue(cleanup_proof(i,c,p,v,[],[],lh))
  with self.assertRaises(ValueError):cleanup_proof(i,c,p,v,[],[{'spec':{'source':{'persistentVolumeName':i['pv']}}}],lh)
if __name__=='__main__':unittest.main()
