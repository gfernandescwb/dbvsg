INSERT INTO db_vsg (
    uuid, operation, query, meta,
    hash, user_id, blob,
    rollbacked_from, is_current,
    is_deleted, deleted_by, deleted_at
) VALUES (
    %(uuid)s, %(operation)s, %(query)s, %(meta)s,
    %(hash)s, %(user_id)s, %(blob)s,
    %(rollbacked_from)s, TRUE,
    FALSE, NULL, NULL
);
