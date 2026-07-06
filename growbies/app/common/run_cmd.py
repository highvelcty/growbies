import shlex, subprocess

from growbies.session import log

logger = log.get_logger(__name__)

def run_cmd(cmd, check=False) -> tuple[int, str, str]:
    for line in cmd.splitlines():
        logger.log(log.STDIN_LEVEL, line)
    try:
        proc = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=check, encoding='utf-8')
    except (subprocess.CalledProcessError, FileNotFoundError) as err:
        logger.exception("Command failed")

        if getattr(err, 'stdout', None):
            for line in err.stdout.splitlines():
                logger.log(log.STDOUT_LEVEL, line)

        if getattr(err, 'stderr', None):
            for line in err.stderr.splitlines():
                logger.log(log.STDERR_LEVEL, line)

        raise
    else:
        if proc.stdout:
            for line in proc.stdout.splitlines():
                logger.log(log.STDOUT_LEVEL, line)
        if proc.stderr:
            for line in proc.stderr.splitlines():
                logger.log(log.STDERR_LEVEL, line)
        return proc.returncode, proc.stdout, proc.stderr
