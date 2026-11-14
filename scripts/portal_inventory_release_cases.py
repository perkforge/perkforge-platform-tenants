from copy import deepcopy
import json
from pathlib import Path
import yaml
root=Path(__file__).resolve().parents[1]
policy=next(yaml.safe_load_all((root/'tenants/portal/foundation/release-policy.yaml').read_text()))
base={'apiVersion':'helm.toolkit.fluxcd.io/v2','kind':'HelmRelease','metadata':{'name':'portal','namespace':'tenant-portal-config'},'spec':{'serviceAccountName':'portal-deployer','targetNamespace':'tenant-portal','storageNamespace':'tenant-portal-release','releaseName':'portal','chart':{'spec':{'chart':'./bundles/portal/chart','sourceRef':{'kind':'GitRepository','name':'tenant-portal'}}},'valuesFrom':[{'kind':'ConfigMap','name':name,'valuesKey':'values.yaml'} for name in ['portal-defaults','portal-environment','portal-profile','portal-cluster']]}}
active=deepcopy(base); active['spec']['valuesFrom'].append({'kind':'ConfigMap','name':'portal-cluster','valuesKey':'enrollment-inventory.values.yaml'})
cases=[{'name':'existing-four','object':base,'allowed':True},{'name':'exact-five','object':active,'allowed':True}]
for name,change in [
 ('wrong-inventory-map',lambda o:o['spec']['valuesFrom'][4].update(name='other')),
 ('wrong-inventory-key',lambda o:o['spec']['valuesFrom'][4].update(valuesKey='other.yaml')),
 ('secret-reference',lambda o:o['spec']['valuesFrom'][4].update(kind='Secret')),
 ('target-path',lambda o:o['spec']['valuesFrom'][4].update(targetPath='identity')),
 ('optional',lambda o:o['spec']['valuesFrom'][4].update(optional=True)),
 ('sixth-source',lambda o:o['spec']['valuesFrom'].append(deepcopy(o['spec']['valuesFrom'][4]))),
 ('reordered',lambda o:o['spec']['valuesFrom'].reverse()),
 ('wrong-base-key',lambda o:o['spec']['valuesFrom'][0].update(valuesKey='other')),
 ('wrong-deployer',lambda o:o['spec'].update(serviceAccountName='other'))]:
 obj=deepcopy(active);change(obj);cases.append({'name':name,'object':obj,'allowed':False})
print(json.dumps({'Policy':policy,'Cases':cases}))
