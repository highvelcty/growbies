default: package

# ?= means to assign only if undefined
CONTAINER ?= growbies_build

INTERNAL_WORKDIR = /code
REPO_ROOT := $(shell git rev-parse --show-toplevel || true)
# Build and source the exported paths
$(REPO_ROOT)/build/paths.env:
	make export_paths -C ${REPO_ROOT}
include $(REPO_ROOT)/build/paths.env

run_cmd = podman run --tty --interactive --rm \
	--volume ${REPO_ROOT}/${PATH_PKG_DEB}:${INTERNAL_WORKDIR}

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
		bash -c "mkdir -p $${path} && \
		         mv /growbies*.deb $${path}/ && \
				 cd $${path} \
				 && dpkg-scanpackages --multiversion . | xz > Packages.xz;"; \
	)


start:
	${run_cmd} --detach --name ${CONTAINER} ${CONTAINER}

stop:
	podman container exec -it ${CONTAINER} systemctl halt
