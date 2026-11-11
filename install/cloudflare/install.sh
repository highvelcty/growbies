#!/bin/bash

# Known hostnames
#
# - norlong-db.growbies.net
#

set -e

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 HOSTNAME"
    exit 1
fi

HOSTNAME="$1"

if [[ -z "$HOSTNAME" ]]; then
    echo "Error: HOSTNAME cannot be empty."
    exit 1
fi

# Install credentials file.
install -d -o root -g root -m 700 /etc/growbies

install -o root -g root -m 600 \
    cloudflare.env /etc/growbies/cloudflare.env

# Install systemd service with hostname substitution.
sed "s|@@HOSTNAME@@|${HOSTNAME}|g" growbies-db-proxy.service | \
    install -o root -g root -m 644 /dev/stdin \
    /etc/systemd/system/growbies-db-proxy.service

# Enable and start service.
systemctl daemon-reload
systemctl enable growbies-db-proxy

echo "Created and enabled the growbies-db-proxy systemd service."
echo "Created /etc/growbies/cloudflare.env."
echo "Please populate it with your Cloudflare Access Service Token credentials."
echo "Start the service with `systemctl start growbies-db-proxy`"
echo "Connect to the database proxy via 127.0.0.1:15432"
