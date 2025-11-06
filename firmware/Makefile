clean:
	platformio run -t clean

# Generic build rule for all environments
_build-%:
	# Extract the last token after the last hyphen
	MODEL_NUMBER=$* platformio run -e $(lastword $(subst -, ,$*))

# Generic upload rule
_upload-%:
	MODEL_NUMBER=$* platformio run -t upload -e $(lastword $(subst -, ,$*))

esp32c3: _build-esp32c3
upload-esp32c32: _upload-esp32c3

mini: _build-mini
upload-mini: _upload-mini

uno: _build-uno
upload-uno: _upload-uno

circle-esp32c3: _build-circle-esp32c3
upload-circle-esp32c3: _upload-circle-esp32c3

square-esp32c3: _build-square-esp32c3
upload-square: _upload-square-esp32c3
