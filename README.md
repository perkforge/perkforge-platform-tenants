# perkforge-platform-tenants

Platform-owned, explicit **paused tenant enrollment**. Cluster roots select small
tenant folders; those folders point to external tenant app repositories under
scoped identities. This illustration has no Big Bang app configuration, charts, implemented tenant
foundation controls, credentials or live bootstrap. Platform-owned reusable
tenant foundations and per-tenant overrides (namespace/RBAC, NetworkPolicy,
quota and enrollment) belong here as they are reviewed, not in app repositories.

- [local](clusters/local/kustomization.yaml), [dev](clusters/dev/kustomization.yaml),
  and [dev-secondary](clusters/dev-secondary/kustomization.yaml) explicitly select
  [portal enrollment](tenants/portal/README.md).
- Omit a tenant resource from a cluster root to omit enrollment on that cluster.
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
dev selects dev/il2; dev-secondary selects dev/il5. App Git selects matching
reusable environment/profile inputs. Cross-repository tests compare protected
platform selection, enrollment metadata/path and app metadata/inputs at exact
pins, including deliberately mismatched environment/profile/target cases.
Annotations are selection evidence, not policy enforcement or IL authorization.
No empty/fake foundation policy profiles are added here; reviewed platform-owned
controls remain unfinished and cannot be configured by app profile values.

All sources/reconcilers are suspended; this is review-stage configuration only.
The current portal pin is a feature commit from
[portal PR #5](https://github.com/perkforge/perkforge-tenant-portal/pull/5), not an
approved production revision. Review order: portal app PR first, then update the
enrollment pin to its approved merged commit and revalidate/merge enrollment;
then update/revalidate the platform proposal's enrollment pin and merge that.
Squash/rebase merges can change SHAs. Nothing automatically advances pins or
unsuspends after merge; activation and live security tests need separate approval.

Offline build checks (no API access):

```sh
kubectl kustomize clusters/local > /tmp/tenant-enrollments-local.yaml
kubectl kustomize clusters/dev > /tmp/tenant-enrollments-dev.yaml
```

CI uses the runner's existing kubectl to build both roots and the empty opt-out
case, without installing dependencies or contacting a Kubernetes API. Local
cross-repository checks also verify pins/paths, scoped field contracts and app
chart inactivity. These checks do not prove live authorization or isolation.
