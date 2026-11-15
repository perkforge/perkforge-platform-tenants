> Historical retry0 checkpoint. The subsequent partial-success retry is documented in `partial-success-retry-selection.md`.

# Corrected released executable: held replacement attempt

The executable is enrollment v2.9.0, exact commit
`4b027b7a50ebf477a36746b88d0f034cc6a7d454`, paired with unchanged platform v0.47.0
`b904017158100944a81129899e8fc64a3ed976b8`. The maintained Ansible image and all
runtime resource, isolation, deadline and receipt-storage constraints remain
unchanged. Bundle manifest is
`a3cd3cb767ad59076ac03482f93871e050e078c66ccb7cedc0fa735b2e8dfb51`:
27 files, 98,839 UTF-8 bytes. Compared with the prior bundle, only run-phase.py,
revisions.json and provenance.sha256 differ. The executable change is the
reviewed bounded projection read for AtomicWriter source metadata.

This is a new declared attempt, not deletion/replay of the retained failed Job.
The prior foundation process failed before any successful receipt publication;
the exact evidence CM was read back empty and the child group was not observed.
No predecessor envelope exists to authenticate. Therefore the existing strict
first-publication contract remains previous_invocation empty/retryGeneration 0.
The changed released source revision produces a new invocation and Job identity.
Do not invent predecessor success or relax the issuer CAS to increment a counter.
Unexpected native receipt/provider state must fail closed during the new run.

The held stage keeps all three child Kustomizations suspended. It may be selected
only after the old-attempt child hold and quiescence have been verified. It must
not start a Job merely because source, input names or foundation hash changed.
After current-generation admission, exact-controller source adoption, empty
issuer-data preservation and fresh resource/storage gates pass, stage A may set
phasesSuspended explicitly false with membershipReleased false. Stage B changes
only the membership scheduling gate and its exact admission/hash; it requires
fresh real issuer evidence and the nonempty metadata-only SSA preservation proof.
No stage grants broader permissions or weakens the five-minute evidence bound.

New Jobs (not yet created by this source preparation):
- tenant-identity-writer/identity-portal-foundation-74a1fd77a43038f5
- tenant-identity-attestor/identity-portal-attest-74a1fd77a43038f5
- tenant-identity-writer/identity-portal-memberships-74a1fd77a43038f5

The owner must receive these actual names and a heads-up before any new Job
starts. Retain the failed b9c6 predecessor Job, existing PVC and native evidence
UID. Source tests and the synthetic AtomicWriter fixture are not a successful
live provider run, permission grant or completion claim.
