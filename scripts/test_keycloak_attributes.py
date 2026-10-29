"""Run the real Ansible drift assertions with synthetic client responses only."""
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import yaml
ROOT=Path(__file__).resolve().parents[1]
SERVER={'backchannel.logout.session.required':'true','backchannel.logout.revoke.offline.tokens':'false','realm_client':'false'}

class KeycloakAttributeTests(unittest.TestCase):
    def test_actual_ansible_drift_checks_accept_only_reviewed_normalization(self):
        tasks=yaml.safe_load((ROOT/'ansible/portal-identity-client.yaml').read_text())
        selected=[t for t in tasks if t['name'] in ['Reject drift instead of silently rewriting an existing client','Require exact managed attributes and reject unknown server additions',"Validate each recognized server attribute's exact string value"]]
        self.assertEqual(len(selected),3)
        desired={'clientId':'portal-local','fullScopeAllowed':False,'redirectUris':['https://portal-local-il2.local-lab.test/auth/callback'],
                 'attributes':{'perkforge-managed-by':'platform-tenants/local-portal','pkce.code.challenge.method':'S256','access.token.lifespan':'300'}}
        normalized=deepcopy(desired);normalized['attributes'].update(SERVER)
        cases=[('original response',deepcopy(desired),True),('Keycloak defaults',deepcopy(normalized),True)]
        for key in SERVER:
            bad=deepcopy(normalized);bad['attributes'][key]='false' if SERVER[key]=='true' else 'true';cases.append(('wrong '+key,bad,False))
            bad=deepcopy(normalized);bad['attributes'][key]=SERVER[key]=='true';cases.append(('boolean '+key,bad,False))
        for name,mutate in [('unknown',lambda c:c['attributes'].update({'unexpected':'true'})),
                            ('missing managed',lambda c:c['attributes'].pop('pkce.code.challenge.method')),
                            ('managed drift',lambda c:c['attributes'].update({'pkce.code.challenge.method':'plain'})),
                            ('full scope',lambda c:c.update(fullScopeAllowed=True)),
                            ('redirect',lambda c:c.update(redirectUris=['https://wrong.invalid']))]:
            bad=deepcopy(normalized);mutate(bad);cases.append((name,bad,False))
        for name,actual,allowed in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                play=Path(directory)/'test.yaml'
                play.write_text(yaml.safe_dump([{'hosts':'localhost','connection':'local','gather_facts':False,
                    'vars':{'portal_client':actual,'portal_desired':desired},'tasks':[{'name':'Synthetic drift checks','no_log':True,'block':selected}]}]))
                result=subprocess.run(['ansible-playbook','-i','localhost,',str(play)],capture_output=True,text=True,
                    env={**os.environ,'ANSIBLE_LOCAL_TEMP':directory+'/local','ANSIBLE_REMOTE_TEMP':directory+'/remote'},timeout=30)
                self.assertEqual(result.returncode==0,allowed,result.stdout+result.stderr)
        self.assertEqual(len(cases),13)

    def test_real_mapper_assertions_accept_actual_shape_and_reject_drift(self):
        tasks=yaml.safe_load((ROOT/'ansible/portal-identity-client.yaml').read_text())
        selected=[t for t in tasks if t['name'] in ['Verify exact mapper names before checking their claims', 'Verify each mapper definition while allowing only server UUID fields']]
        self.assertEqual(len(selected),2)
        desired=yaml.safe_load((ROOT/'tenants/portal/identity/client.yaml').read_text())
        expected=desired['protocolMappers']
        for mapper in expected:
            self.assertEqual(mapper['config']['userinfo.token.claim'],'false')
        actual=yaml.safe_load((ROOT/'scripts/fixtures/keycloak26.8-portal-mappers.yaml').read_text())
        cases=[('actual Keycloak shape',actual,True)]
        for name in ['portal-audience','portal-api-role']:
            for badvalue in ['true',False]:
                bad=deepcopy(actual);next(m for m in bad if m['name']==name)['config']['userinfo.token.claim']=badvalue
                cases.append((name+' wrong userinfo '+str(badvalue),bad,False))
        for label,change in [('unknown config',lambda m:m['config'].update({'unknown.claim':'false'})),
                             ('changed audience',lambda m:m['config'].update({'included.client.audience':'headlamp-local'})),
                             ('unknown field',lambda m:m.update(unexpected=False))]:
            bad=deepcopy(actual);change(next(m for m in bad if m['name']=='portal-audience'));cases.append((label,bad,False))
        bad=deepcopy(actual);bad.pop();cases.append(('missing mapper',bad,False))
        self.assertEqual(next(m for m in expected if m['name']=='portal-groups')['config']['multivalued'],'true')
        for wrong in ['false',True]:
            bad=deepcopy(actual);next(m for m in bad if m['name']=='portal-groups')['config']['multivalued']=wrong
            cases.append(('group multivalued drift '+str(wrong),bad,False))
        for label,mappers,allowed in cases:
            with self.subTest(mapper=label), tempfile.TemporaryDirectory() as directory:
                play=Path(directory)/'test.yaml'
                play.write_text(yaml.safe_dump([{'hosts':'localhost','connection':'local','gather_facts':False,
                    'vars':{'portal_client':{'protocolMappers':mappers},'portal_desired':{'protocolMappers':expected}},
                    'tasks':[{'name':'Synthetic mapper assertions','no_log':True,'block':selected}]}]))
                result=subprocess.run(['ansible-playbook','-i','localhost,',str(play)],capture_output=True,text=True,
                    env={**os.environ,'ANSIBLE_LOCAL_TEMP':directory+'/local','ANSIBLE_REMOTE_TEMP':directory+'/remote'},timeout=30)
                self.assertEqual(result.returncode==0,allowed,result.stdout+result.stderr)
        self.assertEqual(len(cases),11)

if __name__=='__main__':unittest.main()
