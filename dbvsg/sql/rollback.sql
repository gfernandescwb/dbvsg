INSERT INTO db_vsg (
    uuid, operation, query, meta,
    hash, user_id, blob,
    rollbacked_from, parent_uuid,
    is_current, is_deleted, created_at
) VALUES (
    %(uuid)s, %(operation)s, %(query)s, %(meta)s,
    %(hash)s, %(user_id)s, %(blob)s,
    %(rollbacked_from)s, %(parent_uuid)s,
    TRUE, FALSE, CURRENT_TIMESTAMP
);
