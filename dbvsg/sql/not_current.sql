UPDATE db_vsg
SET is_current = FALSE
WHERE is_current = TRUE AND meta->>'table' = %(table)s;
