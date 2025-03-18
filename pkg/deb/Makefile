container_name = growbies_build
git_root := $(shell git rev-parse --show-toplevel)
run_cmd = podman run --tty --interactive --volume=${git_root}:/code ${container_name}

default: package

clean: container
	( \
		${run_cmd} debian/rules clean; \
	)

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
		${run_cmd} debuild -b \
		--no-sign \
		--lintian-opts --allow-root; \
	)
