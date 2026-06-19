clean:
	platformio run -t clean

# Generic build rule for all environments
_build-%:
	# Extract the last token after the last hyphen
	MODEL_NUMBER=$* platformio run -e esp32c3

_upload-%: _build-%
	PORT=$${PORT:-/dev/ttyACM0}; \
	MODEL_NUMBER=$* platformio run -t upload -e esp32c3 -t nobuild --upload-port $$PORT

_upload-all-%: _build-%
	FAIL=0; \
	for PORT in /dev/ttyACM*; do \
		if [ -e "$$PORT" ]; then \
			MODEL_NUMBER=$* platformio run -t upload -e esp32c3 -t nobuild --upload-port $$PORT || FAIL=1; \
		fi \
	done; \
	exit $$FAIL

circle-1: _build-circle-1
upload-circle-1: _upload-circle-1
upload-all-circle-1: _upload-all-circle-1

circle-2: _build-circle-2
upload-circle-2: _upload-circle-2
upload-all-circle-2: _upload-all-circle-2
