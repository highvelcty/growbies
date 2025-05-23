default: package

# ?= means to assign only if undefined
CONTAINER ?= growbies_build
REPO_ROOT ?= $(shell git rev-parse --show-toplevel || true)

# Build and source the exported paths
$(REPO_ROOT)/build/paths.env:
	make export_paths -C ${REPO_ROOT}
PATHS_ENV=$(REPO_ROOT)/build/paths.env
include ${PATHS_ENV}

src_watch = $(shell find ${PATH_DEBIAN_SRC_GROWBIES} -type f -name '*' 2>/dev/null || true)
src_watch += $(shell find ${PATH_DEBIAN_SRC_PKG_BASH_SRC} -type f -name '*' 2>/dev/null || true)

INTERNAL_WORKDIR = /code
PATH_DIST = $(shell basename ${PATH_PKG_DEB_DIST})

run_cmd = podman run --tty --interactive --rm \
	--volume ${REPO_ROOT}/${PATH_PKG_DEB}:${INTERNAL_WORKDIR}

external_build: start $(PATH_DIST)
	make deb_src_copy -C "${REPO_ROOT}"
	$(MAKE) ${PATH_DIST}

internal_build:
	( \
		set -e; \
		PATHS_ENV=${PATHS_ENV} debuild --preserve-env -b --no-sign --lintian-opts --allow-root; \
		mkdir -p ${PATH_DIST}; \
		mv /growbies*.deb ${PATH_DIST}/; \
		cd ${PATH_DIST}; \
		dpkg-scanpackages --multiversion . | xz > Packages.xz; \
		apt reinstall -y ./growbies*.deb; \
	)

package:
	make deb_src_copy -C "${REPO_ROOT}"
	podman build \
		--volume ${REPO_ROOT}/${PATH_PKG_DEB}:${INTERNAL_WORKDIR} \
		--tag ${CONTAINER} \
		--build-arg PATH_CODE=${INTERNAL_WORKDIR} \
		.

${PATH_DIST}: $(src_watch)
	podman container exec -it --env REPO_ROOT=${INTERNAL_WORKDIR}/${PATH_DEBIAN_SRC} ${CONTAINER} \
		make internal_build

enter: start
	podman exec -it ${CONTAINER} /bin/bash

restart:
	( \
		if podman container exists ${CONTAINER}; then \
		  podman restart ${CONTAINER}; \
		else \
		  $(MAKE) start; \
	  fi; \
	)

start:
	( \
		if ! podman container exists ${CONTAINER}; then \
			${run_cmd} --detach --name ${CONTAINER} ${CONTAINER}; \
		fi; \
	)

stop:
	( \
		if podman container exists ${CONTAINER}; then \
	  		podman container exec -it ${CONTAINER} systemctl halt; \
		fi; \
	)

