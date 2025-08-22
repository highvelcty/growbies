#!/usr/bin/env python
import subprocess

from growbies.utils import paths

def _get_git_hash() -> str:
    """Return the short Git hash of the current commit, or 'unknown' if not in a Git repo."""
    git_hash = (
        subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL, encoding='utf-8')
        .strip()
    )
    return git_hash

with open(paths.DebianPaths.DEBIAN_SRC_GROWBIES_INIT.value, 'r') as inf:
    lines = inf.readlines()

with open(paths.DebianPaths.DEBIAN_SRC_GROWBIES_INIT.value, 'w') as outf:
    for line in lines:
        if line.startswith('__version__'):
            line = line.strip()
            if line.endswith('"'):
                quote = '"'
            elif line.endswith("'"):
                quote = "'"

            line = line.rstrip(quote)
            line = line.split('+')[0]
            line = f'{line}+{_get_git_hash()}{quote}\n'
        outf.write(line)
