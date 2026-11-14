from copy import deepcopy
import json
from pathlib import Path
import yaml
root=Path(__file__).resolve().parents[1]
policy=next(yaml.safe_load_all((root/'tenants/portal/foundation/inventory-configmap-policy.yaml').read_text()))
base={'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':'portal-enrollment-inventory','namespace':'tenant-portal'},'data':{'enrollment-inventory.json':'{}'}}
cases=[{'name':'exact-nonsecret-config','object':base,'allowed':True}]
for name, change in [
    ('wrong-name',lambda o:o['metadata'].update(name='portal-identity-ca')),
    ('wrong-namespace',lambda o:o['metadata'].update(namespace='other')),
    ('extra-key',lambda o:o['data'].update(secret='not-allowed')),
    ('binary-data',lambda o:o.update(binaryData={'payload':'YQ=='})),
    ('oversize',lambda o:o['data'].update({'enrollment-inventory.json':'x'*131073})),
    ('immutable',lambda o:o.update(immutable=True)),
    ('missing-data',lambda o:o.pop('data'))]:
    obj=deepcopy(base);change(obj);cases.append({'name':name,'object':obj,'allowed':False})
print(json.dumps({'Policy':policy,'Cases':cases}))
