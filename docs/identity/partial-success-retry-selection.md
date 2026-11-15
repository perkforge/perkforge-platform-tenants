# Reviewed partial-success retry selection

This source selects enrollment v2.10.0 (`3f3d630e70a5f6db7282779cae059202229cb517`)
and platform v0.48.0 (`95ef0f103a89fe71b7e5aff93d0f3dd2ce31947c`). Both normal
release tags were verified. The 27-file bundle has 99,587 UTF-8 bytes and manifest
`763db8699537d09e25650d7e31338b68056b65c72c2d89033f6452bdab96dbb1`.

Prior foundation attempt `89fa3d6348444b25ede774bebe27287c083b5932d4ea192b4dc5826a7e6191c5`
completed successfully. Its attestor failed before issuer publication. The exact
owned evidence ConfigMap remains empty; this is not an attestation success.
Retry generation 1 therefore binds that actual foundation predecessor and an
explicit empty `identity_previous_attestation_invocation`. Group reconciliation
also binds the exact prior source `4b027b7a50ebf477a36746b88d0f034cc6a7d454`.
The adapters must revalidate retained private receipts and native group IDs;
no deletion, reset, fabricated receipt or blind replay is permitted.

New invocation is `3d08188c5f24e69af33ee7e38f05bfbdb3bd3ff3d66a1d794488bb140c030c9c`.
The first immutable selection holds all three children. Only after old-child
quiescence, native admission/current source adoption and exact evidence/UID
preservation may the separately reviewed A selection release foundation and
attestation. B remains separate and requires fresh issuer evidence plus actual
nonempty metadata-only Flux SSA preservation. Five-minute evidence constraints
are unchanged. Retain successful and failed predecessor Jobs and the receipt PVC.

Image, credentials, native authority, target profile, placement and budgets remain
unchanged. Root-owned guard/grant objects are byte-equivalent to the preceding
selection. Source preparation and synthetic tests do not imply live activation or
membership completion. Send the actual new Job names before starting any phase.
