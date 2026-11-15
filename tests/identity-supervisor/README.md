# Maintained-image runtime-shape tests

Explicit local synthetic tests only. Uses the cached pinned IronBank image, no pull,
network, real credentials, provider or cluster API. Test resources are disposable.

- `python3 test_supervisor.py`: native timeout PID/signal/descendant cleanup and
  exact native FLOCK owner proof. Short2s/1s durations exercise production270s/10s
  mechanics. Private bind directory is owned0700. The copied guard is byte-identical
  to the platform v0.47.0 `verify_group_paths.py`, SHA256
  `833ee8e0ddfa21982767f52dd286bc72211bbd0514b63bd43f95bfcc8a1c76dd`.
- `python3 test_private_tmp.py --source REVIEWED_ENROLLMENT_TREE`: imports the exact
  renderer initializer constant. Creates disposable rootless mapped root2777,
  group1001 directories; runs init as UID1001 with all capabilities dropped.
  Success, repeat refusal, existing child, foreign file, symlink and wrong root
  mode are tested. Only the freshly-created child is normalized0700.
- `scripts/test_context_native_container.py --run --platform PLATFORM_TREE
  --output FRESH_OUTPUT --supervised-source REVIEWED_ENROLLMENT_TREE`: full
  synthetic atlas three-phase TLS flow using the exact supervisor constant and
  private temporary bind. One subject, idempotence and stale-attempt/projection
  denials. This fixture uses a service harness parent; the separate PID1 test
  establishes the supervisor process hierarchy.

All containers use500m CPU and512Mi memory caps. The private bind simulation does
not prove kubelet fsGroup/subPath lifecycle. Actual no-credential kubelet preflight,
native defaulted admission and fresh scheduler capacity remain separate gates.

Add `--atomic-writer` to the full driver to test actual filesystem projection
layout: timestamped directories, `..data`, and visible file/directory symlinks
for source, input, API, credential and evidence mounts. The synthetic publisher
retains earlier timestamped fixture versions, unlike kubelet's cleanup. Thus this
proves projection compatibility, bounded reads and phase behavior, not credential
mount isolation or removal of prior credentials. Exact per-phase mounts and
admission remain separate isolation evidence. All bytes and API endpoints here
are synthetic; no real provider credentials are used.
