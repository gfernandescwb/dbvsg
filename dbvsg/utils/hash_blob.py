import hashlib

def hash_blob(blob: str):
   return hashlib.sha256(blob.encode("utf-8")).hexdigest()
