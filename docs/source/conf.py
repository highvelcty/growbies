import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common_conf import *

# --- Sphinx Multiversion
smv_branch_whitelist = r'^docs/manual-.*$'