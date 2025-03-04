from pathlib import Path
from typing import TextIO
import logging

from growbies.constants import INDENT
from growbies.session import Session
from growbies.utils.filelock import FileLock

logger = logging.getLogger(__name__)

def _truncate_for_new_data(outf: TextIO):
    idx = outf.tell()
    while True:
        idx = max(0, idx - 1)
        outf.seek(idx)
        read_char = outf.read(1)
        if read_char == '\n':
            outf.seek(idx)
            outf.truncate()
            return True
        else:
            if idx == 0:
                logger.warning('Did not find a comma in the file.')
                return False

def add_value_to_last_line(path: Path, value: int):
    with (FileLock(), open(path, 'a+') as outf):
        if _truncate_for_new_data(outf):
            outf.write(f',{value}\n')
            print(f"{INDENT}{value} written to last row's column.")

def main(sess: Session):
    try:
        while True:
            human_input = input('Enter value ("del" to delete last):')
            try:
                value = int(human_input)
            except ValueError:
                logger.info('Invalid input - cannot convert to an integer. Please try again.')
                continue

            add_value_to_last_line(sess.path_to_data, value)
    except KeyboardInterrupt:
        pass
