#/usr/bin/env python
from pathlib import Path
import os, subprocess, shlex

# These constructs come from platformio
Import("env")
build_name = env["PIOENV"]

# Forward any externally defined build flags into the platformio build flags.
flags = os.environ.get("BUILD_FLAGS")
if flags:
    env.Append(CPPFLAGS=flags.split())

# Generate and include build time configuration
os.environ['PIOENV'] = build_name
cmd = "python -m build_lib.build_cfg firmware"
subprocess.run(shlex.split(cmd), check=True, cwd=Path('..'), env=os.environ)


