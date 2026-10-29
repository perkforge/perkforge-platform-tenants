# Portal enrollment: platform-owned and paused

`source.yaml` selects the published app configuration tag; `clusters/local` and
`clusters/dev` explicitly choose `gitops/clusters/<name>`. No tenant folder is
automatically enrolled. The app repository owns HelmRelease and values, never
Big Bang or platform security configuration.

The **local trial proposal** adds separately applied boundaries and a scoped
three-namespace deployment. Start with [LOCAL-TRIAL.md](LOCAL-TRIAL.md) for the
entrypoint, release order, budget and later live approval. `dev` keeps the prior
contract-only example; its foundation identities are not provisioned here.

Local source/child Kustomization live in `tenant-portal-config`; the child
impersonates `portal-reconciler` there. Tenant Git can apply only ConfigMaps and
the reviewed HelmRelease. It cannot change its enrollment/source or RBAC.
The app HelmRelease impersonates `portal-deployer` from that same control namespace,
targets runtime `tenant-portal` and stores Helm history in `tenant-portal-release`.
`portal-runtime` has no API grants or mounted API token. Human admin access is an
application policy; it never grants workload/deployer cluster-admin.

`foundation/` is operator-owned namespace/RBAC, PSA, quota, network and native
admission; it is deliberately absent from the ordinary cluster enrollment root.
`ansible/prepare-local-portal.yaml` applies it only after published-code/UID guards
and separate approval. `foundation/routing.yaml` has its own later TLS readiness gate.
No credentials, tenant memberships, OpenBao/ESO or new controllers are supplied.

The app pin selects published v0.2.0, containing the portal v0.3.0 image digest
and explicit local admin-only configuration. Source/reconciler/release suspension,
app disabled defaults keep this proposal inactive. The operator image allowlist
now matches the published source v0.3.0 digest selected by app v0.2.0. Private GHCR
credential delivery and all live security steps still require approval. Offline checks are not live tests.

Cluster/environment/profile annotations remain matching selection evidence, not
security enforcement or IL authorization. App values cannot relax platform
boundaries; admission negative tests and real authorization/network checks remain
separate. The protected parent/child pattern follows the
[official Flux multi-tenancy example](https://github.com/fluxcd/flux2-multi-tenancy).
No change to the existing Fleet deployment or controller lifecycle is included.
