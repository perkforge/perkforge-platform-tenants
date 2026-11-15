# Selected old-attempt pause checkpoint

This source stage holds all three existing Portal child Kustomizations. It does
not select the corrected executable or a new provider attempt. Relative to
reviewed enrollment stage `0732cff9aff9815d1bedec4b94ff2883ce75b577`, every generated
phase file is byte-identical except the two explicit `suspend: true` fields on
foundation and attestation. Membership was already suspended. The existing
failed Job is retained; no deletion or replay is requested.

The selected executable remains enrollment `5621e9b05bd94566c1bfdc6bcf8b75b0404e8ff0`
and platform `b904017158100944a81129899e8fc64a3ed976b8`. The source bundle remains
`43bad232454e5fb0698b417270dfbd329efa64cef34862c98af97dba0a311aaa`.
All Job names retain suffix `b9c6ab787d54ba27`; provider invocation, inputs,
credentials, receipt UID, image and resource budgets do not change.

The selected foundation digest changes only to pin the child scheduling gate:
`655ec3623b60d13f23f0e917ef1facdca45206d24916f7635e1b4a6ce3dea5db`.
The paired platform source must select this stage and its exact foundation hash;
this document is not a live selection or evidence that suspension has occurred.

Before replacing the executable, verify each existing child UID, suspend state,
controller suspension branch after the changed generation, leader continuity,
and absence of active predecessor work. A parent-only hold is insufficient.
Preserve the failed Job and existing receipt volume. Only then prepare the
reviewed released corrected executable in a new held attempt. Resume requires
explicit false scheduling fields; membership remains independently suspended.
