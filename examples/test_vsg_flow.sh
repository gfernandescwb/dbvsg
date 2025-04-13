#!/bin/bash
set -e

echo "Creating base record"
curl -s -X POST http://localhost:5000/clients \
    -H "Content-Type: application/json" \
    -d '{"name": "Ancestor"}' | jq

echo "Getting UUID of base commit"
UUID=$(curl -s "http://localhost:5000/vsg/logs?table=clients&limit=1" | jq -r '.[0].uuid')
echo "Base UUID: $UUID"

echo "Performing checkout (simulates user A holding this base)"
curl -s -X POST http://localhost:5000/vsg/checkout/$UUID | jq

echo "Modifying record with Client A (will become current)"
curl -s -X POST http://localhost:5000/clients \
    -H "Content-Type: application/json" \
    -d '{"name": "Client A"}' | jq

echo "Restoring to old base again (simulates user B using outdated base)"
curl -s -X POST http://localhost:5000/vsg/restore/$UUID | jq

echo "User B tries to write a new commit based on outdated base (should fail)"
curl -s -X POST http://localhost:5000/clients \
    -H "Content-Type: application/json" \
    -d '{"name": "Client B"}' | jq

echo "Final table state:"
curl -s http://localhost:5000/clients | jq

echo "Final commit log:"
curl -s "http://localhost:5000/vsg/logs?table=clients&limit=10" | jq
