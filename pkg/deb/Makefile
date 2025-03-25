container_name = growbies_build

REPO_ROOT := $(shell git rev-parse --show-toplevel)
INTERNAL_REPO_ROOT = /code

run_cmd = podman run --tty --interactive --rm \
	--volume=${REPO_ROOT}:${INTERNAL_REPO_ROOT}

$(shell REPO_ROOT=${REPO_ROOT} python3 -m build_lib.export_paths || false)
include ${REPO_ROOT}/build/paths.env

default: package

clean:
	make clean_pkg -C ${REPO_ROOT}

image:
	( \
		make deb_src_copy -C "${REPO_ROOT}"; \
		podman build \
		 	--env REPO_ROOT=${INTERNAL_REPO_ROOT} \
			--tag ${container_name} .; \
	)
#		tar cf - --exclude="$(basename "${PATH_PKG_DEB_DEBIAN}")" . | (cd "${PATH_DEBIAN_TMP}"; \
#		&& tar xf -)
#		podman build \
#		 	--env INTERNAL_REPO_ROOT=${INTERNAL_REPO_ROOT} \
#			--tag ${container_name} -f .; \


enter: image
		podman exec -it ${container_name} /bin/bash

export_paths:
	make --environment-overrides export_paths -C "${REPO_ROOT}"

start:
	( \
		${run_cmd} --detach --name ${container_name} ${container_name}; \
#		podman exec -it growbies_build /bin/bash -c "apt install /code/pkg/*.deb"; \
#		podman exec -it ${container_name} systemctl enable growbies; \
	)

stop:
	podman container exec -it ${container_name} systemctl halt

package: image
	( \
		${run_cmd} ${container_name} debuild --preserve-env -b \
		--no-sign \
		--lintian-opts --allow-root; \
	)
