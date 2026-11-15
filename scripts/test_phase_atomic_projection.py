"""Real filesystem AtomicWriter layout against exact extracted runtime functions."""
import ast,errno,os,pathlib,stat,tempfile,unittest
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[1]
source=(ROOT/'executor/run-phase.py').read_text();tree=ast.parse(source)
ns={'os':os,'stat':stat,'Path':pathlib.Path}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('bounded','projection')],type_ignores=[]),'run-phase.py','exec'),ns)
class AtomicProjection(unittest.TestCase):
 def layout(self,root,payload=b'{}'):
  v=root/'..2026_11_15';v.mkdir();(v/'revisions.json').write_bytes(payload);(root/'..data').symlink_to(v.name);(root/'revisions.json').symlink_to('..data/revisions.json');return v
 def test_native_layout_and_old_failure(self):
  with tempfile.TemporaryDirectory() as d:
   r=pathlib.Path(d);self.layout(r)
   with self.assertRaises(OSError) as e:ns['bounded'](r/'revisions.json',4096)
   self.assertEqual(e.exception.errno,errno.ELOOP)
   self.assertEqual(ns['projection'](str(r),'revisions.json',4096),b'{}')
   self.assertIn("projection('/opt','revisions.json',4096)",source)
   self.assertNotIn("bounded('/opt/",source)
 def test_escape_root_and_final_replacement(self):
  with tempfile.TemporaryDirectory() as d:
   outer=pathlib.Path(d);r=outer/'mount';r.mkdir();v=self.layout(r);(outer/'outside').write_bytes(b'foreign')
   (r/'revisions.json').unlink();(r/'revisions.json').symlink_to(outer/'outside')
   with self.assertRaises(ValueError):ns['projection'](str(r),'revisions.json',4096)
   (r/'revisions.json').unlink();(r/'revisions.json').symlink_to('..data/revisions.json')
   alias=outer/'alias';alias.symlink_to(r)
   with self.assertRaises(ValueError):ns['projection'](str(alias),'revisions.json',4096)
   original=ns['bounded']
   def swap(p,n):
    p.unlink();p.symlink_to(outer/'outside');return original(p,n)
   with mock.patch.dict(ns,{'bounded':swap}):
    with self.assertRaises(OSError):ns['projection'](str(r),'revisions.json',4096)
 def test_nonregular_oversize_and_broken(self):
  for kind in ('fifo','directory','oversize','broken'):
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as d:
    r=pathlib.Path(d);v=self.layout(r);f=v/'revisions.json';f.unlink()
    if kind=='fifo':os.mkfifo(f)
    elif kind=='directory':f.mkdir()
    elif kind=='oversize':f.write_bytes(b'x'*4097)
    with self.assertRaises((ValueError,OSError)):ns['projection'](str(r),'revisions.json',4096)
if __name__=='__main__':unittest.main()
