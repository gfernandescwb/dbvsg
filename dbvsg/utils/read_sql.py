from pathlib import Path

def load_sql(filename: str) -> str:
    base_path = Path(__file__).resolve().parent.parent / "sql"
    sql_file = base_path / filename
    return sql_file.read_text(encoding="utf-8")
