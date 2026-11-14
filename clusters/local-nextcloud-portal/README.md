# Nextcloud plus admin-only Portal

This optional composite preserves the existing Nextcloud selection byte-for-byte
and selects released Portal app configuration v2.2.0. It is not selected by the
existing platform root. Portal uses the existing digest-pinned app, one 25m CPU/
64Mi replica and admin-only server policy. No new human privileges are granted.

Before selecting this enrollment path at an immutable reviewed commit, verify:

- Physical Portal client/role and TLS identity, private GHCR read credential,
  exact namespace-bound OpenBao/ESO delivery and target Secrets are ready.
- Portal public identity CA, approved exact Keycloak HTTPS egress and ingress
  routing exist. The DNS-only baseline is insufficient for OIDC.
- Existing scoped reconcilers, admission policies and runtime SA remain intact.
- App config v2.2.0 and its pinned image are available without changing builds.

Use physical native OpenBao/ESO custody, never historical VM delivery scripts.
Keep the Portal rollout coordinated with the integrated pilot. Availability and
admin login alone do not satisfy Mattermost/ntfy context-notification acceptance.
Check unauthorized login denial and preserve Nextcloud health before completion.

`tenants/portal/sso/render-physical.yaml` renders public trust, approved ingress/
issuer egress, the existing ESO foundation and three consumers without API calls.
Provide `portal_hostname`, `portal_bao_server`, `portal_issuer_ipv4`, a verified
public `portal_public_ca_file`/SHA256, an absolute `portal_physical_output`, and
`portal_physical_render: true`. The fixed namespace/identity/record names preserve
the existing Portal admission and custody contract; origins and network address
are target inputs. This small-cluster path assumes the same approved public CA
trusts Keycloak and OpenBao. Do not use it unchanged when their trust differs.
Apply requires the separately approved security/credential batch, no target Secret
collision, populated exact records and matching existing Portal identity. Never
apply consumers before reviewing their targets. Verify actual synchronized payloads
and TLS chain before activating the app. The renderer does not provision credentials,
change Keycloak, apply resources, enable the source, or bypass approval gates.

The active Portal selection uses published configuration v2.3.2 and its normal-published
app v0.6.1 digest. Apply the matching platform-owned runtime-contract before source
promotion. Platform-admin access requires only the exact signed platform-admin group,
not tenant membership. CI renders the actual released active chart and rejects the
old auth image; historical disabled fixtures and the default paused roots remain unchanged.

If the CNI evaluates ingress hostPort/service traffic after destination translation,
the ingress IP/32:443 rule alone may not match. After verifying the native RKE2
Traefik pod port, opt in with `portal_ingress_pod_egress: true` and set
`portal_ingress_pod_tls_port` (default `8443`). This adds only the same shared TLS
ingress peer selected by namespace and pod labels; it does not bypass hostname/CA
validation, grant direct Keycloak access or enable HTTP. Leave it off for targets
that do not need this translated-port rule.
