# Pinned mapper lifecycle review

Reviewed Keycloak **26.8.0** public source and the already-collected nonsecret
portal response after token use. No new live token or identity operation was used.
The production change is one explicit `multivalued: 'true'` groups setting;
exact managed-field/mapper validation is retained.

| Path | Configuration effect and handling |
| --- | --- |
| [GroupMembershipMapper.setClaim](https://github.com/keycloak/keycloak/blob/26.8.0/services/src/main/java/org/keycloak/protocol/oidc/mappers/GroupMembershipMapper.java) | Forces `multivalued` string `true` on its supplied mapper model while building a token. This is observed in our returned client after token use. Declare it explicitly so initial/repeated validation is stable. |
| [AudienceProtocolMapper.setClaim](https://github.com/keycloak/keycloak/blob/26.8.0/services/src/main/java/org/keycloak/protocol/oidc/mappers/AudienceProtocolMapper.java) | Reads configured audience and checks the target client exists/enabled; adds a token audience. No mapper-config write found in this token path. Our client audience is explicit; no custom-audience fallback is selected. |
| [UserClientRoleMappingMapper](https://github.com/keycloak/keycloak/blob/26.8.0/services/src/main/java/org/keycloak/protocol/oidc/mappers/UserClientRoleMappingMapper.java) / [AbstractUserRoleMappingMapper](https://github.com/keycloak/keycloak/blob/26.8.0/services/src/main/java/org/keycloak/protocol/oidc/mappers/AbstractUserRoleMappingMapper.java) | Reads explicit portal client, claim path and type/multivalue flags; writes roles into token claims. No mapper-config write found in the token path. Factory construction sets defaults, but is not invoked as a new persistent mapper during issuance. |
| [AbstractOIDCProtocolMapper.getEffectiveModel](https://github.com/keycloak/keycloak/blob/26.8.0/services/src/main/java/org/keycloak/protocol/oidc/mappers/AbstractOIDCProtocolMapper.java) | Clones the mapper model before resolving UserInfo from the ID-token flag and introspection from the access-token flag. All three portal UserInfo flags are already explicitly false. Effective introspection defaults true for these access-token mappers; this clone is not another observed stored-client field to add blindly. |
| [OIDCAttributeMapperHelper](https://github.com/keycloak/keycloak/blob/26.8.0/services/src/main/java/org/keycloak/protocol/oidc/mappers/OIDCAttributeMapperHelper.java) | Converts claim values/types and token paths; inclusion/multivalue helpers read config. Token/JSON map writes are not writes to mapper configuration. |

The version's standard `basic` scope providers were also reviewed: `SubMapper`
sets the token subject and `UserSessionNoteMapper` sets authentication-time claims.
Standard `profile` uses `FullNameMapper`, `UserPropertyMapper` and `UserAttributeMapper`;
their issuance paths read configuration and set token claims, without another mapper
configuration mutation found. The scope construction is in the pinned
[OIDCLoginProtocolFactory](https://github.com/keycloak/keycloak/blob/26.8.0/services/src/main/java/org/keycloak/protocol/oidc/OIDCLoginProtocolFactory.java).
This source review does not certify arbitrary administrator edits to realm scopes.
The gated basic assignment separately checks its existing mapper names/types.

## Coverage and limits

- Independent nonsecret post-token fixture uses synthetic UUIDs; it is not generated
  from desired values. An omitted default in desired YAML must fail comparison.
- Real Ansible assertions cover wrong values/types, unknown fields and missing mappers.
- Isolated HTTPS tests validate initial client creation, then simulated token use,
  repeated validation/token use and unchanged administrative writes. The simulated
  mutation reflects the pinned groups implementation; no real JWT is minted there.
- All configured client mapper response fields now match the recorded post-token shape.
  No other deterministic client-map addition was found in reviewed token paths.
- These tests do not run Keycloak Java/storage/cache or all code/refresh/introspection
  flows. Successful live subject assignment, SSO and guarded observation remain pending.

## Deferred design note

Exact whole-response comparison couples our operator to server-added representation
fields, including fields that do not change our intended security contract. It has
caused avoidable release/retry churn. A later design review should separate managed
security intent, documented normalization and unrelated response metadata, backed by
claim/lifecycle tests. Do not solve that here by ignoring unknown attributes/config:
this repair keeps exact checks and adds only the verified explicit setting.
