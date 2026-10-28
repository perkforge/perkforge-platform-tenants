# Portal enrollment: platform-owned, paused

`source.yaml` pins the external tenant deployment repository;
each cluster root selects `gitops/clusters/<name>` with a single `spec.path`
patch on `reconcile.yaml`. The reusable base deliberately has no valid default
cluster path, so forgetting a selection fails rather than choosing local silently. The local Kustomize file
puts these two paused objects in proposed namespace `tenant-example-portal`.
Both cluster roots explicitly select this folder. The definition alone does
not enroll every cluster or provision anything.

## Identity and ownership contracts

- The platform parent applies this protected enrollment Git as
  `tenant-enrollment-admin`. It needs only reviewed child source/reconciler
  permissions in approved tenant namespaces; it must not take desired state from
  tenant-controlled enrollment Git or grant broad fallback permissions.
- The child Flux Kustomization sets `spec.serviceAccountName: portal-reconciler`
  and targetNamespace `tenant-example-portal`. It may apply only approved tenant
  app release/config objects and cannot change platform policy, identities,
  enrollment sources/reconcilers or privileged namespaces.
- The tenant repository owns `gitops/clusters/<name>`, shared app defaults,
  environment values and its HelmRelease. That
  release sets `spec.serviceAccountName: portal-deployer` and separate
  `storageNamespace: tenant-example-portal-release`; runtime uses `portal-runtime`.
  This repository owns no app HelmRelease and contains no Big Bang package values.

All accounts, namespaces, secret references and permissions are prerequisites,
not created grants. Platform owns tenant namespace/quota/PSA/network/admission,
scoped identities and enrollment definitions in this repository: reuse reviewed
shared foundations with explicit per-tenant opt-in/overrides, rather than
duplicating every tenant foundation. Those controls are not implemented in this
illustration. Cluster/provider bootstrap remains in the platform repository;
credentials are provisioned separately, never stored here. RBAC plus admission
must constrain allowed release/source refs, identities, target/storage namespaces,
image/runtime/secret references and release-storage access. RBAC alone cannot
constrain arbitrary CR fields. Missing prerequisites must fail closed. No broad
RBAC, live secrets or fake proof of tenant isolation is supplied here.

## Pin and readiness limits

The exact review-stage portal pin is
`43ea0aba6f4c66fd6aa4d87800ac62fb6d0459e0` from portal PR #5. It contains the
paused tenant-owned named-cluster entrypoints and references the existing
`bundles/portal/chart` (`household-portal` 0.1.0), rather than copying the chart.
Application values default disabled; no image or client-secret value is approved.
A source-read Secret name is a reference only, not a credential in Git.
The app roots choose their own environment inputs; enrollment Git does not copy
app environment values. The extra app-only `dev-secondary` root shares dev
settings but is not automatically enrolled here.

`spec.suspend: true` stops both enrollment objects; `prune: false` adds no
root deletion authority. The caller's platform root and the app release are also
paused/disabled in their companion PRs. Merge is not activation. Preserve the
existing Fleet deployment; never let Fleet and Flux own the same app release.
Review foundation capacity/security, credential custody, admission/tenant denial
and recovery tests before any separately approved live action.

The [official Flux multi-tenancy example](https://github.com/fluxcd/flux2-multi-tenancy)
provides the parent/child pattern. Explicit per-cluster Kustomize resources are
the selection mechanism here; no Argo-style generator, Flux Operator ResourceSet,
new controller or replacement Flux lifecycle is introduced.
