#!/usr/bin/env python3
"""Deterministic source-only foundation materialization; never talks to Kubernetes."""
import argparse,json,pathlib
import yaml
from finite_identity import unique,render as render_identity
from identity_foundation import build as foundation
from identity_gitops_ownership import build as ownership
from identity_context_binding import selection
ROOT=pathlib.Path(__file__).resolve().parents[1]
EMPTY={'apiVersion':'kustomize.config.k8s.io/v1beta1','kind':'Kustomization','resources':[]}

def render(d,c):
    render_identity(d) # Validate even a disabled context, including its ABI digest.
    if c=={'schemaVersion':1,'enabled':False} and type(c['schemaVersion']) is int:
        return {'kustomization.yaml':EMPTY}, {'enabled':False}
    keys={'schemaVersion','enabled','network','custody','initializer','ownership'}
    if set(c)!=keys or type(c['schemaVersion']) is not int or c['schemaVersion']!=1 or c['enabled'] is not True or d.get('enabled') is not True:
        raise ValueError('explicit enabled foundation and declaration required')
    b=selection(d);s=c['ownership']
    if s.get('runtimeNamespaces')!=[b['writer_namespace'],b['attestor_namespace']] or s.get('controlNamespace')!='flux-system' or s.get('sourceNamespace')!='flux-system' or s.get('sourceName')!=d['sourceName'] or s.get('sourcePath')!='./generated/identity-foundation/portal':
        raise ValueError('foundation must bind the selected context and source')
    objects=foundation(d,c['network'],c['custody'],c['initializer'])
    plan=ownership(objects,s) # Explicit reviewed foundation hash remains mandatory.
    files={stage+'/'+name:o for stage,items in plan['stages'].items() for name,o in items.items()}
    refs=[]
    for o in plan['reconciliations']:
        name=o['metadata']['name']+'.yaml';files[name]=o;refs.append(name)
    files['kustomization.yaml']={**EMPTY,'resources':refs}
    bootstrap={k:plan[k] for k in ('bootstrapGuards','bootstrapGrants','excludedBootstrapObjects','preconditions')}
    bootstrap['foundationSHA256']=s['foundationSHA256']
    return files,bootstrap

def materialize(root,check=False):
    d=json.loads((root/'declarations/identity/portal.json').read_text(),object_pairs_hook=unique)
    c=json.loads((root/'declarations/identity/foundation.json').read_text(),object_pairs_hook=unique)
    files,bootstrap=render(d,c)
    expected={k:yaml.safe_dump(v,sort_keys=False) for k,v in files.items()}
    dest=root/'generated/identity-foundation/portal'
    report=root/'bootstrap/identity-foundation/portal-plan.json'
    text=json.dumps(bootstrap,sort_keys=True,indent=2)+'\n'
    actual={str(p.relative_to(dest)):p.read_text() for p in dest.rglob('*') if p.is_file()}
    if check:
        if actual!=expected or not report.exists() or report.read_text()!=text:
            raise ValueError('stale foundation output; render and review source diff')
        return
    if set(actual)-set(expected):raise ValueError('refusing implicit source cleanup')
    for name,value in expected.items():
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value)
    report.parent.mkdir(parents=True,exist_ok=True);report.write_text(text)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();materialize(ROOT,a.check)
