# Nextcloud plus admin-only Portal

This optional composite preserves the existing Nextcloud selection byte-for-byte
and selects released Portal app configuration v2.1.0. It is not selected by the
existing platform root. Portal uses the existing digest-pinned app, one25m CPU/
64Mi replica and admin-only server policy. No new human privileges are granted.

Before selecting this enrollment path at an immutable reviewed commit, verify:

- Physical Portal client/role and TLS identity, private GHCR read credential,
  exact namespace-bound OpenBao/ESO delivery and target Secrets are ready.
- Portal public identity CA, approved exact Keycloak HTTPS egress and ingress
  routing exist. The DNS-only baseline is insufficient for OIDC.
- Existing scoped reconcilers, admission policies and runtime SA remain intact.
- App config v2.1.0 and its pinned image are available without changing builds.

Use physical native OpenBao/ESO custody, never historical VM delivery scripts.
Keep the Portal rollout coordinated with the integrated pilot. Availability and
admin login alone do not satisfy Mattermost/ntfy context-notification acceptance.
Check unauthorized login denial and preserve Nextcloud health before completion.
