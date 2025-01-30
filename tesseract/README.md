Git clone this repo: 
https://github.com/tesseract-ocr/tesstrain

Level 1 training
----------------
```commandline
make training TESSDATA=/usr/share/tessdata/ START_MODEL=eng MODEL_NAME=scale PSM=13
```
where PSM=13 is described as "Raw line. Treat the image as a single text line,
       bypassing hacks that are Tesseract-specific."

Other models, are ``mm`` for "multi-meter" and ``scale`` for a digital kitchen scale output.


Level 2 training
----------------
```commandline
make training TESSDATA=/usr/share/tessdata/ START_MODEL=scale MODEL_NAME=scale PSM=13
make training TESSDATA=/usr/share/tessdata/ START_MODEL=mm MODEL_NAME=mm PSM=13
```