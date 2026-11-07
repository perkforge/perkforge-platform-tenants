# Nextcloud registry input delivery

`deliver-nextcloud-registry.yaml` captures the operator-owned delivery of exactly
`tenant-home-nextcloud/nextcloud-registry-existing`. It uses an **existing**,
read-only GHCR package credential. It creates no account/token, grants no scopes,
logs into no registry, changes no policy, and activates/restarts no workload.
Do not invoke Portal's registry workflow for Nextcloud.

Default and `--check` runs read no private inputs and contact no APIs, even with
the apply flag set in check mode. An actual run requires separate approval to
share the specified credential with this exact cluster/namespace Secret. Use a
clean checkout of a published enrollment release containing this playbook; the
shared release guard refuses dirty, unpublished or mismatched source.

## Protected operator inputs

Supply `nextcloud_registry_config_file` as an absolute, canonical nonsymlink path
to an owner-owned 0600 regular UTF-8 dockerconfigjson file in an owner-owned 0700
directory. It must contain only `auths`, with only `ghcr.io`, and that entry must
contain only canonical base64 `auth` for `username:token`. No credential helper,
identity token, second registry, plaintext password field or embedded key is
accepted. Maximum input size is 64 KiB. Use the original exact bytes for reuse;
JSON whitespace changes are not silently rewritten on the immutable Secret.

The operator must verify the existing token is read-only (`read:packages` and
only approved package access) and set `nextcloud_registry_read_only_confirmed`.
The playbook validates input shape, not GitHub token scopes or pull success.
Never export the developer's `gh` keyring credential for this purpose. Do not put
credential values in Git, extra-vars, process arguments, chat or logs. This
workflow neither creates nor saves a new persistent credential in GitHub.

A private variables file supplies these non-secret path/selection fields:

- `enrollment_tag`: actual published release containing the playbook.
- `target_kubeconfig`, `target_context`, `expected_cluster_uid`: exact approved target.
- `nextcloud_registry_config_file`: protected existing dockerconfigjson path.
- `nextcloud_registry_read_only_confirmed: true`: operator-verified scope.
- `nextcloud_registry_approval: nextcloud-registry-delivery-v1`: exact approved operation.

After approval, from that released checkout:

```sh
ansible-playbook -i localhost, ansible/deliver-nextcloud-registry.yaml \
  -e @/ABS/PRIVATE/nextcloud-registry-inputs.yaml -e nextcloud_registry_apply=true
```

## Fixed delivery and refusal contract

The playbook verifies the cluster UID and runtime namespace labels, including
restricted PSA v1.36. It reads only the named Secret, never lists Secrets. For an
absent input it server-validates and then creates one immutable
`kubernetes.io/dockerconfigjson` Secret via hidden stdin with only
`.dockerconfigjson` data and ownership label
`platform.perkforge.io/managed-input=nextcloud-registry-v1`.

An existing object is reused only when name, namespace, ownership label, type,
immutable flag and exact data match, with no ownerReferences or pending deletion.
Foreign, controller-owned, mutable, extra-data or mismatched
objects fail closed without adoption, relabeling, overwrite, rotation or deletion.
The ownership label matches the approved existing input. Its actual immutable
flag and exact data must be checked by a future authorized execution; this source
cleanup did not read live credentials or claim those fields were freshly verified.
Do not run the playbook merely because the source PR merges.

A readback verifies the same contract after creation or reuse. API failures and
uncertain creation stop without automatic retry or cleanup. Inspect only the named
input under the existing approval before repeating; a later exact owned match can
be reused with zero writes. A mismatch needs separately reviewed recovery, never
force replacement. Named Secret data is held only for comparison under `no_log`;
use no verbose/debug callbacks or fact caching that could expose it.

Delivery is not node-side pull acceptance. Verify the exact app image digest can
be pulled separately before an approved rollout. OIDC client/CA delivery, issuer
policy, native SSO activation, credential rotation and session revocation remain
separate operations. This playbook is outside every Flux Kustomization and gives
no reconciler permission to manage credentials.

## Offline verification

```sh
KUBECONFIG=/dev/null python3 -m unittest discover -s tests \
  -p test_nextcloud_registry_delivery.py -v
```

Tests run real Ansible against fake Git/GitHub/Kubernetes commands and synthetic
credentials. They cover default/check refusal, source/target/input gates, scoped
create/readback/reuse, foreign/mismatch refusal, redaction and uncertain failures.
They are not real-cluster authorization, credential-scope or registry-pull proof.
