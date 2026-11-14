# Portal enrollment: platform-owned

Portal remains independent of Nextcloud. `clusters/local` and `clusters/dev`
explicitly select app paths; both Portal source/child selections are suspended.
Published physical app configuration `v2.0.0` is selected with verified tag/commit
evidence and remains disabled/suspended. Physical activation is blocked pending
reviewed enrollment/platform releases and OpenBao + ESO runtime custody.

The tenant owns HelmRelease/chart/values, never platform security. Operator-owned
`foundation/` provides namespace/RBAC, PSA, quota, network and native admission;
it is absent from ordinary enrollment roots. The scoped reconciler/deployer retain
three separate namespaces and runtime has no API authority or persistent storage.
`ansible/prepare-local-portal.yaml` remains default off with explicit context/UID and
published-code guards; routing has its own later TLS readiness gate.

See [LOCAL-TRIAL.md](LOCAL-TRIAL.md) for the physical source contract, release order,
network/public trust preparation, credential custody blocker and later acceptance.
Offline source validation is not live authorization or isolation verification.

An [inactive ESO foundation](eso/README.md) defines the separately reviewed
post-controller/auth Store and bounded controller role. It is absent from all
ordinary roots and contains no ExternalSecret or credential delivery.

## Optional inventory security boundary

Inventory delivery is not enabled by adding these source policies. Apply and verify
`portal-inventory-configmap-boundary` policy/binding BEFORE granting ConfigMap
create to the deployer. Kubernetes RBAC cannot restrict create by resourceNames;
the fail-closed native admission rule supplies the exact-name/data boundary.
Deployer read/update/patch/delete is restricted to `portal-enrollment-inventory`
in `tenant-portal`. No Secrets, namespace-wide reads, runtime API token or egress
is granted. Other ConfigMaps (including identity CA) remain inaccessible.

Runtime admission permits only the optional exact inventory read-only mount and
four strictly validated provenance/mode variables, while preserving the old
CA-only pod. Reviewed runtime image pin still applies. Verify denial cases before
activation; do not disable admission or apply RBAC first. This change requires
explicit security-boundary approval before live application.
