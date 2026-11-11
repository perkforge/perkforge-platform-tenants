# Inactive Portal runtime consumers

This directory is a separately reviewed **consumer stage**, not selected by any
cluster root, Portal enrollment, normal foundation, or `../eso` foundation.
Publication alone does not activate it. Offline render only:
`KUBECONFIG=/dev/null kubectl kustomize tenants/portal/eso-consumers`.
It creates only three ExternalSecrets, no credentials, Stores, trust material,
RBAC, workload changes or runtime Secret literals. No release or tag is assumed.
The existing Nextcloud selection and running transfer must remain untouched.

## Exact proposed field contract

All objects use namespace `tenant-portal` and its namespaced SecretStore
`openbao-tenant` (KV-v2 mount `tenants`). Remote keys below are mount-relative,
not API paths with `data/`. These are proposed records/fields, not a claim that
values exist or have been approved. Credential approval and population remain
pending. Do not read or copy legacy VM credentials to fill this contract.

| ExternalSecret | Remote key | Remote property → target key | Target Secret | Type |
| --- | --- | --- | --- | --- |
| portal-oidc | tenant-portal/oidc | client-secret → client-secret | portal-oidc-existing | Opaque |
| portal-registry | tenant-portal/registry/ghcr | dockerconfigjson → .dockerconfigjson | portal-registry-existing | kubernetes.io/dockerconfigjson |
| portal-tls | tenant-portal/tls | certificate → tls.crt; private-key → tls.key | portal-local-tls | kubernetes.io/tls |

Source properties deliberately have no dots or JSON-path operators. Only the
Kubernetes target keys use dotted names. Do not use `.dockerconfigjson`, `tls.crt`
or `tls.key` as source properties or assume CRD validation proves provider
extraction behavior. No existing credential records require migration.

Values are literal strings, not base64 wrappers: a complete Docker config JSON
object and PEM certificate chain/private key respectively. `decodingStrategy:
None` avoids automatic decoding; Kubernetes Secret encoding is ESO's responsibility.
Explicit `spec.data` mappings avoid `dataFrom`, find/list, wildcard paths and
cross-tenant access. No new OpenBao rights or controller permissions are included.
Template `mergePolicy: Merge` preserves the explicitly fetched keys in the typed
output; it does not authorize merging with an existing unmanaged Secret.

`portal-identity-ca/ca.crt` remains separately delivered public Portal-to-Keycloak
trust, outside these consumers. Do not replace it with `eso-openbao-ca`, the
separate public OpenBao trust input. No CA private/signing key belongs here.

## Conservative lifecycle

`creationPolicy: Orphan` avoids setting an ownerReference that would garbage-collect
runtime Secrets if an ExternalSecret is removed. `deletionPolicy: Retain` keeps
existing downstream values when a remote record disappears; failures must be
investigated, not resolved by deleting runtime inputs. Orphan is **not** a collision
or adoption guard: ESO can update an existing same-named Secret.

`refreshPolicy: OnChange` deliberately avoids background credential rotation.
This is a conservative staged-delivery candidate, **not acceptance of automatic
central rotation** under [platform #31](https://github.com/perkforge/perkforge-platform/issues/31).
That issue remains open for reviewed refresh cadence/policy, approved destinations
and live evidence that rotations reach only intended consumers. If ongoing central
rotation is required, review a Periodic policy and safe consumer reload plan before
activation; this draft does not silently enable it.
After initial synchronization, a remote edit alone does not refresh the target.
Each intended refresh requires a separately reviewed ExternalSecret metadata/spec
change and verification of its Ready/synced state. A new/recreated ExternalSecret
can synchronize immediately. Do not treat this as a freeze against controller
reconciliation or as a substitute for access controls. Retirement, revocation and
cleanup of retained Secrets are explicit operations, not automatic rollback.
No restart/reloader annotation is added. OIDC environment values, image pulls and
TLS consumers have different reload behavior; verify each and separately approve
any required restart, with no Nextcloud workload changes.

## Gates before any activation

1. Independently approve the exact released source chain and isolated Portal stage,
   cluster UID/context, ESO native v1 CRDs/controller readiness, PushSecret disabled,
   bounded auth role/policy, verified OpenBao public trust and Ready SecretStore.
   Use the prerequisites and shared-controller caveats in `../eso/README.md`.
2. Approve credentials and their exact record/field destinations separately. Verify
   the OIDC client matches the Portal registration, registry credential is scoped
   for the intended image, and TLS chain/key/SANs match Portal. Never log values.
3. Check metadata only for each target name: existence, type, immutable flag,
   ownerReferences, managers/labels and other writers. Check for competing
   ExternalSecrets too. Stop on any existing Secret, ownership collision, immutable
   target or uncertainty. Do not overwrite/adopt/delete it implicitly; approve a
   specific migration/rollback plan first. This YAML does not enforce that gate.
4. Only the platform-owned enrollment reconciler/operator may manage consumers.
   App reconciler/deployer permissions stay unchanged. Do not wire this directory
   into roots or `../eso`; stage ordering is not a readiness or permission gate.
5. Apply only under separate live authorization after the gates. Verify exact
   target types/keys and ESO status without displaying values. Keep app enrollment
   paused until its distinct rollout gates pass. On failure, stop the Portal stage;
   do not alter the active Nextcloud source, resources, restart state or transfer.

Offline tests validate the pinned native schema and exact manifests, including
negative drift cases and exclusion from all existing roots/foundations. They do
not prove live readiness, valid credential contents, reload behavior or isolation.
