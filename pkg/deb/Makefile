default: package-dist
container_name = growbies_build

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
		--tag ${container_name} \
		--build-arg PATH_CODE=${INTERNAL_WORKDIR} \
		.

enter:
	podman exec -it ${container_name} /bin/bash

export_paths:
	make --environment-overrides export_paths -C "${REPO_ROOT}"

package-dist:
package-repo:
package-%: image
	${run_cmd} ${container_name} \
		bash -c "mv /growbies*.deb ${*} && \
				 cd ${*} \
				 && dpkg-scanpackages --multiversion . | xz > Packages.xz;"; \


start:
	${run_cmd} --detach --name ${container_name} ${container_name}

stop:
	podman container exec -it ${container_name} systemctl halt
