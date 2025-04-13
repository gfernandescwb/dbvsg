# DBVSG - Database Versioning Snapshot

**DBVSG** is a version control system for SQL tables that functions like Git — each operation creates a snapshot of the entire table state. It enables commits, rollbacks, checkouts, restores, and merges with complete traceability and integrity enforcement. Only one version can be marked as "current" at any given time, just like a Git `HEAD`.

<br/>

## Features

- Full table snapshot stored on every change (INSERT, UPDATE, DELETE)
- Conflict prevention based on parent commit reference (`parent_uuid`)
- Rollback to previous versions as new commits
- Restore a historical version without creating a commit
- Checkout a version and commit it as a new head
- Merge divergent versions into the current one
- Audit log with user, timestamp, UUID and hash
- Git-style `state`, `before`, and `after` comparison
- Only one `is_current = true` per table

<br/>

## How It Works

When `vsg.ops(...)` is executed:

1. The raw SQL is executed and the inserted record's `id` is retrieved
2. The current version (`is_current = TRUE`) is fetched
3. If the operation is based on a version that is not the current one, it is rejected (conflict)
4. A snapshot of the entire table is taken
5. The operation is recorded in the audit table (`db_vsg`) with metadata and full blob
6. The new version becomes `is_current`, and previous versions are unmarked

Each commit stores:
- `before`: table state before the change
- `after`: table state after the change
- `state`: the full table at this version
- `meta`: JSON metadata with `record_id`, `table`, and `parent`

<br/>

## Supported Operations

| Method               | Description                                        |
|----------------------|----------------------------------------------------|
| `vsg.ops(...)`       | Executes a write query and saves full snapshot     |
| `vsg.rollback()`     | Commits a previous state as a new version          |
| `vsg.restore(uuid)`  | Restores a previous version (no commit)            |
| `vsg.merge(uuid)`    | Merges a previous version into the current version |
| `vsg.checkout(uuid)` | Restores a version and commits it as current       |
| `vsg.logs(table)`    | Lists all commits for a given table                |

> Commits are rejected if not based on the current `HEAD` version, ensuring linear history unless explicitly merged.

<br/>

## Installation

```bash
git clone https://github.com/your-org/dbvsg.git
cd dbvsg
pip install -e .
```

**Requirements:**
- Python 3.11+
- PostgreSQL 13+
- `psycopg2`
- Optional: Flask (for example usage)

<br/>

## Audit Table Schema (`db_vsg`)

```sql
CREATE TABLE db_vsg (
    uuid UUID PRIMARY KEY,
    operation TEXT NOT NULL,
    query TEXT NOT NULL,
    meta JSON,
    hash TEXT NOT NULL,
    user_id TEXT NOT NULL,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    parent_uuid UUID,
    rollbacked BOOLEAN NOT NULL DEFAULT FALSE,
    rollbacked_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_by TEXT,
    blob TEXT NOT NULL
);
```

<br/>

## Example Usage

```python
# INSERT with version tracking
query = "INSERT INTO clients (name) VALUES ('John') RETURNING id"
vsg.ops(query=query, operation="INSERT", table="clients")
```

<br/>

## REST API (Flask Demo)

| Method | Endpoint                | Description                            |
|--------|-------------------------|----------------------------------------|
| POST   | `/clients`              | Creates client and registers snapshot  |
| GET    | `/clients`              | Lists all clients                      |
| GET    | `/vsg/logs?table=...`   | Shows Git-style log for a table        |
| POST   | `/vsg/rollback`         | Rollback to latest version             |
| POST   | `/vsg/rollback/<uuid>`  | Rollback to specific version           |
| POST   | `/vsg/restore/<uuid>`   | Restore a snapshot (no commit)         |
| POST   | `/vsg/merge/<uuid>`     | Merge snapshot into current            |
| POST   | `/vsg/checkout/<uuid>`  | Restore and create new commit          |

<br/>

## Example Log Output

```json
[
  {
    "uuid": "91ffc25d-...",
    "operation": "INSERT",
    "user_id": "system",
    "created_at": "2025-04-13T17:36:39.978181+00:00",
    "is_current": true
  }
]
```

<br/>

## Test Script

```bash
chmod +x examples/test_vsg_flow.sh
./examples/test_vsg_flow.sh
```

This script validates:

- Insert operations and snapshot generation
- Checkout and rollback behaviors
- Merge mechanics
- Conflict detection (simulated users with divergent histories)

<br/>

## Contributing

- PRs welcome for support of migrations, GraphQL integration, Graphviz tree rendering
- Coming soon: `vsg diff <uuid1> <uuid2>` for visual diff of table state

<br/>

## License

MIT License – use freely, audit responsibly.

<br />
