Git clone this repo: 
https://github.com/tesseract-ocr/tesstrain

Training commands:

```commandline
# make training TESSDATA=/usr/share/tessdata/ START_MODEL=eng MODEL_NAME=scale MAX_ITERATIONS=5000 PSM=13
```
where PSM=13 is described as "Raw line. Treat the image as a single text line,
       bypassing hacks that are Tesseract-specific."

