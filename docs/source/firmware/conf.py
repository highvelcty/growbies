import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common_conf import *

# --- Sphinx Multiversion
smv_branch_whitelist = r'^docs/firmware-.*$'

print('DEBUG: firmware conf.py loaded')
print(f'DEBUG: smv_branch_whitelist = {smv_branch_whitelist!r}')
print(f'DEBUG: extensions = {extensions!r}')