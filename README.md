# DBVSG - Database Versioning Snapshot

**DBVSG** is a SQL table versioning engine that functions like Git. Each database mutation creates a full snapshot of the table state and is stored as an auditable and traceable commit, with rollback, restore, merge, checkout, and diff capabilities.

It enforces linear history through parent-child tracking (`parent_uuid`) and prevents divergence unless explicitly resolved through merge.

<br />

## Features

- Full snapshot of table state on every INSERT/UPDATE/DELETE
- Audit trail with SHA256 hash, timestamp, user and UUID
- Linear commit history using `parent_uuid`
- Only one `is_current = TRUE` per table (HEAD)
- Git-style operations:
  - `commit`, `checkout`, `rollback`, `merge`, `restore`
- Detects and prevents conflicting commits
- Visual `diff` support between any two commits
- Designed for PostgreSQL 13+

<br />

## How It Works

On every call to `dbvsg.ops(...)`:

1. The SQL is executed, and `RETURNING id` retrieves the new record's ID
2. The current version (`is_current = TRUE`) is fetched
3. If the commit isn't based on the current `parent_uuid`, a conflict is raised
4. The full table state is captured as `state`
5. The commit (blob) is registered in the audit table `db_vsg`
6. All other versions are marked `is_current = FALSE`

Each blob contains:
- `before`, `after`, and full `state`
- Metadata with `record_id`, `table`, and `parent_uuid`
- Timestamp, operation, hash and user_id

<br />

## File Structure

```
dbvsg/
├── core.py                   # Main DBVSG class
├── mods/                     # Modular operations
│   ├── ops.py                # Core commit logic
│   ├── rollback.py           # Creates rollback commits
│   ├── restore.py            # Reverts table without commit
│   ├── merge.py              # Merges two snapshots
│   ├── checkout.py           # Checkout + commit
│   ├── logs.py               # Git-style log viewer
│   ├── diff.py               # Table diff between commits
│   ├── delete.py             # Soft delete commit
│   └── ensure_table.py       # Creates `db_vsg` table
├── sql/                      # External SQL queries
│   ├── insert_audit.sql
│   ├── rollback.sql
│   ├── not_current.sql
│   ├── new_version.sql
│   └── create_table.sql
├── utils/
│   ├── logger.py             # Logs to file
│   └── read_sql.py           # SQL file reader
```

<br />

## Usage

### Install

```bash
git clone https://github.com/your-org/dbvsg.git
cd dbvsg
pip install -e .
```

Requirements:

- Python 3.11+
- PostgreSQL (locally or via Docker)
- `psycopg2` or `psycopg[binary]`

<br />

### Simple Insert Commit

```python
from dbvsg.core import DBVSG

dbvsg = DBVSG()
dbvsg.conn("postgresql://admin:secret@localhost:5432/demo")

query = "INSERT INTO clients (name) VALUES ('John') RETURNING id"
dbvsg.ops(query=query, operation="INSERT", table="clients")
```

<br />

## Docker Setup

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: demo
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secret
    ports:
      - "5433:5432"
    volumes:
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
```

To run:

```bash
docker-compose up -d
```

<br />

## Example Script

### `main.py`

```python
from dbvsg.core import DBVSG

dbvsg = DBVSG()
dbvsg.conn("postgresql://admin:secret@localhost:5432/demo")

# Insert
dbvsg.ops("INSERT INTO clients (name) VALUES ('Alpha') RETURNING id", "INSERT", "clients")

# Checkout
dbvsg.checkout(vsg.logs("clients")[0]["uuid"])

# Merge, Rollback, Restore
dbvsg.rollback()
dbvsg.merge(uuid_from_old_commit)
dbvsg.restore(uuid_from_old_commit)

# Diff
diff = dbvsg.diff(uuid1, uuid2)
print(diff)
```

<br />

## Full Test Script

```bash
chmod +x examples/test_vsg_flow.sh
./examples/test_vsg_flow.sh
```

Tests:

- Inserts
- Rollbacks and checkouts
- Conflict detection
- Diff between states
- Merge divergent branches

<br />

## Audit Table Schema

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

<br />

## Logs Example

```json
[
  {
    "uuid": "abc123...",
    "operation": "INSERT",
    "user_id": "system",
    "created_at": "2025-04-13T17:36:39Z",
    "is_current": true
  }
]
```

<br />

## Coming Soon

- Git-like CLI (e.g. `vsg commit`, `vsg diff`, `vsg checkout`)
- TUI interface with `Rich`
- Graphviz DAG rendering
- ORM adapters

<br />

## Contributing

- PRs welcome
- Submit issues or ideas in Discussions
- Follow Git conventions and prefer modular PRs

<br />

## License

MIT — use freely, but maintain integrity.

<br />
