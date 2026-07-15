clean:
	platformio run -t clean

# ============================================================================
# Generic rules
# ============================================================================

_build:
	MODEL_NUMBER=$(MODEL) platformio run -e $(ENV)

_upload: _build
	PORT=$${PORT:-/dev/ttyACM0}; \
	MODEL_NUMBER=$(MODEL) platformio run \
		-e $(ENV) \
		-t upload \
		-t nobuild \
		--upload-port $$PORT

_upload-all: _build
	FAIL=0; \
	for PORT in /dev/ttyACM*; do \
		if [ -e "$$PORT" ]; then \
			MODEL_NUMBER=$(MODEL) platformio run \
				-e $(ENV) \
				-t upload \
				-t nobuild \
				--upload-port $$PORT || FAIL=1; \
		fi; \
	done; \
	exit $$FAIL


# ============================================================================
# Scale products
# ============================================================================

circle-1: ENV=scale
circle-1: MODEL=circle-1
circle-1: _build

upload-circle-1: ENV=scale
upload-circle-1: MODEL=circle-1
upload-circle-1: _upload

upload-all-circle-1: ENV=scale
upload-all-circle-1: MODEL=circle-1
upload-all-circle-1: _upload-all


circle-2: ENV=scale
circle-2: MODEL=circle-2
circle-2: _build

upload-circle-2: ENV=scale
upload-circle-2: MODEL=circle-2
upload-circle-2: _upload

upload-all-circle-2: ENV=scale
upload-all-circle-2: MODEL=circle-2
upload-all-circle-2: _upload-all


# ============================================================================
# Thermal chamber products
# ============================================================================

thermal-chamber-1: ENV=thermal
thermal-chamber-1: MODEL=thermal-chamber-1
thermal-chamber-1: _build

upload-thermal-chamber-1: ENV=thermal
upload-thermal-chamber-1: MODEL=thermal-chamber-1
upload-thermal-chamber-1: _upload

upload-all-thermal-chamber-1: ENV=thermal
upload-all-thermal-chamber-1: MODEL=thermal-chamber-1
upload-all-thermal-chamber-1: _upload-all