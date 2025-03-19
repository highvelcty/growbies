from pathlib import Path
import shlex
import subprocess

def get_git_repo_root() -> Path:
    cmd = 'git rev-parse --show-toplevel'
    proc = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, encoding='utf-8')
    return Path(proc.stdout.strip())

