# Nextcloud pilot enrollment

## Selected source contract

`clusters/local-nextcloud` selects published app **v1.1.0**, commit
`8c8ed5e140049b41e676dffd1c45a953ff1ef23b`; `release-evidence.json` records and
verifies that pin. Platform **v0.26.0** selects enrollment **v1.5.0** through this
Nextcloud-only root. It includes no Portal resources. Shared defaults remain
paused/UNCONFIGURED; `clusters/local` and `clusters/dev` are separate Portal paths,
not alternatives for Nextcloud activation.

The selected app uses the digest-pinned private SSO image, enabled database/web
releases, guarded non-root same-Pod cron and fixed read-only OIDC mounts.
Foundation remains operator-owned and separately applied from a clean published
enrollment checkout; the tenant child cannot reconcile its own authority.

The 2026-11-07 acceptance check observed this source chain Ready, working private
DNS/trusted HTTPS and same-Pod cron. The owner confirmed SSO, native admin access,
display name and logout; separate local recovery is retained. This dated evidence
supersedes the earlier unselected/unresolved-DNS preparation state below, not a
promise of continuing health or proof of all isolation boundaries. Independent
paired backup/restore, household-client acceptance and real household import
remain pending. Recheck current readiness and recovery before maintenance.

### Sources and operator procedures

- [App operations](https://github.com/perkforge/perkforge-tenant-nextcloud/blob/v1.1.0/docs/operations.md)
  and [native SSO](https://github.com/perkforge/perkforge-tenant-nextcloud/blob/v1.1.0/sso/README.md)
  own workload/native-provider procedures and independent local recovery.
- [OIDC/CA delivery and registry prerequisites](sso/README.md) own protected input
  delivery. Required runtime references are `nextcloud-registry-existing`,
  `nextcloud-oidc` and `nextcloud-oidc-ca`. None is created by source selection.
  Reuse exact owned immutable inputs; do not rotate or overwrite them during
  documentation cleanup. Node-side pull verification is separate from Pod egress.
- [Platform issuer policy](https://github.com/perkforge/perkforge-platform/blob/v0.26.0/big-bang-bootstrap/configuration/identity/nextcloud/local/README.md)
  owns selected issuer egress and its operator-admin access prerequisite.
  Enrollment's offline SSO boundary renderer is not a competing live policy owner.
- [Platform enrollment prerequisites](https://github.com/perkforge/perkforge-platform/blob/v0.26.0/big-bang-bootstrap/configuration/ansible/enrollment-prerequisites.yaml)
  validate the explicit selected Nextcloud root. Do not use the Portal path or
  broaden the reconciler identity to bypass a prerequisite failure.

For future changes, merge/publish reviewed app and enrollment releases, verify
actual immutable tags, and then separately approve platform promotion. Never
fabricate a future tag. Publication does not itself deliver credentials, apply
foundation policies, change issuer egress or activate native SSO. Preserve the
existing GitLab/runner stage. The initial data-only sequence used enrollment
v1.2.1/app v1.0.1; it is historical staging, not a reason to downgrade or replay
bootstrap on the accepted installation.

The guarded same-Pod activation originated in app v1.0.4 and is preserved in
v1.1.0. The pilot uses
32Gi files plus 16Gi PostgreSQL on the accepted two-replica longhorn-dedicated
tier (platform v0.19.0). Storage expansion requires coordinated app values,
admission and quota review before household import. No single-excess claim is
allowed here. One web process, one database instance and serial cron are an empty
pilot, not application HA or accepted household load. Both prefer worker-2; worker-1
remains eligible. On fresh installation or recovery, verify initialization, trusted HTTPS, synthetic retention and bounded same-Pod execution with the released policy. Verify matching container/volume SELinux labels and two successful background runs after the controlled rollout.

## Reviewed expansion foundation: 128Gi files / 144Gi quota

This candidate raises both `nextcloud-budget` storage quota keys from `48Gi` to
`144Gi` for 128Gi files plus the unchanged 16Gi database. The two-PVC count and
all CPU/memory, class, identity, image, network and deletion boundaries remain
unchanged. Files admission permits only the existing 32Gi or reviewed 128Gi size,
with monotonic UPDATEs. The selected app v1.1.0 still requests 32Gi; its pin and
release evidence are deliberately unchanged so the foundation can precede expansion.
A rollback to a 32Gi app manifest after expansion is denied, not a recovery path.

Merge/publish the paired app change and this foundation through human review.
For a separately authorized rollout, first verify the published enrollment
release and apply only the reviewed quota/files-policy objects. Foundation is
operator-applied separately; the `clusters/local-nextcloud` Flux root does not
include it and must not be granted authority to reconcile its own boundaries.
Recheck native schema/type warnings and positive/negative admission, then verify
actual new app tags before updating app pin/evidence and the platform enrollment
pin in later reviewed releases. Do not fabricate future tags or apply a feature
branch. Publishing these changes alone performs no live expansion or promotion.

Before rollout require the exact expandable `longhorn-dedicated` class, two healthy
replicas on the actual dedicated disks, current free/scheduled capacity including
96Gi additional per replica, snapshots/reserves/rebuild headroom and a recoverable
paired backup for protected data. Afterward verify the original PVC/PV identities,
128Gi request/capacity and filesystem, both healthy replicas, unchanged 16Gi DB,
144Gi quota use and web/cron/synthetic-file retention. Preserve resources on any
failure; never shrink, delete/recreate claims, or loosen admission to roll back.
Any required restart is a separate disruption decision. Backup/restore acceptance
and household import remain separate gates.

## What the foundation owns

Corey retains full platform administration. This foundation adds no ClusterRole,
ClusterRoleBinding, OIDC authentication change or replacement of existing owner
bindings. Its policies scope the tenant's resources; the owner still controls
those policies and can perform reviewed recovery. The reconciler/deployer identities
are limited automation accounts, not Corey's personal administrator identity.
Nextcloud's initial application administrator is separately bootstrapped from its
operator-delivered admin Secret and must be verified in the app. Kubernetes or Keycloak platform-admin status does not implicitly grant native
Nextcloud admin. The accepted mapping was an explicit native-app operation.
The released private image includes the plugin, but provider activation is a
separate gated operation.
Use the app runbook's local-admin-first, explicit-SSO-mapping-later procedure;
preserve local recovery and existing platform administration.

Three restricted namespaces separate configuration, runtime and Helm release
Secrets. No Pods are allowed in configuration/release namespaces. Reconciler and
deployer Roles cannot modify namespaces, RBAC, NetworkPolicies, admission or source
selection. Runtime credentials cannot be read through deployer RBAC; Helm storage
Secret access is confined to its own release namespace. Retained files claims
and CNPG Clusters cannot be directly deleted by the deployer. Application Helm
uninstall/reset is not an approved operation. It would still remove app workloads;
keep it separate from data-retention and restore claims.

Admission fixes the release/chart/source/values contracts, private route, image
digests, dedicated claim budgets, single Recreate web replica and serial colocated
cron. It prevents arbitrary Secret/token mounts, CNPG identity use by app templates
and spoofed CNPG labels. Restricted PSA supplies container/host security checks.
Flux's inline values are preserved untyped JSON and cannot be directly inspected
by typed CEL. Named values references are constrained; safety is enforced on the
rendered resources, including inline overrides. Source pins and operator review
remain necessary. No unsupported `has(object.spec.values)` check is used.
CNPG's existing platform operator creates its own narrowly scoped instance-manager
ServiceAccount/Role/binding, jobs, certificates and PVC. Review those actual generated
objects before acceptance; this foundation adds no operator cluster permissions.

The foundation network baseline permits only DNS, Traefik-to-web TCP80, app/cron-to-own-database TCP5432
and the observed platform-cnpg controller-to-instance-manager TCP8000. App Pods
have no API or general internet egress. The selected platform issuer policy
separately adds bounded issuer TCP443 egress, shared by same-Pod cron. CNPG API
egress uses the protected endpoint renderer below. No public routing, Redis or
household import is supplied. DNS/TLS and network enforcement require live checks.

The shared `cnpg-system/platform-cnpg` operator initially watches only `gitlab`.
This foundation adds its pinned 1.30.1 namespaced Role and RoleBinding only in
`tenant-home-nextcloud`. The subject is the platform operator, never a tenant
identity. It can reconcile database resources and read Secrets in this namespace;
it gains no other namespace or cluster-wide Secret permission. Apply the reviewed
foundation before selecting a published platform stage that sets both the actual
operator Deployment and config to `gitlab,tenant-home-nextcloud`. Do not create a
second operator or use an empty/all-namespace watch. Verify operator readiness,
watch list, positive Nextcloud and GitLab access, and denial in an unrelated
namespace before creating the Nextcloud database. Keep the existing GitLab Role
and database unchanged. The controller rollout briefly pauses reconciliation;
this is not an instruction to restart database Pods.

CNPG alone needs API egress. Before activation, privately inventory the Kubernetes
Service IP and actual API endpoints, then render an additional policy with:

```sh
ansible-playbook -i localhost, ansible/render-nextcloud-api-policy.yaml \
  -e @/ABS/PRIVATE/api-inputs.yaml -e nextcloud_api_reviewed=true
```

Inputs are nextcloud_api_cidrs (1–4 reviewed IPv4 /32 endpoints) and a fresh
nextcloud_api_output file in an owner-only 0700 directory. The renderer makes no
API calls and never applies anything. Review actual Service/DNAT behavior and the
required 443/6443 ports; broad subnet or 0.0.0.0/0 egress is refused. This is a
required hardware-specific input, not a default wildcard or a fake successful
CNPG setup. App labels cannot select this API policy.

## Fresh-installation and recovery gates

The following order describes initial setup and separately approved recovery, not
instructions to replay completed activation or overwrite existing inputs. Preserve
the running database, claims and local recovery. Backup/restore and household
acceptance remain outstanding even though the current pilot is selected.

1. Review app and enrollment together. Verify chart 9.4.1 archive
   hash and both image digests, version/security compatibility and the accepted
   dedicated disks. App v1.1.0 is published and pinned with exact evidence. Keep the
   platform parent unselected through prerequisites and credential preparation.
   First accept the published data-only stage and deliver its public database CA.
   Then promote this released web stage; accept the disabled correction and bounded same-Pod checks before this controlled activation, then verify real sidecar progress and sustained web health.
   Do not manually change HelmRelease suspension against selected Git values.
2. Choose encrypted independent backup destination, retention and key custody;
   confirm nextcloud.perkforge.home.arpa DNS and private trusted TLS. Deliver
   nextcloud-admin, nextcloud-db-app and nextcloud-tls only in runtime using the
   gated input workflow below. The public local source needs no source-read Secret. No
   Secret values belong in Git, logs or this document.
3. Under separate live approval, verify exact published source/cluster UID, apply
   foundation plus reviewed endpoint policy, and server-validate all native CEL
   policies/CRDs. Check type warnings and actual positive/negative admission before
   resuming sources/child. Test impersonated Roles, cross-tenant network denial,
   forbidden Secret/API access, alternate images/sources/identity, generic storage
   and data deletion. Offline tests do not prove those controller boundaries.
4. Activate data only. Verify CNPG Ready, TLS-only HBA, its generated RBAC/identity,
   16Gi PVC and both actual SSD replica IDs. Export only the CNPG CA's public ca.crt
   to a nextcloud-db-ca ConfigMap in runtime; never copy its signing key. Require
   its fingerprint and Service hostname SAN to match the database. App/cron mount
   this public ConfigMap read-only at /etc/nextcloud-postgres-ca. Do not weaken
   verify-full or mount certificates below an image's read-only /etc subdirectory.
5. Activate app only after DB/public-CA/TLS gates. Verify the 32Gi files claim's SSD
   replica placement, directory ownership, initialized web and trusted private
   HTTPS. Run the app repository's database TLS probe for positive verified TLS and
   wrong-CA, wrong-hostname and plaintext denials. Keep credentials out of output.
   The current app already selects same-Pod cron; on fresh setup require initialization
   before running writers and verify repeated successful background runs. Drain/recovery must quiesce all cron
   writers before moving the web workload.
6. Verify synthetic WebDAV data, paired database/files/config backup and isolated
   restore, then load/upload limits. No real files until those gates and Corey's
   separate import/housecleaning direction. Never reset or overwrite existing data.

Build foundation and the selected enrollment root independently with kubectl kustomize.
Tests use actual pinned-chart renders and native CEL expression evaluation;
live schema/type-check, authorization, CNPG defaults, network/DNAT, TLS and restore
remain acceptance gates. Source definitions alone are not proof of isolation.

## DNS, HTTPS and credential delivery

The earlier unresolved-name/workstation-hosts observations were preparation history.
Private DNS and trusted HTTPS were working at the acceptance check above. For
maintenance or another client, verify `nextcloud.perkforge.home.arpa` resolution,
routing and certificate trust; do not reuse historical VM addresses or TLS material.
Keep physical ingress addresses in protected local inputs, not Git. A successful
workstation check is not household-client DNS/TLS acceptance. Never use Service/Pod
IPs as household ingress destinations.

The accepted setup uses operator-owned private-CA issuance. Use an explicitly approved issuance
path for a server certificate with DNS SAN `nextcloud.perkforge.home.arpa`, matching
leaf key and full intermediate chain. Trust the public root on each browser/sync
client. Keep the signing key in operator custody; only the leaf key enters the TLS
Secret. This ingress/client trust is separate from CNPG's database CA. Issuance,
DNS changes, credentials and delivery remain separate live approvals, not side
effects of this source change.

After the namespace foundation exists, supply an external 0700 directory containing
0600 regular owner files `admin-username`, `admin-password`, `db-password`, `tls.crt`
and `tls.key`. Choose the owner-controlled bootstrap admin name explicitly; do not
reuse old VM passwords. Password inputs are one-line strings of at least 20
characters; lookup removes trailing whitespace. Store/recover these inputs through
the approved encrypted backup workflow, never Git or chat. Supply the public
ingress CA trust bundle separately. From a clean, published enrollment checkout:

```sh
ansible-playbook -i localhost, ansible/deliver-nextcloud-inputs.yaml \
  -e @/ABS/PRIVATE/nextcloud-inputs.yml -e nextcloud_inputs_apply=true
```

Private YAML supplies `enrollment_tag`, `target_kubeconfig`, `target_context`,
`expected_cluster_uid`, `nextcloud_private_dir` and `nextcloud_ingress_ca_file`.
Default/check modes touch no API or private file. Apply verifies the exact clean
published checkout, cluster UID and namespace label, file ownership/modes, HTTPS
chain/purpose/hostname/expiry and leaf key match. It sends only the three intended
Secrets through hidden stdin, server-validates all before creation and refuses
existing objects. It never rotates credentials, overwrites or emits private files.
Certificate bundles must contain no private key; the leaf key file must contain
one matching, unencrypted private key. Bundled signing keys are rejected.
Partial creation must be inspected; do not retry blindly or delete retained inputs.
No local sudo is required when using the existing authorized admin kubeconfig.

After separately approved data activation, verify CNPG Ready and its server
certificate Service SAN/fingerprint, then project **only** public `ca.crt` to the
runtime `nextcloud-db-ca` ConfigMap. Do not copy `ca.key`, a signing key or the
server private key. This public-CA delivery is not performed by the bootstrap
Secret playbook and must precede web activation. Then run the existing read-only
app TLS probe and require wrong-CA, wrong-hostname and plaintext failures. Neither
that runtime probe nor household client TLS/backup restore is accepted by a build.

Repeat the offline checks with Python/PyYAML/Ansible, kubectl, Helm and Go 1.27.3:

```sh
mkdir -m 700 /ABS/FRESH/schema-fixtures
bash tests/nextcloud-cel/fetch-schemas.sh /ABS/FRESH/schema-fixtures
export NEXTCLOUD_APP_CHECKOUT=/ABS/PUBLISHED/v1.1.0-nextcloud-checkout
export NEXTCLOUD_ROLLBACK_APP_CHECKOUT=/ABS/PUBLISHED/v1.0.4-nextcloud-checkout
export NEXTCLOUD_CHART=/ABS/VERIFIED/nextcloud-9.4.1.tgz
export NEXTCLOUD_OPENAPI=/ABS/FRESH/schema-fixtures/openapi.json
export NEXTCLOUD_CRD_DIR=/ABS/FRESH/schema-fixtures
python3 -m unittest discover -s tests -p 'test_*.py' -v
cd tests/nextcloud-cel && go test -count=1 -v .
```

The schema fetcher pins source commits for Kubernetes 1.36.5, Flux helm-controller
1.6.4/source-controller 1.9.5/kustomize-controller 1.9.5 and CNPG 1.30.1, matching
the reviewed target. No cluster API is called. CI verifies and checks out the selected v1.1.0 release
and the explicit v1.0.4 rollback fixture at their recorded commits. Both real
chart renders remain covered; the former app PR head is no longer a fixture.
Every policy is type-checked, including an intentionally invalid-field control,
before positive real renders and negative mutations are evaluated. Repeat against
the actual controller schema/defaults before live acceptance. Never treat a successful offline case as proof of authorization or
network isolation.

`-count=1` is required: Go's test cache cannot reliably track YAML and external app
files read by the Python render subprocess. Build/dependency caching remains safe.

## Historical cron correction and current contract

The bounded separate-Pod cron test completed, but web shared-volume access failed
until an automatic restart. Suspected SELinux MCS relabeling requires host audit
confirmation. The separate CronJob remains suspended; the selected same-Pod
runner is the current execution path. The released policy permits only
the web Deployment's existing `nextcloud` and optional `nextcloud-cron` containers,
with the same pinned image, UID33 and existing token/volume restrictions. It adds
no RBAC, Secret access, host mounts or fixed SELinux labels. Extra or substituted
sidecars remain denied. CronJob containers still have the existing single-container
limit; this policy does not enable or resume them.

The preceding app v1.0.3 deployed the same-Pod correction with its runner disabled.
The selected private image preserves the guarded non-root runner from v1.0.4.
Do not replay the earlier disabled stage as routine maintenance. Runtime acceptance must show continuous web health and
synthetic-file retention over multiple successful runs, matching container/volume
MCS labels, and no audit denials. No household import or backup claim is included.

## SSO policy ownership

[The offline SSO renderer](sso/README.md) remains unselected review tooling.
The live issuer policy is selected by platform Git, not this renderer. Do not
apply generated policy output over that adopted object. The enrollment foundation
owns the separately applied runtime admission policy; neither the app nor the
enrollment child may grant itself policy authority.

The source runtime policy admits [digest-pinned PerkForge GHCR images with the fixed
private-pull reference](sso/README.md#registry-trust-and-private-pull-review-prerequisite).
App/init/cron cannot mix images. App Git selects the exact digest. The legacy
v1.0.4 render remains an explicit rollback fixture and its exact public image
remains admitted; that exception is not evidence the public image is still active.
Rollback, credential rotation, policy withdrawal and session revocation each
require their applicable approval and recovery checks.
