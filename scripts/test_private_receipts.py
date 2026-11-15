from identity_target_profile import PILOT
import copy,json,pathlib,sys,unittest,hashlib
from unittest.mock import patch
import private_receipts as receipts
from private_receipts import plan,guard,pending_guard,release_patch,cleanup_proof,BUDGET
class Private(unittest.TestCase):
 def fixture(self):
  i=dict(storageProfile=copy.deepcopy(PILOT['storage']),clusterUID='11111111-1111-4111-8111-111111111111',claim='identity-receipts',claimUID='22222222-2222-4222-8222-222222222222',pv='pvc-example',pvUID='33333333-3333-4333-8333-333333333333',volumeHandle='pvc-example',node='worker-2',pullSecret='private-registry',operatorUser='synthetic-operator')
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
 def test_native_empty_args_and_cni_readback(self):
  i,c,p,v=self.fixture();h=plan(i);pod=copy.deepcopy(h['pod']);pod['metadata']['uid']='44444444-4444-4444-8444-444444444444';pod['spec']['nodeName']=i['node'];pod['status']={'phase':'Running','podIP':'192.0.2.5'}
  gate=copy.deepcopy(h['gate']);gate['metadata'].update(uid='55555555-5555-4555-8555-555555555555',resourceVersion='12');gate.pop('data')
  pod['spec']['containers'][0].pop('args')
  self.assertTrue(release_patch(i,c,p,v,[pod],pod,gate))
  pod['metadata']['annotations'].update({'cni.projectcalico.org/containerID':'a'*64,'cni.projectcalico.org/podIP':'192.0.2.5/32','cni.projectcalico.org/podIPs':'192.0.2.5/32'})
  self.assertTrue(release_patch(i,c,p,v,[pod],pod,gate))
  for change in ('nonempty-args','unknown-key','protected-value','partial-cni','bad-id','bad-ip','wrong-ip','multi-ip','subnet','missing-cidr'):
   bad=copy.deepcopy(pod);a=bad['metadata']['annotations']
   if change=='nonempty-args':bad['spec']['containers'][0]['args']=['foreign']
   elif change=='unknown-key':a['cni.projectcalico.org/foreign']='bad'
   elif change=='protected-value':a['platform.perkforge.io/claim-uid']='foreign'
   elif change=='partial-cni':a.pop('cni.projectcalico.org/containerID')
   elif change=='bad-id':a['cni.projectcalico.org/containerID']='bad'
   elif change=='bad-ip':a['cni.projectcalico.org/podIP']='bad';a['cni.projectcalico.org/podIPs']='bad'
   elif change=='wrong-ip':bad['status']['podIP']='192.0.2.6'
   elif change=='multi-ip':a['cni.projectcalico.org/podIPs']+=',192.0.2.6/32'
   elif change=='missing-cidr':a['cni.projectcalico.org/podIP']='192.0.2.5';a['cni.projectcalico.org/podIPs']='192.0.2.5'
   else:a['cni.projectcalico.org/podIP']='192.0.2.5/24';a['cni.projectcalico.org/podIPs']='192.0.2.5/24'
   with self.assertRaises(ValueError):release_patch(i,c,p,v,[bad],bad,gate)
 def test_plan_matches_reviewed_base(self):
  # Canonical complete plan from da1b464; includes script bytes/image/budget/name.
  i,*_=self.fixture();digest=hashlib.sha256(json.dumps(plan(i),sort_keys=True,separators=(',',':')).encode()).hexdigest()
  self.assertEqual(digest,'76dc37c7a6ad20b28c7489e346c8f080bcf762dfd8a7b6bf3e28c2f8bf30a913')
 def test_bounded_running_wait(self):
  i,*_=self.fixture();h=plan(i);uid='44444444-4444-4444-8444-444444444444';pod=copy.deepcopy(h['pod']);pod['metadata']['uid']=uid;pod['status']={'phase':'Pending'};ready=copy.deepcopy(pod);ready['status']['phase']='Running'
  now=[0.0]
  def clock():return now[0]
  def sleep(seconds):now[0]+=seconds
  def running():
   p=receipts.helper_state(i,h,uid);return p if p['status']['phase']=='Running' else None
  with patch.object(receipts.time,'monotonic',side_effect=clock),patch.object(receipts.time,'sleep',side_effect=sleep),patch.object(receipts,'get',side_effect=[pod,ready]):
   self.assertEqual(receipts.wait_for(running,60,180),ready);self.assertEqual(now[0],2)
  for mode in ('Failed','Succeeded','deleted','replaced'):
   bad=copy.deepcopy(pod)
   if mode=='deleted':bad['metadata']['deletionTimestamp']='fixture'
   elif mode=='replaced':bad['metadata']['uid']='foreign'
   else:bad['status']['phase']=mode
   with patch.object(receipts,'get',return_value=bad):
    with self.assertRaises(ValueError):receipts.helper_state(i,h,uid)
  now[0]=179
  with patch.object(receipts.time,'monotonic',side_effect=clock),patch.object(receipts.time,'sleep',side_effect=sleep),patch.object(receipts,'get',return_value=pod):
   with self.assertRaises(ValueError):receipts.wait_for(running,60,180)
   self.assertEqual(now[0],180)
   with self.assertRaises(ValueError):receipts.remaining(180)
  now[0]=179
  def slow():now[0]+=2;return ready
  with patch.object(receipts.time,'monotonic',side_effect=clock):
   with self.assertRaises(ValueError):receipts.wait_for(slow,60,180)
if __name__=='__main__':unittest.main()
