CREATE TABLE IF NOT EXISTS db_vsg (
    uuid UUID PRIMARY KEY,
    operation TEXT NOT NULL,
    query TEXT NOT NULL,
    meta JSON,
    hash TEXT NOT NULL,
    user_id TEXT NOT NULL,
    blob TEXT NOT NULL,
    parent_uuid UUID,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    rollbacked BOOLEAN NOT NULL DEFAULT FALSE,
    rollbacked_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_by TEXT
);
