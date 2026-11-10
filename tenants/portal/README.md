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
