package nextcloudcel

import (
	"context"
	"encoding/json"
	"github.com/google/cel-go/cel"
	admissionv1 "k8s.io/api/admissionregistration/v1"
	"k8s.io/apimachinery/pkg/api/meta"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/util/version"
	admissioncel "k8s.io/apiserver/pkg/admission/plugin/cel"
	"k8s.io/apiserver/pkg/admission/plugin/policy/validating"
	"k8s.io/apiserver/pkg/cel/environment"
	"os"
	"os/exec"
	"testing"
)

type expression struct {
	source   string
	variable bool
}

func (e expression) GetExpression() string { return e.source }
func (e expression) ReturnTypes() []*cel.Type {
	if e.variable {
		// Match the API server: variable expressions may have concrete types.
		return (&validating.Variable{}).ReturnTypes()
	}
	return []*cel.Type{cel.BoolType}
}

// Actual Kubernetes 1.36 admission CEL compiler; fixtures render the pinned app.
// Schema/type warnings and controller defaults still require server acceptance.
func TestNextcloudAdmission(t *testing.T) {
	data, err := exec.Command("python3", "../../scripts/nextcloud_admission_cases.py").CombinedOutput()
	if err != nil {
		t.Fatalf("fixtures: %s: %v", data, err)
	}
	var f struct {
		Policies []admissionv1.ValidatingAdmissionPolicy
		Schemas  fixtureSchemas
		Cases    []struct {
			Name, Policy, Resource string
			Object                 map[string]any
			Allowed                bool
		}
	}
	if err = json.Unmarshal(data, &f); err != nil {
		t.Fatal(err)
	}
	if len(f.Policies) != 13 || len(f.Cases) < 50 {
		t.Fatal("missing policy/mutation coverage")
	}
	if path := os.Getenv("NEXTCLOUD_OPENAPI"); path == "" {
		t.Fatal("NEXTCLOUD_OPENAPI and matching CRD schemas are required for native type checking")
	} else {
		raw, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		var s struct{ Definitions fixtureSchemas }
		if err = json.Unmarshal(raw, &s); err != nil {
			t.Fatal(err)
		}
		if len(f.Schemas) < 5 {
			t.Fatal("provide matching Flux and CNPG CRD schemas")
		}
		for k, v := range f.Schemas {
			s.Definitions[k] = v
		}
		mapper := meta.NewDefaultRESTMapper(nil)
		for _, g := range []schema.GroupVersionKind{
			{Group: "", Version: "v1", Kind: "ConfigMap"}, {Group: "", Version: "v1", Kind: "Service"}, {Group: "", Version: "v1", Kind: "PersistentVolumeClaim"},
			{Group: "apps", Version: "v1", Kind: "Deployment"}, {Group: "batch", Version: "v1", Kind: "CronJob"}, {Group: "networking.k8s.io", Version: "v1", Kind: "Ingress"},
			{Group: "helm.toolkit.fluxcd.io", Version: "v2", Kind: "HelmRelease"}, {Group: "kustomize.toolkit.fluxcd.io", Version: "v1", Kind: "Kustomization"},
			{Group: "source.toolkit.fluxcd.io", Version: "v1", Kind: "GitRepository"}, {Group: "source.toolkit.fluxcd.io", Version: "v1", Kind: "HelmRepository"},
			{Group: "postgresql.cnpg.io", Version: "v1", Kind: "Cluster"}} {
			mapper.Add(g, meta.RESTScopeNamespace)
		}
		checker := validating.TypeChecker{SchemaResolver: s.Definitions, RestMapper: mapper}
		for _, p := range f.Policies {
			if warnings := checker.Check(&p); len(warnings) > 0 {
				t.Errorf("%s type warnings: %+v", p.Name, warnings)
			}
			broken := p.DeepCopy()
			broken.Spec.Validations = append(broken.Spec.Validations, admissionv1.Validation{Expression: "object.definitelyNotARealField == true"})
			if len(checker.Check(broken)) == 0 {
				t.Fatalf("%s: schema checker failed its invalid-field control", p.Name)
			}
		}
	}
	base := environment.MustBaseEnvSet(version.MajorMinor(1, 36))
	env, err := base.Extend(environment.VersionedOptions{IntroducedVersion: version.MajorMinor(1, 36), EnvOptions: []cel.EnvOption{cel.Variable("variables", cel.DynType)}})
	if err != nil {
		t.Fatal(err)
	}
	compiler := admissioncel.NewCompiler(env)
	policies := map[string]admissionv1.ValidatingAdmissionPolicy{}
	for _, p := range f.Policies {
		policies[p.Name] = p
	}
	for _, tc := range f.Cases {
		t.Run(tc.Name, func(t *testing.T) {
			p, ok := policies[tc.Policy]
			if !ok {
				t.Fatal("unknown policy")
			}
			vars := map[string]any{}
			bindings := map[string]any{"object": tc.Object, "oldObject": nil, "namespaceObject": nil, "request": map[string]any{"operation": "CREATE", "resource": map[string]any{"resource": tc.Resource}, "userInfo": map[string]any{"username": "system:serviceaccount:tenant-home-nextcloud-config:nextcloud-deployer"}}, "variables": vars}
			evaluate := func(source string, variable bool) (any, error) {
				r := compiler.CompileCELExpression(expression{source, variable}, admissioncel.OptionalVariableDeclarations{}, environment.NewExpressions)
				if r.Error != nil {
					t.Fatalf("compile: %s: %v", source, r.Error)
				}
				value, _, err := r.Program.ContextEval(context.Background(), bindings)
				if err != nil {
					return nil, err
				}
				return value, nil
			}
			for _, v := range p.Spec.Variables {
				value, err := evaluate(v.Expression, true)
				if err != nil {
					t.Fatal(err)
				}
				vars[v.Name] = value
			}
			allowed := true
			for _, v := range p.Spec.Validations {
				value, err := evaluate(v.Expression, false)
				if err != nil {
					allowed = false
					continue
				}
				if value.(interface{ Value() any }).Value() != true {
					allowed = false
				}
			}
			if allowed != tc.Allowed {
				t.Fatalf("allowed=%v want=%v", allowed, tc.Allowed)
			}
		})
	}
}
