#!/usr/bin/env python3

from pathlib import Path
import cv2
import os, argparse

import pytesseract
from PIL import Image

model_name = 'mm'
path = Path(f'/home/meyer/code/tesstrain/data/{model_name}-ground-truth')

# This will attempt to an optical character recognition (OCR) conversion for a folder full of
# .png, comparing it to tesseract formed data.
def ocr_tesseract_comparison_dir(directory: Path = path):
    correct = 0
    incorrect = 0
    for filename in directory.iterdir():
        if filename.suffix == '.png':
            with open(filename.with_suffix('.gt.txt'), 'r') as inf:
                exp = inf.read()
                exp = exp.strip()
            print(filename)
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
            print(f'exp: "{exp}" obs: "{text}"')
    print(f'rate: {(correct/(correct + incorrect))*100}%')
