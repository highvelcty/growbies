from pathlib import Path
import os
import pwd
import re
import shlex
import subprocess

from . import constants
from growbies.constants import APPNAME

def _add_trusted_user_to_pg_conf(path_to_conf):
    to_be_inserted = f"""\

# {APPNAME}
local   {constants.DB_USER}        {constants.DB_NAME}                                trust
"""
    with open(path_to_conf, 'r') as inf:
        buffer = inf.readlines()
        for line in buffer:
            line = line.strip()
            if line.startswith('#'):
                continue
            if re.search(fr'local\s+{constants.DB_NAME}\s+{constants.DB_USER}\s+trust', line):
                return

    columns = ['type', 'database', 'user', 'address', 'method']
    for idx, line in enumerate(buffer):
        line = line.lower()
        tokens = line.split()
        if all(c in tokens for c in columns):
            buffer.insert(idx+1, to_be_inserted)
            break

    with open(path_to_conf, 'w') as outf:
        outf.write(''.join(buffer))

def _create_stuff(cmd: str):
    proc = _run_as_user(cmd, constants.ADMIN_DB_USER)
    stdout = proc.stdout.read()
    stderr = proc.stderr.read()
    if proc.returncode != 0:
        if re.search(f'{constants.DB_USER}.*exists', stderr):
            pass
        else:
            raise subprocess.CalledProcessError(proc.returncode, cmd, stdout, stderr)

def _create_db():
    cmd = f'createdb {constants.DB_NAME} --owner={constants.DB_USER}'
    _create_stuff(cmd)

def _create_user():
    cmd = f'createuser {constants.DB_USER}'
    _create_stuff(cmd)

def _run_as_user(cmd: str, user: str):
    pw_record = pwd.getpwnam(user)
    user_uid = pw_record.pw_uid
    user_gid = pw_record.pw_gid

    def preexec_fn():
        os.setgid(user_gid)
        os.setuid(user_uid)

    proc = subprocess.Popen(shlex.split(cmd), preexec_fn=preexec_fn,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    proc.wait()
    return proc

def _get_pg_hba_conf_path():
    cmd = 'psql -c "show hba_file;"'
    user = constants.ADMIN_DB_USER
    proc = _run_as_user(cmd, user)

    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, proc.stdout.read(),
                                            proc.stderr.read())

    for line in proc.stdout.readlines():
        line = line.strip()
        if os.sep in line:
            path = Path(line)
            if path.exists():
                return path
    raise FileNotFoundError(f'Unable to resolve the path to the postgres configuration file.')

def _reload_service():
    cmd = f'systemctl reload {constants.RDBMS_SERVICE}'
    subprocess.run(shlex.split(cmd), check=True)

def init_db_and_user():
    _create_user()
    _create_db()
    path_to_conf = _get_pg_hba_conf_path()
    _add_trusted_user_to_pg_conf(path_to_conf)
    _reload_service()
