#!/bin/bash
set -e

echo "Waiting 1s before checking PostgreSQL readiness..."
sleep 1

python <<EOF
import os
import time
import psycopg2

MAX_RETRIES = 30
RETRY_INTERVAL = 1

for i in range(MAX_RETRIES):
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host="db",
            port=5432
        )
        conn.close()
        print("PostgreSQL is ready.")
        break
    except Exception as e:
        print(f"Attempt {i + 1}/{MAX_RETRIES} failed: {e}")
        time.sleep(RETRY_INTERVAL)
else:
    print("PostgreSQL did not become ready in time.")
    exit(1)
EOF

echo "Starting Flask app..."
exec flask run --host=0.0.0.0 --port=5000
