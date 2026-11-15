# Native Flux health-expression regression

This isolated test imports the actual `NewStatusReader` and `NewStatusEvaluator`
used by kustomize-controller **v1.9.5**, rather than the Kubernetes admission CEL
fixture or the separate Flux dependency-expression scope. Its runtime v0.110.3,
health API v1.19.2, cli-utils v1.2.3, CEL v0.26.1 and parser dependency pins follow
[the controller's release go.mod](https://github.com/fluxcd/kustomize-controller/blob/v1.9.5/go.mod).
The controller delegates custom health expressions to
[the runtime evaluator](https://github.com/fluxcd/pkg/blob/runtime/v0.110.3/runtime/cel/status_evaluator.go).

Run `go test -C tests/flux-health -count=1 -v .` from the repository root.
The test reads the generator's actual rendered health expression, confirms the
old bare `has(status)` macro fails parsing, and checks current/stale/missing
status and warning states. Missing status may produce a native evaluator error;
it must never become Current. This source-only test performs no Kubernetes calls.
Normal candidate CI runs it alongside the existing admission/dependency suite.
Selected source A/B must be regenerated after this generic generator correction;
no executable bundle, Job input, provider permission or readiness bypass changes.
