# Local portal trial: activation selection requires live approval

The platform root knows only this enrollment repository. `clusters/local` selects
portal; `dev` is unchanged. The app owns chart/values, this repo owns security.

| Namespace | Purpose |
| --- | --- |
| `tenant-portal-config` | Protected source/child reconciler, app HelmRelease/values and deployer identities; zero Pods allowed |
| `tenant-portal` | Runtime and portal-specific OIDC/TLS inputs; no runtime API token or RoleBinding |
| `tenant-portal-release` | Scoped Helm history, inaccessible to runtime; zero Pods allowed |

Flux impersonates `portal-reconciler` for app ConfigMaps/HelmRelease and
`portal-deployer` for runtime Deployment/Service plus readiness reads and isolated
Helm storage. Neither can create RBAC/security or mount identities across namespaces.
Native admission fixes source/identity/namespace references, approved image,
admin-only environment and private Service. The operator image contract pins the published v0.3.0 image digest selected by
app v0.3.0; missing or mismatched image contracts deny runtime creation. No new controller,
OpenBao, ESO, database or PVC. PSA restricted and quotas remain platform-owned.
This constrains tenant automation, not trusted cluster administrators.

## Release order

1. Source policy release/image: verify published digest, dependency audit, image smoke. GHCR remains private; authenticated pull verification is pending.
2. App configuration: pin digest in local values, release chart/config.
3. Enrollment: select the real app tag/evidence; pin the same image in the operator
   contract; release. Platform then selects that enrollment tag/evidence.

No nonexistent tags are inserted. App v0.3.0 is now published and selected, with its exact image in the operator
allowlist. This does not enable or authorize deployment. Only the published local app/source/child selection is active; dev/shared defaults
remain paused/disabled. The existing live platform stage does not enroll this source.
Advancing it requires separate live approval. Offline proposal checks do not validate a future published chain.

## Later bundled live approval

- Verify exact cluster UID, published chain and fresh headroom. Apply generic
  platform enrollment prerequisites and this local foundation with gated Ansible.
  Check policy type warnings and server dry-run denials before unpausing anything.
- Generate one portal client secret and HTTPS leaf/key under protected
  `.secrets/bigbang-local-trial-01/portal/`. Reuse the public trial CA; keep its
  signing key on the workstation. Deliver only portal-specific Secret/TLS inputs
  and the public CA. Readers can use those credentials; no secrets enter Git/logs.
- Run `ansible/configure-portal-identity.yaml` from the approved published tag.
  Create/reuse only owned `portal-local` in existing `perkforge`, exact HTTPS
  callback `/auth/callback`, code+S256 and audience/azp `portal-local`. Map only the
  client-specific `tenant-reader` role to existing `/platform/admins`. No users,
  memberships, realm import, rotation, Headlamp client or API OIDC changes.
  Unowned clients or drift fail instead of being overwritten.
- Add only `portal-local-il2.local-lab.test` routing to `.201`; verify its CA-signed
  TLS leaf without warning bypass. Supply `portal-oidc-existing/client-secret`,
  `portal-local-tls` and `portal-identity-ca/ca.crt`, then explicitly apply routing.
- Separately approve read-only GHCR credential delivery as runtime
  `portal-registry-existing` and verify an authenticated pull; never reuse Registry1
  credentials against GHCR or change package visibility. The default-off registry delivery playbook still requires separate live approval.
- Enable only the reviewed portal app and resume protected enrollment/source/
  reconciler/release in order. Test real admin SSO, developer/no-grants denials,
  signed tenant-only fixtures, session/logout, network and scoped identity denials.

One Recreate Pod requests **25m/64Mi**, limits **250m/192Mi**. Prior worker request
snapshot of 1500m/1792Mi becomes 1525m/1856Mi, leaving 475m/1797Mi before system reserve.
No added controller/storage. Admission overhead and actual Node startup peaks are
unmeasured. Keep existing host 2048Mi/node 512Mi, swap/PSI/OOM guards and ten-minute watch.

On failure, pause only new enrollment/portal reconcilers and scale portal to 0;
preserve namespaces, credentials, policies and existing Headlamp/Keycloak/Flux.
No restart is needed. Capture sanitized failures/retries; never widen roles to pass.
Publication does not authorize credential, security, host/network or workload writes.

## Private registry delivery (default off)

The app references `tenant-portal/portal-registry-existing` as an imagePullSecret.
It is not a mounted workload credential. Before activation, separately approve a
read-only GHCR `read:packages` credential with access to only the private portal
package where supported. Agree its owner, expiry/rotation, owner-only local file
and exact Secret delivery method. `ansible/deliver-portal-registry.yaml` accepts only a preexisting `portal_registry_file`
with one `auths.ghcr.io.auth` entry. It rejects helpers/other registries, symlinks,
non-owner/private-mode files and malformed credentials. Its `no_log` gate verifies
clean published source and exact cluster UID, then creates only that named
`kubernetes.io/dockerconfigjson` Secret in `tenant-portal` via private stdin.
It defaults off (`portal_registry_apply: false`), and check mode reads no files/API.
The current input playbook deliberately delivers only OIDC/TLS/public-CA inputs;
it does not read or provision registry credentials; the new separate registry
playbook is the only registry input path. Do not use Registry1 credentials
for GHCR, persist Docker login, change package visibility, or place credentials in Git.
Verify an authenticated manifest/pull before unpausing; preserve failed pull evidence
without credential headers. Secret readers can reuse the credential.


## Activation ordering and containment

Preparation changes never clear suspension or set app enablement. Activation is a
separate reviewed diff: local app `enabled: true` plus local HelmRelease unsuspended;
local enrollment source/child unsuspended; local platform enrollment source/parent
unsuspended. Shared defaults and dev stay paused/disabled. Publish and select actual
release tags in app → enrollment → platform order; never substitute future tags.
The activation review must update pause-only regression expectations while retaining
dev/default assertions and adding exact local activation assertions.

Live order after explicit approval: verify UID/releases/headroom; apply generic
platform and tenant foundations; verify admission warnings/server dry-run denials;
deliver portal registry/OIDC/TLS/CA inputs and configure the owned client; validate
TLS, authenticated image pull and routes; select the reviewed platform stage last.
Sources and child reconciliation then proceed through the reviewed scoped identities.
No resource relies on Kustomize file order: foundations/inputs are explicit operator
prerequisites before unpaused app reconciliation. Routing is separately gated.

For containment, suspend root `flux-system/cluster-root` first so it cannot
restore parent reconciliation, then parent `flux-system/tenant-enrollments`, child
`tenant-portal-config/tenant-portal`, app HelmRelease `tenant-portal-config/portal`
and its source. Pause only the portal HelmChart source as needed to stop retries.
Scale only `tenant-portal/portal` to zero after reconcilers are paused. Preserve
namespaces, policies, credentials, data and existing Headlamp/Keycloak/Flux Pods.
The shared root pause temporarily stops GitOps changes, not running services.
Return to a reviewed paused platform stage/tag before resuming that root; an old
app tag alone cannot override admission or automatically remove portal safely.


## Keycloak response normalization

The pinned Keycloak 26.8.0 server adds logout defaults and the computed
`realm_client` response field. The drift check tolerates only these extra string
values when present: `backchannel.logout.session.required: 'true'`,
`backchannel.logout.revoke.offline.tokens: 'false'`, `realm_client: 'false'`.
All requested attributes remain exact; unknown additions, wrong types/values,
client field changes, mapper changes and secret mismatch still stop execution.
No existing client is rewritten or secret rotated to satisfy this check.
The regression executes the actual Ansible assertions with 13 synthetic cases.

Versioned upstream sources: [OIDC client creation defaults](https://github.com/keycloak/keycloak/blob/26.8.0/services/src/main/java/org/keycloak/protocol/oidc/OIDCLoginProtocolFactory.java#L705-L709)
and [computed realm-client representation](https://github.com/keycloak/keycloak/blob/26.8.0/server-spi-private/src/main/java/org/keycloak/models/utils/ModelToRepresentation.java#L842).
After a reviewed release, reuse the owned `portal-local` client and protected
files at the checkpoint; do not rerun credential generation or realm initialization.
