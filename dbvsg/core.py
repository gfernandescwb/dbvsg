from .mods.conn import conn
from .mods.ensure_table import ensure_table
from .mods.ops import ops
from .mods.rollback import rollback
from .mods.restore import restore
from .mods.merge import merge
from .mods.checkout import checkout
from .mods.logs import logs
from .mods.diff import diff

class DBVSG:
    def __init__(self):
        self.connection = None
        self.user_callback = None

    def conn(self, db_url: str, user_context=None):
        self.user_callback = user_context
        conn(self, db_url)
        ensure_table(self)

    def ops(self, *, query: str, operation: str, table: str, parent_uuid: str = None):
        return ops(self, query=query, operation=operation, table=table, parent_uuid=parent_uuid)

    def rollback(self, target_uuid=None):
        return rollback(self, target_uuid)

    def restore(self, record_id: str):
        return restore(self, record_id)

    def merge(self, incoming_uuid: str):
        return merge(self, incoming_uuid)

    def checkout(self, uuid: str):
        return checkout(self, uuid)

    def logs(self, table: str, limit: int = 10):
        return logs(self, table, limit)

    def diff(self, uuid_a: str, uuid_b: str):
        return diff(self, uuid_a, uuid_b)

    def _hash_blob(self, blob: str) -> str:
        import hashlib
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()
