default: build

# ?= means to assign only if undefined
IMAGE_NAME ?= growbies_build
CONTAINER_NAME ?= $(IMAGE_NAME)
REPO_ROOT ?= $(shell git rev-parse --show-toplevel || true)

# Build and source the exported paths
$(REPO_ROOT)/build/paths.env:
	make export_paths -C ${REPO_ROOT}
PATHS_ENV=$(REPO_ROOT)/build/paths.env
include ${PATHS_ENV}

src_watch := $(shell find ${PATH_DEBIAN_SRC_GROWBIES} -type f \
    			-not -path "*/__pycache__/*" \
    			-not -name "*.pyc")
src_watch += $(shell find ${PATH_DEBIAN_SRC_PKG_BASH_SRC} -type f -name '*' 2>/dev/null || true)

INTERNAL_WORKDIR = /code
PATH_DIST = $(shell basename ${PATH_PKG_DEB_DIST})

run_cmd = podman run --tty --interactive --rm \
 	$(shell ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null | sed 's|^|--device=|') \
	--volume ${REPO_ROOT}/${PATH_PKG_DEB}:${INTERNAL_WORKDIR}

build: image start $(PATH_DIST)
	$(MAKE) ${PATH_DIST}

clean-%: stop
clean-source:
	make clean -C "${REPO_ROOT}"
clean-image:
	podman rmi -f "${IMAGE_NAME}"
clean: clean-source clean-image

internal_build:
	( \
		set -ex; \
		PATHS_ENV=${PATHS_ENV} debuild --preserve-env -b --no-sign --lintian-opts --allow-root; \
		mkdir -p ${PATH_DIST}; \
		mv /growbies*.deb ${PATH_DIST}/; \
		cd ${PATH_DIST}; \
		dpkg-scanpackages --multiversion . | xz > Packages.xz; \
		apt remove -y ${PATH_APPNAME} 2>/dev/null || true; \
		apt install -y ./${PATH_APPNAME}*.deb; \
	)

image:
	( \
		make deb_src_copy -C "${REPO_ROOT}"; \
		podman build \
			--volume ${REPO_ROOT}/${PATH_PKG_DEB}:${INTERNAL_WORKDIR} \
			--tag ${IMAGE_NAME} \
			--build-arg PATH_CODE=${INTERNAL_WORKDIR} \
			.; \
	)

${PATH_DIST}: $(src_watch)
	podman container exec -it --env REPO_ROOT=${INTERNAL_WORKDIR}/${PATH_DEBIAN_SRC} \
		${CONTAINER_NAME} \
		make internal_build

#enter: start
#	podman exec -it ${CONTAINER_NAME} /bin/bash

enter: start
	podman exec -it ${CONTAINER_NAME} /bin/bash -c "\
		source ${PATH_USR_LIB_GROWBIES_VENV_ACTIVATE} && \
		exec bash \
	"


restart:
	( \
		if podman container exists ${CONTAINER_NAME}; then \
		  podman restart ${CONTAINER_NAME}; \
		else \
		  $(MAKE) start; \
	  fi; \
	)

start:
	( \
		if ! podman container exists ${CONTAINER_NAME}; then \
			${run_cmd} --detach --name ${IMAGE_NAME} ${CONTAINER_NAME}; \
		fi; \
	)

stop:
	( \
		if podman container exists ${CONTAINER_NAME}; then \
	  		podman container exec -it ${CONTAINER_NAME} systemctl halt; \
		fi; \
	)

