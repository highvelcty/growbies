#!/usr/bin/env python
from growbies.utils import paths

path_to_output = paths.Paths.BUILD_PATHS_ENV.value
path_to_output.parent.mkdir(parents=True, exist_ok=True)
with open(path_to_output, 'w') as outf:
    for path in paths.Paths:
        outf.write(f'PATH_{path.name}={path.value}\n')
    outf.write('\n\n')
