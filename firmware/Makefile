default: esp32c3 mini uno

clean:
	platformio run -t clean

# Base boards
esp32c3:
	platformio run -e esp32c3

mini:
	platformio run -e mini

uno:
	platformio run -e uno

# Base board uploads
upload-esp32c3:
	platformio run -t upload -e esp32c3

upload-mini:
	platformio run -t upload -e mini

upload-uno:
	platformio run -t upload -e uno

# esp32 variants
circle-esp32c3: BUILD_FLAGS=BUILD_TARGET_CIRCLE
circle-esp32c3: esp32c3

square-esp32c3: BUILD_FLAGS=BUILD_TARGET_SQUARE
square-esp32c3: esp32c3

# esp32 variant uploads
upload-circle-esp32c3: BUILD_FLAGS=BUILD_TARGET_CIRCLE
upload-circle-esp32c3: upload-esp32c3

upload-square-esp32c3: BUILD_FLAGS=BUILD_TARGET_SQUARE
upload-square-esp32c3: upload-esp32c3


all: esp32c3 mini uno circle-esp32c3 square-esp32c3
