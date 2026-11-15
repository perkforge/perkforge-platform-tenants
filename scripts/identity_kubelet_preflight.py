"""Exact offline-only credential-free kubelet proof. Never creates or deletes Pods."""
import copy
from finite_identity import render,digest,RUNTIME_PROFILE,SUPERVISOR
from identity_context_binding import selection
from private_receipts import validate,namespace
CHECK="""import os,stat
s=os.lstat('/tmp')
if os.getuid()!=1001 or os.getgid()!=1001 or not stat.S_ISDIR(s.st_mode) or s.st_uid!=1001 or s.st_gid!=1001 or stat.S_IMODE(s.st_mode)!=0o700 or os.listdir('/tmp'):
 raise SystemExit('PrivateTemporaryWorkspaceUnverified')
if os.getpid()<=1:
 raise SystemExit('MissingSupervisor')
print('PrivateTemporaryWorkspaceVerified',flush=True)
"""
def build(d,initializer):
 validate(initializer);binding=selection(d)
 if d.get('runtimeProfile')!=RUNTIME_PROFILE:raise ValueError('explicit corrected runtime profile required')
 if namespace(initializer)!=binding['writer_namespace'] or initializer['node']!=d['workerNode'] or initializer['pullSecret']!=d['pullSecret']:raise ValueError('preflight target mismatch')
 source=render(d)['foundation/job.yaml'];pod=copy.deepcopy(source['spec']['template']['spec'])
 pod['volumes']=[v for v in pod['volumes'] if v['name']=='tmp']
 main=pod['containers'][0];main['name']='verify-private-tmp';main['volumeMounts']=[m for m in main['volumeMounts'] if m['name']=='tmp'];main['command']=SUPERVISOR[:-2]+['/home/python/python-env/bin/python3','-c',CHECK];main['args']=[]
 pod['activeDeadlineSeconds']=300
 proof=digest({'clusterUID':initializer['clusterUID'],'operatorUser':initializer['operatorUser'],'context':binding['digest'],'spec':pod})
 return {'apiVersion':'v1','kind':'Pod','metadata':{'name':binding['phase_prefix'][:36]+'-preflight-'+proof[:16],'namespace':binding['writer_namespace'],'labels':{'platform.perkforge.io/owner':'tenant-identity-preflight-v1'},'annotations':{'platform.perkforge.io/preflight-sha256':proof}},'spec':pod}
