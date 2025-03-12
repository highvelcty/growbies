container_name = gateway_build
git_root := $(shell git rev-parse --show-toplevel)
path_to_build_sh = /code/gateway/deb/build.sh
run_cmd = podman run --tty --interactive --volume=${git_root}:/code ${container_name}

default: package

container:
	( \
		podman build --tag ${container_name} .; \
	)

enter: container
	( \
		${run_cmd} /bin/bash; \
	)

package: container
	( \
		podman run --volume=${git_root}:/code ${container_name} ${path_to_build_sh}; \
	)
