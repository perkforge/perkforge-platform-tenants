# perkforge-platform-tenants

Platform-owned, explicit **tenant enrollment with paused shared defaults**. Cluster roots select small
tenant folders; those folders point to external tenant app repositories under
scoped identities. This repository has no Big Bang app configuration or charts.
Local portal boundaries are operator-applied separately; enrollment cannot grant
its own security permissions. No credentials are stored here. Platform-owned reusable
tenant foundations and per-tenant overrides (namespace/RBAC, NetworkPolicy,
quota and enrollment) belong here as they are reviewed, not in app repositories.

- [local](clusters/local/kustomization.yaml) and [dev](clusters/dev/kustomization.yaml) explicitly select
  [portal enrollment](tenants/portal/README.md).
- Omit a tenant resource from a cluster root to omit enrollment on that cluster.
- [Nextcloud pilot enrollment](tenants/nextcloud/README.md) has a separate
  `clusters/local-nextcloud` selector pinned to published app v1.1.2. It enables
  no Portal resources. The selected app adds two Apache workers and a 512Mi/1Gi
  memory budget; CPU, probes, PHP and retained storage stay unchanged. Publication
  does not change the live chain; reviewed enrollment/platform releases and
  separately approved promotion and runtime checks are still required.
  There is no automatic repository or directory discovery.
- The platform bootstrap owns cluster/provider prerequisites and references this repository with
  a pinned GitRepository/Flux Kustomization. Tenant repositories own app manifests
  and values; tenants cannot edit this privileged enrollment boundary.

Each cluster root explicitly selects the tenant app's named-cluster path with a
small one-field patch. App environment selection stays in app Git; multiple app
clusters can share environment defaults without adding platform/Big Bang values.
The local/dev source pins and paths must be advanced and validated together.

Cluster context is explicit native YAML: `commonAnnotations` records cluster,
environment and profile on the built enrollment objects. Local selects local/il2;
dev selects dev/il2. App Git selects matching
reusable environment/profile inputs. Cross-repository tests compare protected
platform selection, enrollment metadata/path and app metadata/inputs at exact
pins, including deliberately mismatched environment/profile/target cases.
Annotations are selection evidence, not policy enforcement or IL authorization.
No empty/fake foundation policy profiles are added here; platform controls require
separate review/live validation and cannot be relaxed by app profile values.

Local portal namespace/RBAC, PSA, quota, network and native admission definitions
are proposed under `tenants/portal/foundation`; they are not live-verified tenant
isolation. Start with the focused [local trial plan](tenants/portal/LOCAL-TRIAL.md).

## Portal staging context

The following describes the earlier Portal staging sequence, not the current
Nextcloud selection linked above. Only Portal local is declaratively unsuspended;
dev and shared defaults stay suspended.
Publication alone does not activate a Portal platform selection.
Portal config release `v1.0.0` is published and selected by `spec.ref.tag`.
`release-evidence.json` records its resolved source commit separately; CI rejects
missing/unpublished or moved tags and validates the actual checked-out app paths.
After a reviewed Portal enrollment release, platform can separately select its
verified tag. The Nextcloud-only platform path does not select Portal.
That staging record used an identity-only platform stage. Advancing Portal to
this activation release and live security tests require separate approval.

Offline build checks (no API access):

```sh
kubectl kustomize clusters/local > /tmp/tenant-enrollments-local.yaml
kubectl kustomize clusters/dev > /tmp/tenant-enrollments-dev.yaml
```

CI uses the runner's existing kubectl to build both roots and the empty opt-out
case. PyYAML parses test inputs; read-only GitHub calls verify the published app
tag before its checkout/path/context tests. No Kubernetes API is contacted. Local
cross-repository checks also verify pins/paths, scoped field contracts and app
chart inactivity. These checks do not prove live authorization or isolation.

Future profiles (for example il5) need reviewed platform requirements and matching
explicit app selections; no il5 deployment input is included. To add a tenant,
add a small platform-owned folder under `tenants/`, declare its reviewed foundation
and scoped identity contracts, then include it only in the intended cluster roots.
Never place those controls in the app repository.

## Configuration versions

See [RELEASING.md](RELEASING.md) for reviewed release PRs, immutable-tag
expectations, first-release ordering and the staged switch to tag-based refs.

Selection annotations use `platform.perkforge.io/cluster`, `/environment` and `/profile`. This migration requires a compatible published portal configuration release, followed by an enrollment release and a separately reviewed platform pin advance. Never rewrite old tags or enable enrollment as part of metadata maintenance.
