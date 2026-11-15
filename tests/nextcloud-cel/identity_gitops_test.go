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
 admissioncel "k8s.io/apiserver/pkg/admission/plugin/cel"
 "k8s.io/apiserver/pkg/admission/plugin/policy/validating"
 "k8s.io/apiserver/pkg/cel/environment"
)
func TestIdentityGitopsOwnership(t *testing.T){
 raw,err:=exec.Command("python3","../../scripts/identity_gitops_cases.py").CombinedOutput();if err!=nil{t.Fatalf("%s %v",raw,err)}
 var f struct{Policies []admissionv1.ValidatingAdmissionPolicy;Cases []struct{Name,Policy string;Object map[string]any;Allowed bool}}
 if err=json.Unmarshal(raw,&f);err!=nil{t.Fatal(err)}
 b,err:=os.ReadFile(os.Getenv("NEXTCLOUD_OPENAPI"));if err!=nil{t.Fatal(err)}
 var schemas struct{Definitions fixtureSchemas};if err=json.Unmarshal(b,&schemas);err!=nil{t.Fatal(err)}
 mapper:=meta.NewDefaultRESTMapper(nil);for _,kind:=range []string{"Role","RoleBinding"}{mapper.Add(schema.GroupVersionKind{Group:"rbac.authorization.k8s.io",Version:"v1",Kind:kind},meta.RESTScopeNamespace)}
 checker:=validating.TypeChecker{SchemaResolver:schemas.Definitions,RestMapper:mapper};compiler:=admissioncel.NewCompiler(environment.MustBaseEnvSet(version.MajorMinor(1,36)))
 policies:=map[string]admissionv1.ValidatingAdmissionPolicy{}
 for _,p:=range f.Policies{policies[p.Name]=p;if w:=checker.Check(&p);len(w)>0{t.Errorf("%s: %+v",p.Name,w)}}
 for _,tc:=range f.Cases{t.Run(tc.Name,func(t *testing.T){allowed:=true;p:=policies[tc.Policy]
  for _,v:=range p.Spec.Validations{r:=compiler.CompileCELExpression(expression{v.Expression,false},admissioncel.OptionalVariableDeclarations{},environment.NewExpressions);if r.Error!=nil{t.Fatal(r.Error)};value,_,err:=r.Program.ContextEval(context.Background(),map[string]any{"object":tc.Object,"oldObject":nil,"request":map[string]any{"operation":"UPDATE","userInfo":map[string]any{"username":"system:serviceaccount:flux-system:platform-reconciler"}},"namespaceObject":nil});if err!=nil || value.Value()!=true{allowed=false}}
  if allowed!=tc.Allowed{t.Fatalf("allowed=%v expected=%v",allowed,tc.Allowed)}
 })}
}
