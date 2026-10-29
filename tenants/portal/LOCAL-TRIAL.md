# Local portal trial: disabled until release and live approval

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
app v0.2.0; missing or mismatched image contracts deny runtime creation. No new controller,
OpenBao, ESO, database or PVC. PSA restricted and quotas remain platform-owned.
This constrains tenant automation, not trusted cluster administrators.

## Release order

1. Source policy release/image: verify published digest, dependency audit, image smoke. GHCR remains private; authenticated pull verification is pending.
2. App configuration: pin digest in local values, release chart/config.
3. Enrollment: select the real app tag/evidence; pin the same image in the operator
   contract; release. Platform then selects that enrollment tag/evidence.

No nonexistent tags are inserted. App v0.2.0 is now published and selected, with its exact image in the operator
allowlist. This does not enable or authorize deployment. All sources/releases stay paused and app disabled until
separate approval. Offline proposal checks do not validate a future published chain.

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
  credentials against GHCR or change package visibility. No delivery is implemented here.
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

## Private registry delivery contract (not implemented)

The app references `tenant-portal/portal-registry-existing` as an imagePullSecret.
It is not a mounted workload credential. Before activation, separately approve a
read-only GHCR `read:packages` credential with access to only the private portal
package where supported. Agree its owner, expiry/rotation, owner-only local file
and exact Secret delivery method. A future explicitly gated, `no_log` delivery
step must accept a preexisting credential file without printing arguments/data,
verify private regular-file ownership/mode, and create only that named
`kubernetes.io/dockerconfigjson` Secret in `tenant-portal` via private stdin.
The current input playbook deliberately delivers only OIDC/TLS/public-CA inputs;
it does not read or provision registry credentials. Do not use Registry1 credentials
for GHCR, persist Docker login, change package visibility, or place credentials in Git.
Verify an authenticated manifest/pull before unpausing; preserve failed pull evidence
without credential headers. Secret readers can reuse the credential.
