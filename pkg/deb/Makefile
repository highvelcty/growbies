container_name = growbies_build

REPO_ROOT := $(shell git rev-parse --show-toplevel || true)
INTERNAL_REPO_ROOT = /code

run_cmd = podman run --tty --interactive --rm \
	--volume=${REPO_ROOT}:${INTERNAL_REPO_ROOT}

default: package

image:
	( \
		make deb_src_copy -C "${REPO_ROOT}"; \
		podman build \
		 	--env REPO_ROOT=${INTERNAL_REPO_ROOT} \
			--tag ${container_name} .; \
	)

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
