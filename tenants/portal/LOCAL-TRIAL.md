# Physical Portal baseline: source preparation only

Portal is separate from Nextcloud. `clusters/local` selects only Portal; the existing
`clusters/local-nextcloud` source, release and render are unchanged. Both Portal
source and child are suspended. Published physical app configuration `v2.0.0` is
selected with verified release evidence. Its local HelmRelease remains suspended and its chart disabled.
Do not unsuspend this chain before the remaining custody and activation gates.

## Boundary and release order

- `tenant-portal-config`: source/child, app HelmRelease/values and scoped deployer
  identities; zero Pods. The existing `flux-system/tenant-enrollment-admin` receives
  only namespaced GitRepository/Kustomization CRUD through `portal-enrollment`.
  A separately named platform source/parent can reuse it without changing Nextcloud.
- `tenant-portal`: stateless runtime, no API grants/token or PVC. One Recreate Pod,
  25m/64Mi requests, 250m/192Mi limits, frozen published Portal v0.3.0 digest.
- `tenant-portal-release`: isolated Helm history, zero Pods.
- Physical workers require `storage.perkforge.io/worker=true` and required absence
  of control-plane/master labels. Admission denies nodeName and tolerations.
- Admission fixes the image, issuer, client/audience `portal-local`, exact server-side
  `platform-admins` policy, disabled tenant source, public CA mount and resource budget.
  Application authorization still requires signed claims, `/platform/admins`, and
  the client-specific `tenant-reader` role. UI changes are outside this baseline.

The published physical app configuration `v2.0.0` resolves to
`e8de0e3cf68d01860b0addaa3b38e24f928d5ff6`. Offline checks render that actual
release, verify disabled output, and force-enable it only in tests against the
physical admission boundary. The historical VM v1.0.0 fixture must remain denied.
Review/release this enrollment next, then separately review the independent platform
Portal selection at that real enrollment tag. Never use future or moved tags.
Publication is not deployment approval.

## Required runtime custody work

Physical deployment is blocked on reviewed isolated OpenBao + ESO runtime input
delivery. Controller and Store/RBAC isolation design remains a separate review.
The platform migration is tracked in
[platform issue #32](https://github.com/perkforge/perkforge-platform/issues/32).
Do not introduce manual Kubernetes Secret delivery as a competing physical design.
There is no ESO delivery implementation in this change. Required app contracts are:

- `portal-oidc-existing/client-secret`, scoped only to `portal-local`.
- `portal-registry-existing`, GHCR read-only pull authentication, not mounted.
- `portal-local-tls`, certificate/key for `portal.perkforge.home.arpa`.
- `portal-identity-ca/ca.crt`, public CA trust only.

`ansible/deliver-portal-inputs.yaml` and `deliver-portal-registry.yaml` are historical
VM helpers, not physical runbook steps. Never import VM credentials or CA signing
keys, rotate existing identities, or reuse Registry1 credentials for GHCR.

## Source-only identity and network preparation

`ansible/configure-portal-identity.yaml` remains default off. Default/check mode
reads no credentials and makes no API calls. The guarded path verifies the published
source, exact physical issuer endpoint, reviewed public CA fingerprint, and owned
private input directories/files. Later approved execution may create only the owned
`portal-local` client in existing `perkforge`, with code + S256, exact callback
`https://portal.perkforge.home.arpa/auth/callback`, basic/profile scopes and exact
client-role/group mappings. It rejects unowned clients and drift, not rewrites them.
No users, memberships, realm import, Headlamp client or API OIDC changes are included.
Secret provisioning for that later operation must follow the reviewed custody design.
See [MAPPER-LIFECYCLE.md](MAPPER-LIFECYCLE.md) for the existing exact-response tests.

`tenants/portal/sso/prepare.yaml` renders only unselected review output. Set
`portal_sso_render=true` with a fresh absolute `portal_sso_output` in a private
directory outside this checkout. Never commit the generated boundary or physical IP.
Supply reviewed private
`portal_sso_issuer_ipv4`, and public `portal_sso_ca_file`/`portal_sso_ca_sha256`.
It permits only one RFC1918 IPv4 /32 on TCP 443, checks public certificate/fingerprint,
and refuses overwriting output. No physical address is committed. Default/check
mode performs no input reads or writes. Operator foundation provides DNS and
Traefik ingress only; issuer egress is denied until this separately approved output
is applied. Real CNI/NAT behavior and TLS verification remain live acceptance gates.
An L3/L4 allowance to shared ingress cannot constrain HTTPS Host/SNI to Keycloak;
other applications on that endpoint may be reachable. This does not prove complete
cross-tenant network isolation. Do not widen egress to pass a test.

## Later, separately approved activation

Verify the cluster UID/context, published chain, actual worker headroom, immutable
image and authenticated GHCR pull. Complete runtime custody, review/apply foundation,
validate admission warnings/negative cases, public trust/leaf SAN/key, exact issuer
route, owned client, and Portal-only DNS/ingress. Then review explicit activation
changes in app, enrollment and independent platform source. All other tenants stay
unchanged. Test real admin SSO, developer/no-grant denials, session/logout, network
and scoped identity denials. Offline tests do not prove live isolation or capacity.

Contain through a reviewed Git change that suspends only the independent Portal
parent/source. Wait for shared cluster-root to reconcile that exact change, then
pause the Portal child/HelmRelease and scale Portal to zero. Manual parent suspension
alone is insufficient because cluster-root can restore it. Emergency live-only
containment needs a separately reviewed plan. Preserve Nextcloud, transfers,
namespace/policy/credential state and existing identity/platform services. No shared
root suspension, VM capacity estimates or VM credential paths are part of this plan.

## Platform administrator identity without tenant roles

For the compatible Portal application that authorizes `platform-admins` using
validated issuer/audience/authorized-party and exact `/platform/admins` membership,
select `portal_identity_access_policy: platform-admins` in reviewed operator inputs.
The client body keeps code + S256, basic/profile, exact callback/origin, groups and
explicit Portal audience. It omits the client-role mapper, creates no tenant role,
and adds no role or scope mappings. The existing exact admin group is read only;
users and memberships are never changed. `fullScopeAllowed` remains false.

The default is `platform-admins`; it cannot accidentally grant a tenant role.
Explicit `tenant-reader` retains the legacy client-role/mapping procedure for
older application releases. Select policy together with the compatible application
release; changing this input alone neither upgrades the app nor migrates an existing
client. Existing incompatible mapper/role state is refused, not silently rewritten,
deleted or adopted. Any existing-client transition requires separately reviewed
scope. Both paths retain release, CA, protected-input, ownership, exact mapper and
credential-custody gates; default/check mode remains inert. This source addition
authorizes no live identity change or grant.
