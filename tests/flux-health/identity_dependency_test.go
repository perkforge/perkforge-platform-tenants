package fluxhealth

import (
	"context"
	"encoding/json"
	fluxcel "github.com/fluxcd/pkg/runtime/cel"
	"os/exec"
	"strings"
	"testing"
)

// Pinned Flux runtime CEL implementation, not an approximation with another evaluator.
func TestIdentityPhaseDependencyCurrentReady(t *testing.T) {
	raw, err := exec.Command("python3", "-c", `import sys,json,runpy,contextlib,io;sys.path.insert(0,'../../scripts');from finite_identity import render;from identity_context_fixture import alternate
with contextlib.redirect_stdout(io.StringIO()):f=runpy.run_path('../../scripts/identity_foundation_cases.py')
print(json.dumps([render(d)[p+'-reconcile.yaml']['spec']['dependsOn'][0]['readyExpr'] for d in (f['D'],alternate(f['D'],f['I'],f['custody'],'atlas')[0]) for p in ('attest','memberships')]))`).CombinedOutput()
	if err != nil {
		t.Fatalf("fixture: %v %s", err, raw)
	}
	var expressions []string
	if err = json.Unmarshal(raw, &expressions); err != nil {
		t.Fatal(err)
	}
	for i, expr := range expressions {
		evaluator, err := fluxcel.NewExpression(expr, fluxcel.WithCompile(), fluxcel.WithStructVariables("dep", "self"))
		if err != nil {
			t.Fatal(err)
		}
		for _, tc := range []struct {
			name                string
			suspend             any
			top, condition      any
			ready               string
			attempt, invocation string
			want                bool
		}{
			{"current-omitted", nil, int64(2), int64(2), "True", "attempt", "invocation", true},
			{"current-false", false, int64(2), int64(2), "True", "attempt", "invocation", true},
			{"held-current", true, int64(2), int64(2), "True", "attempt", "invocation", false},
			{"held-old-success-current-top", true, int64(2), int64(1), "True", "attempt", "invocation", false},
			{"resumed-old-success-current-top", false, int64(2), int64(1), "True", "attempt", "invocation", false},
			{"omitted-old-success-current-top", nil, int64(2), int64(1), "True", "attempt", "invocation", false},
			{"missing-ready-generation", false, int64(2), nil, "True", "attempt", "invocation", false},
			{"stale-top", false, int64(1), int64(2), "True", "attempt", "invocation", false},
			{"false-ready", false, int64(2), int64(2), "False", "attempt", "invocation", false},
			{"unknown-ready", false, int64(2), int64(2), "Unknown", "attempt", "invocation", false},
			{"wrong-attempt", false, int64(2), int64(2), "True", "other", "invocation", false},
			{"wrong-invocation", false, int64(2), int64(2), "True", "attempt", "other", false},
			{"bad-suspend", "false", int64(2), int64(2), "True", "attempt", "invocation", false},
		} {
			t.Run(strings.Join([]string{string(rune('0' + i)), tc.name}, "/"), func(t *testing.T) {
				annotation := func(a, v string) map[string]any {
					return map[string]any{"platform.perkforge.io/attempt": a, "platform.perkforge.io/invocation": v}
				}
				spec := map[string]any{"commonMetadata": map[string]any{"annotations": annotation(tc.attempt, tc.invocation)}}
				if tc.suspend != nil {
					spec["suspend"] = tc.suspend
				}
				cond := map[string]any{"type": "Ready", "status": tc.ready}
				if tc.condition != nil {
					cond["observedGeneration"] = tc.condition
				}
				dep := map[string]any{"spec": spec, "metadata": map[string]any{"generation": int64(2)}, "status": map[string]any{"observedGeneration": tc.top, "conditions": []any{cond}}}
				self := map[string]any{"spec": map[string]any{"commonMetadata": map[string]any{"annotations": annotation("attempt", "invocation")}}}
				if tc.name == "held-old-success-current-top" {
					legacy := strings.Replace(expr, " && (!has(dep.spec.suspend) || dep.spec.suspend == false)", "", 1)
					legacy = strings.Replace(legacy, " && has(e.observedGeneration) && e.observedGeneration == dep.metadata.generation", "", 1)
					old, e := fluxcel.NewExpression(legacy, fluxcel.WithCompile(), fluxcel.WithStructVariables("dep", "self"))
					if e != nil {
						t.Fatal(e)
					}
					value, e := old.EvaluateBoolean(context.Background(), map[string]any{"dep": dep, "self": self})
					if e != nil || !value {
						t.Fatalf("old false-ready counterexample not reproduced: %v %v", value, e)
					}
				}
				allowed, err := evaluator.EvaluateBoolean(context.Background(), map[string]any{"dep": dep, "self": self})
				if (err == nil && allowed) != tc.want {
					t.Fatalf("allowed=%v err=%v want=%v", allowed, err, tc.want)
				}
			})
		}
	}
}
