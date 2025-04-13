#!/bin/bash
set -e

echo "Create client 1"
curl -s -X POST http://localhost:5000/clients -H "Content-Type: application/json" -d '{"name": "Client 1"}' | jq

echo "Create client 2"
curl -s -X POST http://localhost:5000/clients -H "Content-Type: application/json" -d '{"name": "Client 2"}' | jq

echo "Show commits"
curl -s "http://localhost:5000/vsg/logs?table=clients&limit=5" | jq

echo "Get current UUID"
UUID=$(curl -s "http://localhost:5000/vsg/logs?table=clients&limit=1" | jq -r '.[0].uuid')

echo "CHECKOUT to UUID $UUID"
curl -s -X POST http://localhost:5000/vsg/checkout/$UUID | jq

echo "ROLLBACK"
curl -s -X POST http://localhost:5000/vsg/rollback | jq

echo "RESTORE with UUID $UUID"
curl -s -X POST http://localhost:5000/vsg/restore/$UUID | jq

echo "MERGE with UUID $UUID"
curl -s -X POST http://localhost:5000/vsg/merge/$UUID | jq
