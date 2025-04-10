default: package

# ?= means to assign only if undefined
CONTAINER ?= growbies_build
REPO_ROOT ?= $(shell git rev-parse --show-toplevel || true)

# Build and source the exported paths
$(REPO_ROOT)/build/paths.env:
	make export_paths -C ${REPO_ROOT}
PATHS_ENV=$(REPO_ROOT)/build/paths.env
include ${PATHS_ENV}

src_watch = $(shell find ${PATH_DEBIAN_SRC_GROWBIES} \
	-type f -name '*' 2>/dev/null || true)
src_watch += $(shell find ${PATH_DEBIAN_SRC_PKG_BASH_SRC} \
	-type f -name '*' 2>/dev/null || true)

#src_watch = $(shell find ${PATH_DEBIAN_SRC}/${PATH_GROWBIES} \
#	-type f -name '*' 2>/dev/null || true)
#src_watch += $(shell find ${PATH_DEBIAN_SRC}/${PATH_PKG_BASH_SRC} \
#	-type f -name '*' 2>/dev/null || true)

INTERNAL_WORKDIR = /code
PATH_DIST = $(shell basename ${PATH_PKG_DEB_DIST})

run_cmd = podman run --tty --interactive --rm \
	--volume ${REPO_ROOT}/${PATH_PKG_DEB}:${INTERNAL_WORKDIR}

external_build: $(PATH_DIST)
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
		systemctl enable growbies; \
		systemctl enable growbies; \
		systemctl enable postgresql; \
	)

${PATH_DIST}: $(src_watch)
	podman container exec -it --env REPO_ROOT=/code/debian/src ${CONTAINER} make internal_build

image:
	make deb_src_copy -C "${REPO_ROOT}"
	podman build \
		--volume ${REPO_ROOT}/${PATH_PKG_DEB}:${INTERNAL_WORKDIR} \
		--tag ${CONTAINER} \
		--build-arg PATH_CODE=${INTERNAL_WORKDIR} \
		.

enter:
	podman exec -it ${CONTAINER} /bin/bash

export_paths:
	make --environment-overrides export_paths -C "${REPO_ROOT}"

package: image
	( \
	path=$$(basename ${PATH_PKG_DEB_DIST}); \
	${run_cmd} ${CONTAINER} \
		bash -c "mkdir -p $${path}   && \
		         mv /growbies*.deb $${path}/ && \
				 cd $${path} \
				 && dpkg-scanpackages --multiversion . | xz > Packages.xz;"; \
	)

start:
	${run_cmd} --detach --name ${CONTAINER} ${CONTAINER}

stop:
	podman container exec -it ${CONTAINER} systemctl halt
