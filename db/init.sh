#!/bin/bash

set -e

POSTGRES_USER="postgres"
DB_NAME="growbies"

echo "Switching to the ${POSTGRES_USER} user."
su postgres -c \
  "createuser $(whoami) 2>/dev/null || true && \
   echo 'Created role: $(whoami)' && \
   createdb growbies --owner=$(whoami) 2>/dev/null || true && \
   echo 'Created database: ${DB_NAME}'"

psql -d ${DB_NAME} -f init_tables.sql

