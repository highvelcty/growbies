container_name = growbies_build

REPO_ROOT := $(shell git rev-parse --show-toplevel || true)

run_cmd = podman run --tty --interactive --rm

default: image

image:
	make deb_src_copy -C "${REPO_ROOT}"
	podman build --tag ${container_name} .

enter:
	podman exec -it ${container_name} /bin/bash

export_paths:
	make --environment-overrides export_paths -C "${REPO_ROOT}"

start:
	${run_cmd} --detach --systemd=always --name ${container_name} ${container_name}

stop:
	podman container exec -it ${container_name} systemctl halt
