CREATE TABLE IF NOT EXISTS db_vsg (
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
    parent_uuid UUID,
    rollbacked_from UUID,
    blob TEXT NOT NULL
);
