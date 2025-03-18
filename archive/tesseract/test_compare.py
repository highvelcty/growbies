#!/usr/bin/env python3
import enum
from pathlib import Path
import sys

import pytesseract
from PIL import Image

class Models(enum.StrEnum):
    # Multi-meter
    MM = 'mm'
    SCALE = 'scale'

# This will attempt to an optical character recognition (OCR) conversion for a folder full of
# .png, comparing it to tesseract formed data.
def ocr_tesseract_comparison_dir(model_name):
    path = Path(f'/home/meyer/code/tesstrain/data/{model_name}-ground-truth')
    correct = 0
    incorrect = 0
    iteration = 1
    files = list(path for path in path.iterdir() if path.suffix == '.png')
    # Init the file
    with open(f'/home/meyer/tmp/{model_name}.err', 'w'): pass
    for filename in files:
        if filename.suffix == '.png':
            with open(filename.with_suffix('.gt.txt'), 'r') as inf:
                exp = inf.read()
                exp = exp.strip()
            print(f'{iteration} / {len(files)}')
            img = Image.open(filename)
            config = f"-l {model_name} --oem 1 --psm 13"
            #
            # See also:
            #   text = pytesseract.image_to_data(img, config=config,
            #                                     output_type=pytesseract.Output.DICT)
            #
            text = pytesseract.image_to_string(img, config=config).strip()
            if exp == text:
                correct += 1
            else:
                incorrect += 1
                msg = (f'miscompare @ {filename}:\n'
                       f'exp: {exp}\n'
                       f'obs: {text}\n')
                print(msg)
                with open(f'/home/meyer/tmp/{model_name}.err', 'a') as outf:
                    outf.write(msg)

            iteration += 1

    print(f'\nGrade for model "{model_name}": {(correct/(correct + incorrect))*100}%')

if __name__ == '__main__':
    ocr_tesseract_comparison_dir(*sys.argv[1:])