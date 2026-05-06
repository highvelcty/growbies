clean:
	platformio run -t clean

# Generic build rule for all environments
_build-%:
	# Extract the last token after the last hyphen
	MODEL_NUMBER=$* platformio run -e $(lastword $(subst -, ,$*))

# Generic upload rule
_upload-%:
	MODEL_NUMBER=$* platformio run -t upload -e $(lastword $(subst -, ,$*))

_upload-all-%:
	@ENV=$(lastword $(subst -, ,$*)); \
	FAIL=0; \
	for PORT in /dev/ttyACM*; do \
		if [ -e "$$PORT" ]; then \
			echo "Uploading $$* to $$PORT using env $$ENV"; \
			MODEL_NUMBER=$* platformio run -t upload -e $$ENV --upload-port $$PORT || FAIL=1; \
		fi \
	done; \
	exit $$FAIL

_upload-all-parallel-%:
	@ENV=$(lastword $(subst -, ,$*)); \
	echo "Building $$ENV once..."; \
	MODEL_NUMBER=$* platformio run -e $$ENV || exit 1; \
	for PORT in /dev/ttyACM*; do \
		if [ -e "$$PORT" ]; then \
			echo "Starting upload to $$PORT"; \
			( MODEL_NUMBER=$* platformio run -t upload -e $$ENV --upload-port $$PORT ) & \
		fi \
	done; \
	wait; \
	echo "All uploads complete."

esp32c3: _build-esp32c3
upload-esp32c32: _upload-esp32c3
upload-all-circle-esp32c3: _upload-all-circle-esp32c3
upload-all-parallel-circle-esp32c3: _upload-all-parallel-circle-esp32c3

mini: _build-mini
upload-mini: _upload-mini

uno: _build-uno
upload-uno: _upload-uno

circle-esp32c3: _build-circle-esp32c3
upload-circle-esp32c3: _upload-circle-esp32c3

square-esp32c3: _build-square-esp32c3
upload-square: _upload-square-esp32c3
