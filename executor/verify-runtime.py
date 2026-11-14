#!/usr/bin/env python3
"""Read-only bounded provenance/projection checks; private receipt-directory guard."""
import hashlib,json,os,re,stat,sys,importlib.util
from pathlib import Path

def bounded(path, limit):
    fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK)
    try:
        s=os.fstat(fd)
        if not stat.S_ISREG(s.st_mode) or s.st_size>limit: raise ValueError('invalid file')
        data=os.read(fd,limit+1)
        if len(data)>limit: raise ValueError('oversized file')
        return data
    finally: os.close(fd)

def projected(path, root, limit):
    p=Path(path); r=Path(root)
    if r.is_symlink() or not r.is_dir(): raise ValueError('invalid projection root')
    real=p.resolve(strict=True)
    if not real.is_relative_to(r) or real==r: raise ValueError('projection escape')
    return bounded(str(real),limit)

if __name__=='__main__':
    try:
        if len(sys.argv)==3 and sys.argv[1]=='--receipt':
            context=sys.argv[2]
            if not re.fullmatch('[a-z][a-z0-9-]{0,30}',context):raise ValueError()
            root=Path('/receipts')
            if root.is_symlink() or not root.is_dir():raise ValueError()
            p=root/context
            try:p.mkdir(mode=0o700)
            except FileExistsError:pass
            s=p.lstat()
            if not stat.S_ISDIR(s.st_mode) or s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)!=0o700:raise ValueError()
            lock=p/'trigger.lock'
            if lock.exists() or lock.is_symlink():
                s=lock.lstat()
                if not stat.S_ISREG(s.st_mode) or s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)!=0o600 or s.st_nlink!=1:raise ValueError()
        else:
            enrollment,platform,context,digest,work=sys.argv[1:]
            rev=json.loads(bounded('/opt/revisions.json',4096))
            if rev!={'enrollment':enrollment,'platform':platform}:raise ValueError('revision mismatch')
            selection=json.loads(bounded('/opt/enrollment/contracts/tenant-identity-v1.json',65536))
            if selection['platformRevision']!=platform or context not in selection['contexts']:raise ValueError('selection mismatch')
            data=projected('/inputs/inputs.yaml','/inputs',65536)
            if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('input digest mismatch')
            w=Path(work); st=w.lstat()
            if not re.fullmatch(r'/tmp/identity\.[A-Za-z0-9]+',work) or not stat.S_ISDIR(st.st_mode) or st.st_uid!=os.getuid() or stat.S_IMODE(st.st_mode)!=0o700:raise ValueError('private stage')
            def stage(name, value):
                fd=os.open(w/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                try:
                    with os.fdopen(fd,'wb',closefd=False) as f:f.write(value);f.flush();os.fsync(f.fileno())
                finally:os.close(fd)
            stage('inputs.yaml',data)
            # Reuse pinned literal JSON-only adapter schema BEFORE Ansible or credentials.
            spec=importlib.util.spec_from_file_location('groupguard','/opt/platform/big-bang-bootstrap/configuration/packages/gitlab/enrollment/verify_group_paths.py')
            guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
            selected=guard.validate_inputs(str(w/'inputs.yaml'))
            if selected['gitlab_group_context']!=context or selected['gitlab_group_source_revision']!=enrollment or selected['gitlab_group_run'] is not True or selected.get('gitlab_group_allow_parent_create',False) is not False or type(selected.get('gitlab_group_expected_parent_id')) is not int or selected['gitlab_group_expected_parent_id']<=0 or selected['gitlab_native_ca_file']!='/credentials/ca.crt':raise ValueError('group input binding')
            token=projected('/credentials/group-writer','/credentials',4096)
            if not token or b'\n' in token or b'\r' in token:raise ValueError('token format')
            ca=projected('/credentials/ca.crt','/credentials',65536)
            if not ca:raise ValueError('CA empty')
            stage('token',token);stage('ca.crt',ca)
    except Exception:
        print('Executor preflight rejected; no provider call made.',file=sys.stderr)
        sys.exit(2)
