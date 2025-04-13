from flask import Blueprint, request, jsonify
from app import vsg
from .models import Client
import psycopg2.extras
from uuid import uuid4
from dbvsg.utils.read_sql import load_sql
import json
from datetime import datetime, timezone

main = Blueprint('main', __name__)

@main.route('/clients', methods=['GET'])
def list_clients():
    clients = Client.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in clients])

@main.route('/clients', methods=['POST'])
def create_client():
    data = request.get_json()
    name = data['name']
    try:
        query = f"INSERT INTO clients (name) VALUES ('{name}') RETURNING id"
        new_id = vsg.ops(query=query, operation="INSERT", table="clients")
        return jsonify({'id': new_id, 'name': name}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/audit/clients', methods=['GET'])
def audit_clients():
    try:
        with vsg.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM db_vsg WHERE meta->>'table' = 'clients' ORDER BY created_at DESC")
            logs = cur.fetchall()
        return jsonify(logs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/vsg/rollback', methods=['POST'])
@main.route('/vsg/rollback/<uuid>', methods=['POST'])
def vsg_rollback(uuid=None):
    try:
        result = vsg.rollback(target_uuid=uuid)
        return jsonify({'rollbacked_to': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/vsg/restore/<uuid>', methods=['POST'])
def vsg_restore(uuid):
    try:
        result = vsg.restore(uuid)
        return jsonify({'restored': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/vsg/merge/<uuid>', methods=['POST'])
def vsg_merge(uuid):
    try:
        result = vsg.merge(incoming_uuid=uuid)
        return jsonify({'merged_as': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/vsg/checkout/<uuid>', methods=['POST'])
def vsg_checkout(uuid):
    try:
        # Restaura a tabela
        success = vsg.restore(uuid)
        if not success:
            raise Exception("Restore failed")

        # Obter blob original
        with vsg.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM db_vsg WHERE uuid = %s", (uuid,))
            version = cur.fetchone()
            if not version:
                raise Exception("Snapshot not found")
            blob = json.loads(version["blob"])
            table = blob["table"]

        # Estado atual após restore
        with vsg.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {table} ORDER BY id ASC")
            state = cur.fetchall()

        now = datetime.now(timezone.utc).isoformat()
        user = vsg.user_callback() if vsg.user_callback else "system"
        new_uuid = str(uuid4())

        commit_blob = json.dumps({
            "uuid": new_uuid,
            "operation": "CHECKOUT",
            "query": f"CHECKOUT from {uuid}",
            "table": table,
            "record_id": None,
            "user": user,
            "timestamp": now,
            "before": blob["state"],
            "after": state,
            "state": state,
            "meta": {"checkout_from": uuid, "table": table}
        }, sort_keys=True)

        hash_blob = vsg._hash_blob(commit_blob)

        with vsg.connection.cursor() as cur:
            cur.execute(load_sql("not_current.sql"), {"table": table})
            cur.execute(load_sql("insert_audit.sql"), {
                "uuid": new_uuid,
                "operation": "CHECKOUT",
                "query": f"CHECKOUT from {uuid}",
                "meta": json.dumps({"checkout_from": uuid, "table": table}),
                "hash": hash_blob,
                "user_id": user,
                "blob": commit_blob,
                "is_current": True,
                "rollbacked": False,
                "is_deleted": False,
                "created_at": now
            })

        vsg.connection.commit()
        return jsonify({"checkout": new_uuid}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/vsg/logs', methods=['GET'])
def vsg_logs():
    table = request.args.get('table')
    limit = request.args.get('limit', default=10, type=int)

    if not table:
        return jsonify({'error': 'Parâmetro "table" é obrigatório'}), 400

    try:
        entries = vsg.logs(table=table, limit=limit)
        return jsonify(entries), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
