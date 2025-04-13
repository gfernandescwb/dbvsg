import json
import psycopg2.extras
from dbvsg.core import DBVSG
from dbvsg.mods.diff import diff as vsg_diff

def setup_dbvsg():
    vsg = DBVSG()
    db_url = "postgresql://admin:secret@localhost:5433/demo"
    vsg.conn(db_url, user_context=lambda: "example_user")
    return vsg

def reset_table(vsg, table):
    with vsg.connection.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {table}")
        cur.execute(f"CREATE TABLE {table} (id SERIAL PRIMARY KEY, name TEXT)")
        cur.execute("DELETE FROM db_vsg WHERE meta->>'table' = %s", (table,))
    vsg.connection.commit()

def insert_commit(vsg, name, table, parent_uuid=None):
    query = f"INSERT INTO {table} (name) VALUES ('{name}') RETURNING id"
    return vsg.ops(query=query, operation="INSERT", table=table, parent_uuid=parent_uuid)

def get_last_commit_uuid(vsg, table):
    with vsg.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT uuid FROM db_vsg WHERE meta->>'table' = %s ORDER BY created_at DESC LIMIT 1", (table,))
        return cur.fetchone()["uuid"]

def test_all_operations():
    vsg = setup_dbvsg()
    table = "clients"
    reset_table(vsg, table)

    print("[INSERT] Base: Alpha")
    insert_commit(vsg, "Alpha", table)
    alpha_uuid = get_last_commit_uuid(vsg, table)

    print("[CHECKOUT] Alpha")
    vsg.checkout(alpha_uuid)
    checkout_uuid = get_last_commit_uuid(vsg, table)

    print("[INSERT] Branch: Beta")
    try:
        insert_commit(vsg, "Beta", table, parent_uuid=checkout_uuid)
    except Exception as e:
        print("[ERROR] Conflict:", e)

    print("[ROLLBACK] to HEAD")
    rollback_id = vsg.rollback()
    print("Rollback UUID:", rollback_id)

    print("[MERGE] Alpha into HEAD")
    try:
        vsg.merge(alpha_uuid)
        print("Merge successful")
    except Exception as e:
        print("[ERROR] Merge failed:", e)

    print("[RESTORE] Alpha")
    vsg.restore(alpha_uuid)

    print("[LOGS]")
    logs = vsg.logs(table=table, limit=10)
    for log in logs:
        print(log["uuid"], log["operation"], log["created_at"])

    print("[DIFF] Alpha ↔ HEAD")
    head_uuid = get_last_commit_uuid(vsg, table)
    print(json.dumps(vsg_diff(vsg, alpha_uuid, head_uuid), indent=2))

if __name__ == "__main__":
    test_all_operations()
