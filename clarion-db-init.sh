#!/bin/bash

CONTAINER_NAME="clariondb"
POSTGRES_PASSWORD="mysecretpassword"
DB_NAME="clarion"
DUMP_FILE="clarion.sql"
DATA_DIR="$(pwd)/postgres_data"
# PG_UID=$(id -u) 
# PG_GID=$(id -g)

mkdir -p "$DATA_DIR" || { echo "Cannot create data directory"; exit 1; }
# chown -R $PG_UID:$PG_GID $DATA_DIR

echo "Starting PostgreSQL container..."
podman run --name $CONTAINER_NAME \
    -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    -p 5432:5432 \
    -v $DATA_DIR:/var/lib/postgresql/data:Z \
    -d docker.io/library/postgres:17

echo "Waiting for PostgreSQL to be ready..."
until podman exec "$CONTAINER_NAME" pg_isready -U postgres > /dev/null 2>&1; do
    echo "PostgreSQL is not ready yet, waiting..."
    sleep 3
done

echo "PostgreSQL is now ready!"

echo "Copying the database dump file into the container..."
podman cp "$DUMP_FILE" "$CONTAINER_NAME":/tmp/"$DUMP_FILE"

echo "Creating missing database role..."
podman exec -it "$CONTAINER_NAME" psql -U postgres -c "CREATE ROLE clarion WITH LOGIN CREATEDB PASSWORD 'clarionpassword';"

echo "Creating the database if it doesn't exist..."
podman exec -it "$CONTAINER_NAME" psql -U postgres -c "CREATE DATABASE $DB_NAME OWNER clarion;"

echo "Importing the database dump..."
podman exec -it "$CONTAINER_NAME" psql -U clarion -d "$DB_NAME" -f /tmp/"$DUMP_FILE"

echo "✅ PostgreSQL container is running with persistent storage at $DATA_DIR"