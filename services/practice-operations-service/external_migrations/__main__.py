import os

from .runner import run

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise SystemExit("DATABASE_URL is required")
applied = run(database_url)
print("External migration result:", ", ".join(applied) if applied else "already current")
