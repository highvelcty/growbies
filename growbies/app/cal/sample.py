from argparse import Namespace
import time

from .cli import Action, SampleAction, MassSampleParam, TempSSampleParam
from growbies.app.common.run_cmd import run_cmd
from growbies.session import log
from growbies.common.utils import timestamp

logger = log.get_logger(__name__)

def _sample(count: int, forward_args: str, check):
    cmd = f'growbies read {forward_args}'
    run_cmd(f'{cmd} --reset', check=check)
    for ii in range(count - 1):
        run_cmd(cmd, check=check)


def sample_for_mass_cal(args: Namespace, forward_args: str):
    count = getattr(args, MassSampleParam.COUNT)
    _sample(count, forward_args, check=True)

def sample_for_thermal_cal(args: Namespace, forward_args: str):
    count = getattr(args, MassSampleParam.COUNT)
    interval = getattr(args, TempSSampleParam.INTERVAL)
    if '--ref-mass' not in forward_args:
        forward_args = f'{forward_args} --ref-mass 0'
    if '--sensor-ref-mass' not in forward_args:
        forward_args = f'{forward_args} --sensor-ref-mass 0 0 0'
    try:
        samples = 0
        iterations = 0
        startt = time.time()
        while True:
            _sample(count, forward_args, check=False)
            samples += count
            iterations += 1
            logger.log(log.STDOUT_LEVEL,
                       f'\nElapsed: {timestamp.get_elapsed_str(int(time.time()-startt))}\n'
                       f'Iterations: {iterations}\n'
                       f'Samples: {samples}\n'
                       f'Interval: {interval}\n'
                       f'Count / Interval: {count}')
            time.sleep(interval)
    except KeyboardInterrupt:
        pass

def execute(args: Namespace, forward_args: list[str]):
    sample_type = getattr(args, Action.SAMPLE)

    if sample_type == SampleAction.MASS:
        sample_for_mass_cal(args, ' '.join(forward_args))
    elif sample_type == SampleAction.TEMP:
        sample_for_thermal_cal(args, ' '.join(forward_args))

    logger.info('*** PASS ***')
