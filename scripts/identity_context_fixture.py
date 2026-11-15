"""Synthetic alternate-context fixtures only; never writes a deployment declaration."""
import copy,hashlib
from identity_context_binding import derive,CONTRACT_BYTES

def alternate(d,i,custody,context='atlas'):
 d,i,custody=copy.deepcopy((d,i,custody));b=derive(context)
 d.update(context=context,contextDigest=b['digest']);i.update(context=context,contextDigest=b['digest'])
 for body in d['phaseInputs'].values():
  body['identity'].update(identity_context=context,identity_context_digest=b['digest'],identity_receipt_namespace=b['writer_namespace'],identity_receipt_name=b['evidence_name'])
 if 'group' in d['phaseInputs']['foundation']:d['phaseInputs']['foundation']['group']['gitlab_group_context']=context
 custody['keycloak']['record']=b['record']
 old=d['sourceBundle'];paths={item['path']:old['configMaps'][0]['data'][item['key']] for item in old['items'] if item['path']!='provenance.sha256'}
 paths['platform/big-bang-bootstrap/configuration/packages/gitlab/enrollment/identity_context.py']=CONTRACT_BYTES.decode()
 oldcontext='platform/big-bang-bootstrap/configuration/authorization/contexts/portal.yaml'
 if oldcontext in paths:paths['platform/big-bang-bootstrap/configuration/authorization/contexts/'+context+'.yaml']=paths.pop(oldcontext).replace('portal',context)
 manifest=''.join(hashlib.sha256(v.encode()).hexdigest()+'  '+k+'\n' for k,v in sorted(paths.items()));sha=hashlib.sha256(manifest.encode()).hexdigest();paths['provenance.sha256']=manifest
 items=[{'key':'file-'+str(n),'path':p} for n,p in enumerate(sorted(paths))];name='identity-source-'+sha[:20];data={item['key']:paths[item['path']] for item in items}
 bundle={'sha256':sha,'items':items,'configMaps':[{'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':name,'namespace':ns},'immutable':True,'data':data} for ns in (b['writer_namespace'],b['attestor_namespace'])]}
 d.update(sourceBundle=bundle,sourceItems=items,sourceBundleSHA256=sha,sourceBundleName=name)
 return d,i,custody
