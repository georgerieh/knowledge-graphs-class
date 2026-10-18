#!/bin/sh
set -e

if [ "$CLEAN" = "1" ]; then
    echo "Unzip parameter detected. Unzipping neo4j database files  ..."
    
    tar -xvf /app/neo4j.tar.gz
    
    echo "Unzip completed successfully."
else
    echo "No unzip parameter provided. Skipping."
fi

exec "$@"