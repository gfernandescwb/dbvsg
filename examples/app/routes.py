from flask import Blueprint, request, jsonify
from app import vsg

main = Blueprint('main', __name__)

@main.route("/clients", methods=["POST"])
def create_client():
    data = request.get_json()
    name = data["name"]
    try:
        query = f"INSERT INTO clients (name) VALUES ('{name}') RETURNING id"
        new_id = vsg.ops(query=query, operation="INSERT", table="clients")
        return jsonify({"id": new_id, "name": name}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 409 if "Conflict" in str(e) else 500

@main.route("/clients", methods=["GET"])
def list_clients():
    try:
        with vsg.connection.cursor() as cur:
            cur.execute("SELECT id, name FROM clients ORDER BY id ASC")
            result = cur.fetchall()
        return jsonify([{"id": row[0], "name": row[1]} for row in result])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/vsg/rollback", methods=["POST"])
@main.route("/vsg/rollback/<uuid>", methods=["POST"])
def rollback(uuid=None):
    try:
        result = vsg.rollback(target_uuid=uuid)
        return jsonify({"rollbacked_to": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/vsg/restore/<uuid>", methods=["POST"])
def restore(uuid):
    try:
        result = vsg.restore(uuid)
        return jsonify({"restored": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/vsg/merge/<uuid>", methods=["POST"])
def merge(uuid):
    try:
        result = vsg.merge(incoming_uuid=uuid)
        return jsonify({"merged_as": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/vsg/checkout/<uuid>", methods=["POST"])
def checkout(uuid):
    try:
        result = vsg.checkout(target_uuid=uuid)
        return jsonify({"checkout": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/vsg/logs", methods=["GET"])
def log_table():
    table = request.args.get("table")
    limit = int(request.args.get("limit", 10))
    try:
        logs = vsg.logs(table=table, limit=limit)
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
