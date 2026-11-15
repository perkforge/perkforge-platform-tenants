# Current phase dependency readiness

A dependent phase requires the predecessor to be unsuspended (false or omitted),
with matching invocation/attempt, current top-level observedGeneration, and a
Ready=True condition whose own observedGeneration equals metadata.generation.
A suspended reconcile can advance the top-level observedGeneration while retaining
an earlier Ready condition. That retained success must not release a later phase,
even after the predecessor is resumed but before its new completion is observed.

The pinned Flux runtime evaluator regression covers Portal and atlas, both phase
edges, current success, held/resumed stale success, absent condition generation,
wrong attempts/invocations and false/unknown readiness. No controller feature flag,
authority, workload, receipt or provider input changes are part of this fix.
Selected outputs and their exact admission templates must be regenerated together
in a later reviewed source transition; this component alone changes no live state.
