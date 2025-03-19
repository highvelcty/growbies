container_name = growbies_build

REPO_ROOT := $(shell git rev-parse --show-toplevel)
INTERNAL_REPO_ROOT = /code

run_cmd = podman run --tty --interactive \
	--volume=${REPO_ROOT}:${INTERNAL_REPO_ROOT} \
	${container_name}

path_to_build_package = $(dpkg-parsechangelog -S Source)

default: package

clean:
	( \
		rm -f debian/*.substvars; \
		rm -rf debian/files; \
#		rm -rf "debian/${path_to_build_package}"; \
	)

container:
	( \
		podman build \
		 	--env REPO_ROOT=${INTERNAL_REPO_ROOT} \
			--tag ${container_name} .; \
	)

enter: container
	( \
		${run_cmd} /bin/bash; \
	)

export_paths:
	make --environment-overrides export_paths -C "${REPO_ROOT}"

package: container export_paths
	( \
		${run_cmd} debuild --preserve-env -b \
		--no-sign \
		--lintian-opts --allow-root; \
	)
