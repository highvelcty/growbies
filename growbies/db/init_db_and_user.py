import os
import pwd
import re
import shlex
import subprocess

from growbies import constants

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

def _reload_service():
    cmd = f'systemctl reload {constants.RDBMS_SERVICE}'
    subprocess.run(shlex.split(cmd), check=True)

def init_db_and_user():
    _create_user()
    _create_db()
    _reload_service()
