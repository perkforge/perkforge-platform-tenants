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

if __name__=='__main__':unittest.main()
