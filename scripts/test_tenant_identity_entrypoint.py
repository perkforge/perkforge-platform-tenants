"""Offline invocation/status regression; fake adapter never contacts an API."""
import json, os, pathlib, shutil, subprocess, tempfile, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
class EntryPoint(unittest.TestCase):
    def test_pinned_invocation_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            d=pathlib.Path(td); e=d/'enrollment'; p=d/'platform'; private=d/'private'
            for v in (e,p,private): v.mkdir(mode=0o700)
            (e/'ansible').mkdir(); (e/'scripts').mkdir(); (e/'contracts').mkdir()
            for name in ('reconcile-tenant-identity.yaml','verify-release.yaml'):
                shutil.copy(ROOT/'ansible'/name,e/'ansible'/name)
            verify=e/'scripts/verify-release-ref.sh'
            verify.write_text('#!/bin/sh\n[ "$1" = perkforge/perkforge-platform-tenants ] && [ "$2" = v0.0.1 ] && [ ${#3} = 40 ]\n'); verify.chmod(0o700)
            base=p/'big-bang-bootstrap/configuration'; (base/'authorization/contexts').mkdir(parents=True)
            (base/'packages/gitlab/enrollment').mkdir(parents=True)
            (base/'authorization/contexts/portal.yaml').write_text('fixture: canonical-context\n')
            (base/'authorization/contexts/verify.py').write_text('import sys\nassert sys.argv[1].endswith("/portal.yaml")\n')
            launcher=base/'packages/gitlab/enrollment/run-groups.sh'
            launcher.write_text('''#!/usr/bin/env python3
import json,os,pathlib,sys
mode,token,receipt,inputs=sys.argv[1:]
v=json.loads(pathlib.Path(inputs).read_text())
with open(os.environ['FIXTURE_CALLS'],'a') as f: f.write(mode+'\\n')
assert mode in ('--validate','--apply')
if mode=='--apply':
 if os.environ.get('FIXTURE_FAIL')=='1': sys.exit(1)
 pathlib.Path(receipt).write_text(json.dumps({'context':v['gitlab_group_context'],'source_revision':v['gitlab_group_source_revision'],'stage':'group-ready','parent_id':11,'group_id':12}))
'''); launcher.chmod(0o700)
            def commit(repo):
                def git(*args): return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL,text=True).strip()
                if not (repo/'.git').exists(): git('init','-q')
                git('add','.'); git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture')
                return git('rev-parse','HEAD')
            ph=commit(p)
            contract=json.loads((ROOT/'contracts/tenant-identity-v1.json').read_text()); contract['platformRevision']=ph
            (e/'contracts/tenant-identity-v1.json').write_text(json.dumps(contract)); eh=commit(e)
            inputs=private/'inputs.json'; token=private/'token'; receipt=private/'receipt.json'; calls=private/'calls'
            token.write_text('OFFLINE-ONLY'); token.chmod(0o600)
            inp={'gitlab_group_context':'portal','gitlab_group_source_revision':eh,'gitlab_group_scope':'gitlab-enrollment-group-foundation-v1'}
            def run(extra=None,envextra=None,check=False):
                calls.write_text(''); inputs.write_text(json.dumps(inp)); inputs.chmod(0o600)
                values={'tenant_identity_apply':True,'tenant_identity_context':'portal','tenant_identity_platform_checkout':str(p),'tenant_identity_inputs_file':str(inputs),'tenant_identity_token_file':str(token),'tenant_identity_receipt_file':str(receipt),'enrollment_tag':'v0.0.1'}
                values.update(extra or {}); vf=private/'vars.json'; vf.write_text(json.dumps(values)); vf.chmod(0o600)
                r=subprocess.run(['ansible-playbook','-i','localhost,',str(e/'ansible/reconcile-tenant-identity.yaml'),'-e','@'+str(vf)]+(['--check'] if check else []),env={**os.environ,'FIXTURE_CALLS':str(calls),'ANSIBLE_SHOW_CUSTOM_STATS':'true',**(envextra or {})},capture_output=True,text=True,timeout=90)
                self.assertNotIn('OFFLINE-ONLY',r.stdout+r.stderr)
                return r,calls.read_text().splitlines()
            for extra,check in [({'tenant_identity_apply':False},False),({},True)]:
                r,c=run(extra,check=check); self.assertEqual(r.returncode,0,r.stdout+r.stderr); self.assertEqual(c,[])
            r,c=run(); self.assertEqual(r.returncode,0,r.stdout+r.stderr); self.assertEqual(c,['--validate','--apply']); self.assertIn('PendingIdentity',r.stdout); self.assertIn('ReadyGroup',r.stdout)
            inp['gitlab_group_context']='other'; r,c=run(); self.assertNotEqual(r.returncode,0); self.assertEqual(c,['--validate'])
            inp['gitlab_group_context']='portal'; inp['gitlab_group_source_revision']='0'*40; r,c=run(); self.assertNotEqual(r.returncode,0); self.assertEqual(c,['--validate'])
            inp['gitlab_group_source_revision']=eh; r,c=run(envextra={'FIXTURE_FAIL':'1'}); self.assertNotEqual(r.returncode,0); self.assertNotIn('"group": "ReadyGroup"',r.stdout); self.assertIn('PartialFailure',r.stdout)
            (p/'dirty').write_text('drift'); r,c=run(); self.assertNotEqual(r.returncode,0); self.assertEqual(c,[])
            (p/'dirty').unlink(); contract['platformRevision']=None; (e/'contracts/tenant-identity-v1.json').write_text(json.dumps(contract)); inp['gitlab_group_source_revision']=commit(e); r,c=run(); self.assertNotEqual(r.returncode,0); self.assertEqual(c,[])
if __name__=='__main__': unittest.main()
