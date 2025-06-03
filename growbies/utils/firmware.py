import shlex
import subprocess

from growbies.utils.paths import RepoPaths

def make_upload_mini():
    cmd = f'make -C {RepoPaths.ENDPOINT_ARDUINO.value} upload-mini'
    subprocess.run(shlex.split(cmd), check=True)
