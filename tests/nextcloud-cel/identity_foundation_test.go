package nextcloudcel
import (
 "context"
 "encoding/json"
 "os"
 "os/exec"
 "testing"
 admissionv1 "k8s.io/api/admissionregistration/v1"
 "k8s.io/apimachinery/pkg/api/meta"
 "k8s.io/apimachinery/pkg/runtime/schema"
 "k8s.io/apimachinery/pkg/util/version"
 utilvalidation "k8s.io/apimachinery/pkg/util/validation"
 admissioncel "k8s.io/apiserver/pkg/admission/plugin/cel"
 "k8s.io/apiserver/pkg/admission/plugin/policy/validating"
 "k8s.io/apiserver/pkg/cel/environment"
)
func TestIdentityFoundation(t *testing.T){
 raw,err:=exec.Command("python3","../../scripts/identity_foundation_cases.py").CombinedOutput();if err!=nil{t.Fatalf("%s %v",raw,err)}
 var f struct{Policies []admissionv1.ValidatingAdmissionPolicy;Schemas fixtureSchemas;Cases []struct{Name,Policy,Username,Operation string;Object,OldObject map[string]any;Allowed bool}}
 if err=json.Unmarshal(raw,&f);err!=nil{t.Fatal(err)}
 path:=os.Getenv("NEXTCLOUD_OPENAPI");if path==""{t.Fatal("exact native OpenAPI required")};b,err:=os.ReadFile(path);if err!=nil{t.Fatal(err)}
 var schemas struct{Definitions fixtureSchemas};if err=json.Unmarshal(b,&schemas);err!=nil{t.Fatal(err)}
 for k,v:=range f.Schemas{schemas.Definitions[k]=v};mapper:=meta.NewDefaultRESTMapper(nil);mapper.Add(schema.GroupVersionKind{Group:"kustomize.toolkit.fluxcd.io",Version:"v1",Kind:"Kustomization"},meta.RESTScopeNamespace);mapper.Add(schema.GroupVersionKind{Group:"batch",Version:"v1",Kind:"Job"},meta.RESTScopeNamespace);mapper.Add(schema.GroupVersionKind{Group:"",Version:"v1",Kind:"Pod"},meta.RESTScopeNamespace);mapper.Add(schema.GroupVersionKind{Group:"",Version:"v1",Kind:"ConfigMap"},meta.RESTScopeNamespace)
 checker:=validating.TypeChecker{SchemaResolver:schemas.Definitions,RestMapper:mapper}
 compiler:=admissioncel.NewCompiler(environment.MustBaseEnvSet(version.MajorMinor(1,36)))
 policies:=map[string]admissionv1.ValidatingAdmissionPolicy{}
 for _,p:=range f.Policies {policies[p.Name]=p;if w:=checker.Check(&p);len(w)>0{t.Errorf("%s: %+v",p.Name,w)}}
 // RKE2 1.36 live OpenAPI v3 Quantity is oneOf string/number, not v2 string.
 // It makes typed CEL omit Quantity-bearing fields: preserve guards via narrow dyn parents.
 quantity:=schemas.Definitions["io.k8s.apimachinery.pkg.api.resource.Quantity"]
 if err=json.Unmarshal([]byte(`{"oneOf":[{"type":"string"},{"type":"number"}]}`),&quantity);err!=nil{t.Fatal(err)}
 quantity.Type=nil
 schemas.Definitions["io.k8s.apimachinery.pkg.api.resource.Quantity"]=quantity
 for _,p:=range f.Policies{if w:=checker.Check(&p);len(w)>0{t.Errorf("live-v3 %s: %+v",p.Name,w)}}
 for _,tc:=range f.Cases{t.Run(tc.Name,func(t *testing.T){allowed:=true;p:=policies[tc.Policy];if tc.Username==""{tc.Username="system:serviceaccount:flux-system:identity-group-reconciler"};if tc.Operation==""{tc.Operation="CREATE"}
  for _,v:=range p.Spec.Validations{r:=compiler.CompileCELExpression(expression{v.Expression,false},admissioncel.OptionalVariableDeclarations{},environment.NewExpressions);if r.Error!=nil{t.Fatal(r.Error)}
   value,_,err:=r.Program.ContextEval(context.Background(),map[string]any{"object":tc.Object,"oldObject":tc.OldObject,"request":map[string]any{"operation":tc.Operation,"userInfo":map[string]any{"username":tc.Username}},"namespaceObject":nil});if err!=nil || value.Value()!=true{allowed=false}}
  if tc.Allowed && tc.Object["kind"] == "Job" {name:=tc.Object["metadata"].(map[string]any)["name"].(string);if errors:=utilvalidation.IsValidLabelValue(name);len(errors)>0{t.Fatalf("Job controller label invalid: %s %v",name,errors)}}
  if allowed!=tc.Allowed{t.Fatalf("allowed=%v expected=%v",allowed,tc.Allowed)}
 })}
}
