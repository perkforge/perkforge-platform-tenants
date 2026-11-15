"""Synthetic-only AtomicWriter topology; caller supplies disposable fixture roots."""
import pathlib,os,tempfile

def publish(root,files):
 root=pathlib.Path(root);root.mkdir(exist_ok=True)
 if root.is_symlink():raise ValueError('fixture root symlink')
 for name in files:
  p=pathlib.PurePosixPath(name)
  if p.is_absolute() or '..' in p.parts or any(x.startswith('..') for x in p.parts):raise ValueError('fixture path')
 version=pathlib.Path(tempfile.mkdtemp(prefix='..fixture-',dir=root))
 for name,data in files.items():
  p=version/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data.encode() if isinstance(data,str) else data);p.chmod(0o755)
 for p in root.iterdir():
  if p.name.startswith('..'):continue
  if not p.is_symlink():raise ValueError('refuse nonprojection fixture content')
  p.unlink()
 tmp=root/'..data_tmp';tmp.symlink_to(version.name);os.replace(tmp,root/'..data')
 for top in sorted({pathlib.PurePosixPath(x).parts[0] for x in files}):(root/top).symlink_to('..data/'+top)
