# Receipt extraction diagnosis (source only)

The first live reader started and failed, then UID cleanup and natural detached
baseline verification succeeded. No originals were captured. Its operator runner
did not preserve terminated status or logs before deletion, so the cause is unknown.
No retry is authorized by this source change.

The revised reader emits only an enumerated reason code or numeric filesystem
errno, never exception text, paths, or receipt content. A separate private operator
draft captures bounded protected failed status/log evidence before mandatory cleanup.
It has not been executed; it requires review and a separately authorized attempt.

The exact maintained-image Python `-c` CLI with an AtomicWriter-style UID projection
passed locally; a synthetic mode02770 context is correctly refused. This is not
proof of the actual PVC modes. Source of the released writers confirms group JSON
uses the eight expected fields and0600; launcher foundation capsule uses the nine
expected fields. Successful writer phases enforce private0700 ancestry/0600 files.

Kubernetes v1.33.12 `pkg/volume/volume_linux.go` lines66–73 and136–213: when an
fsGroup ownership pass runs, it ORs0660 into writable files and setgid/0770 into
directories. OnRootMismatch skips only when the volume root GID, mode superset and
setgid agree. Therefore recursive permission drift is possible if the root changes,
but is not established as the live failure. The reader itself has no fsGroup.

## Actual writer-generated synthetic byte check

Both the original19d1159 reader and diagnostic reader passed the complete `-c`
CLI in the exact cached maintained image with UID1001 and readonly mounts of
retained atlas writer output. Provenance: runtimeba7f181c441c0690cd576892a847cefa3f3df41a,
ABI7bf7a089be0346ff816fa70a40838f91bc4a7d74, synthetic platform
551ba9544e03c4af07299e6a075b4c2f8f04a1c5; the producing partial-success fixture
reported PASS171.830s. Both decoded transport bodies and hashes matched the exact
original synthetic writer bytes. This rules out a universal CLI/schema mismatch,
not live PVC permissions, identity, content, mount behavior or filesystem effects.
No live volume or provider endpoint was accessed by this check.
