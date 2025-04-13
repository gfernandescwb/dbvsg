INSERT INTO db_vsg (
    uuid, operation, query, meta,
    hash, user_id, blob,
    parent_uuid, is_current,
    rollbacked, is_deleted, created_at
) VALUES (
    %(uuid)s, %(operation)s, %(query)s, %(meta)s,
    %(hash)s, %(user_id)s, %(blob)s,
    %(parent_uuid)s, %(is_current)s,
    %(rollbacked)s, %(is_deleted)s, %(created_at)s
);
