container_name = growbies_build

git_root := $(shell git rev-parse --show-toplevel)
INTERNAL_REPO_ROOT = /code
run_cmd = podman run --tty --interactive \
	--volume=${git_root}:${INTERNAL_REPO_ROOT} \
	${container_name}

default: package

clean: container
	( \
		${run_cmd} debian/rules -e clean; \
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

package: container
	( \
		${run_cmd} debuild --preserve-env -b \
		--no-sign \
		--lintian-opts --allow-root; \
	)
