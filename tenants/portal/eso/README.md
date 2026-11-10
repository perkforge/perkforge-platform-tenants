# Inactive Portal ESO foundation

This is a separately invoked **post-CRD/controller/OpenBao-auth** stage, not part of
`foundation/`, any cluster root, app reconciliation or automatic discovery. It
creates only a token subject ServiceAccount, namespaced controller Role/RoleBinding
and namespaced SecretStore. It creates no ExternalSecret, runtime Secret, public CA
placeholder, credential, OpenBao policy or live grant. Publication does not apply it.

Offline review: `kubectl kustomize tenants/portal/eso`. Do not apply until a separately
approved operation verifies the exact released chain, cluster UID/context, native
ESO `2.12.0-bb.0` CRDs/controller readiness, protected trust and bounded OpenBao auth
configuration. The platform owner coordinates those prerequisites; Kustomize order
is not a CRD/readiness or authorization gate. Existing Nextcloud enrollment stays
unchanged. No runtime input migration or adoption is included.

## Coordinated identity and trust contract

- Native controller: `external-secrets/external-secrets`, class `perkforge`.
- Store: `tenant-portal/openbao-tenant`, served `external-secrets.io/v1`.
- OpenBao: verified HTTPS `https://openbao.perkforge.home.arpa`, KV-v2 mount `tenants`.
- Public CA: separately delivered `tenant-portal/eso-openbao-ca`, key `ca.crt`.
  This is a separate trust lifecycle from Portal's `portal-identity-ca`; neither
  bundle nor CA signing key is copied into this stage.
- Kubernetes auth: mount `kubernetes-eso`, exact role `eso-tenant-portal`, bound to
  `tenant-portal/eso-tenant-portal` and audience `openbao-eso`. The SA has automount
  disabled and no Kubernetes API grants. Native TokenRequest is the only intended
  authentication path; no static-token Secret or controller-token fallback.
- Proposed OpenBao policy permits only `read` on exact paths
  `tenants/data/tenant-portal/oidc`, `tenants/data/tenant-portal/registry/ghcr` and
  `tenants/data/tenant-portal/tls`. No `list`, wildcard or other-tenant paths. That
  policy/role must be independently reviewed and provisioned before stage application.
- Same-namespace CA and SA references omit `namespace`; this is a SecretStore,
  not a ClusterSecretStore. App reconcilers receive no Store/SA/ClusterSecretStore
  authority, and runtime admission still requires the exact `portal-runtime` SA.

## Shared-controller limits and stronger alternative

The selected baseline is one native ESO controller. Platform-owned global informer
RBAC supplies Secret list/watch and Store/ExternalSecret discovery; those cached
reads are cluster-wide, including other tenants. This tenant Role adds bounded
Portal mutation, trust reads and one named TokenRequest permission. Shared-controller
compromise can cross those namespaced permissions: this is **not hard tenant
isolation**. A controller class is routing only, and the native controller also
accepts unclassified stores. OpenBao scoped policies do not remove controller cache
visibility or turn class selection into an authorization boundary.

A PaaS deployment needing tighter separation should separately review a controller
per trust domain/tenant, namespace-scoped watches and Kubernetes permissions,
strict class handling where supported, distinct bounded OpenBao identities, and
admission preventing cross-domain Store/Secret references. Validate controller
cache behavior and compromised-controller blast radius before claiming isolation.
That is a documented alternative, not additional controllers or permissions here.

The controller can currently mutate Secrets within Portal, not only three names,
because native creation and lifecycle handling require namespace-level verbs.
Future ExternalSecret consumers and their admission/lifecycle constraints require
separate review; none are included in this stage.
