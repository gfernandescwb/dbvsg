# DBVSG - Database Versioning Snapshot Git

DBVSG is a database versioning and auditing system that works like Git for SQL tables. Each write operation creates a snapshot (commit) of the table's full state, allowing rollback, merge, restore, and checkout operations — all with full traceability.

---

## Features

- Full version control for insert/update/delete operations
- Snapshot of the entire table state on every change
- Rollback to any previous version
- Merge a historical state into the current one
- Checkout a version and register it as a new commit
- Track user, timestamp, and operation metadata
- Only one current version per table (like Git HEAD)
- Soft delete with recovery support

---

## How It Works

When calling `vsg.ops(...)`, the system:

1. Executes the provided SQL query
2. Captures the full state of the table before and after the operation
3. Registers the operation in `db_vsg` as a versioned commit
4. Marks this version as the current one and clears previous current flags
5. Stores metadata (user, operation, UUID, timestamp, SHA256 hash)

Each version includes:
- `before` state
- `after` state
- `state` snapshot (the full table at that point)
- Metadata in JSON format

---

## Supported Operations

| Method               | Description                                      |
|----------------------|--------------------------------------------------|
| `vsg.ops(...)`       | Executes a query and registers a version         |
| `vsg.rollback()`     | Creates a new version based on the previous state|
| `vsg.restore(uuid)`  | Restores a version without creating a new commit |
| `vsg.merge(uuid)`    | Merges another version and creates a new one     |
| `vsg.checkout(uuid)` | Restores and commits a new version               |
| `vsg.logs(...)`      | Lists versioned commits for a table              |

---

## Installation

```bash
git clone https://github.com/your-org/dbvsg.git
cd dbvsg
pip install -e .
```

Requirements:
- Python 3.11+
- PostgreSQL
- psycopg2
- Flask (example app)

---

## Table Schema: `db_vsg`

```sql
CREATE TABLE db_vsg (
    uuid UUID PRIMARY KEY,
    operation TEXT NOT NULL,
    query TEXT NOT NULL,
    meta JSON,
    hash TEXT NOT NULL,
    user_id TEXT NOT NULL,
    is_current BOOLEAN DEFAULT TRUE,
    rollbacked BOOLEAN DEFAULT FALSE,
    rollbacked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_by TEXT,
    blob TEXT NOT NULL
);
```

---

## Example (Flask)

```python
@main.route('/clients', methods=['POST'])
def create_client():
    data = request.get_json()
    name = data['name']
    query = f"INSERT INTO clients (name) VALUES ('{name}') RETURNING id"
    new_id = vsg.ops(query=query, operation="INSERT", table="clients")
    return jsonify({'id': new_id, 'name': name}), 201
```

---

## API Endpoints (REST)

| Method | Path                    | Description                            |
|--------|-------------------------|----------------------------------------|
| POST   | `/clients`              | Create a client and audit              |
| GET    | `/clients`              | List all clients                       |
| GET    | `/audit/clients`        | Raw audit log                          |
| GET    | `/vsg/logs?table=...`   | Git-style log for a table              |
| POST   | `/vsg/rollback`         | Rollback to current                    |
| POST   | `/vsg/rollback/<uuid>`  | Rollback to specific UUID              |
| POST   | `/vsg/restore/<uuid>`   | Restore table to a version             |
| POST   | `/vsg/merge/<uuid>`     | Merge a version into current           |
| POST   | `/vsg/checkout/<uuid>`  | Restore and register as new version    |

---

## Log Output Example

```json
[
  {
    "uuid": "2ad7801f-...",
    "operation": "INSERT",
    "user_id": "system",
    "created_at": "2025-04-13T17:59:30.004162+00:00",
    "is_current": true
  }
]
```

---

## Test Script

Run the following to test the full versioning lifecycle:

```bash
chmod +x examples/test_vsg_flow.sh
./examples/test_vsg_flow.sh
```

This script tests:
- Insertions
- Log reading
- Checkout
- Rollback
- Restore
- Merge

---

## License

MIT License

---

## Author

Gabriel Fernandes OSS/ACC — Software Developer and

```
