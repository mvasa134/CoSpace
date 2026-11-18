"""Накочує схему і процедури в БД (Azure SQL або будь-який SQL Server) з Python.

    python scripts/deploy_db.py                # схема (якщо ще немає) + процедури
    python scripts/deploy_db.py --procs-only   # лише процедури (CREATE OR ALTER, можна повторювати)
    (002_email_verification.sql застосовується завжди: ідемпотентна міграція)
    python scripts/deploy_db.py --app-user     # + створити обмеженого користувача coworking_api (EXECUTE only)

Параметри з .env (DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD, ...). Для --app-user ще APP_DB_PASSWORD.
"""
import argparse
import os
import re
import sys
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

GO_RE = re.compile(r"^\s*GO\s*$", re.IGNORECASE | re.MULTILINE)


def conn_str() -> str:
    env = os.environ
    parts = [
        f"DRIVER={{{env.get('DB_DRIVER', 'ODBC Driver 18 for SQL Server')}}}",
        f"SERVER={env['DB_SERVER']}",
        f"DATABASE={env.get('DB_NAME', 'CoworkingDB')}",
        f"UID={env['DB_USER']}",
        "PWD={" + env["DB_PASSWORD"].replace("}", "}}") + "}",
        "Encrypt=yes",
        f"TrustServerCertificate={'yes' if env.get('DB_TRUST_CERT', 'false').lower() == 'true' else 'no'}",
        "Connection Timeout=60",
    ]
    return ";".join(parts) + ";"


def run_file(cur, path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    batches = [b.strip() for b in GO_RE.split(text) if b.strip()]
    print(f">> {path.name}: {len(batches)} batch(es)")
    for i, batch in enumerate(batches, 1):
        try:
            cur.execute(batch)
            while cur.nextset():
                pass
        except pyodbc.Error as e:
            print(f"!! помилка в batch #{i} файлу {path.name}:\n{batch[:300]}...\n{e}")
            sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs-only", action="store_true")
    ap.add_argument("--app-user", action="store_true")
    args = ap.parse_args()

    conn = pyodbc.connect(conn_str(), autocommit=True)
    cur = conn.cursor()

    if not args.procs_only:
        exists = cur.execute("SELECT OBJECT_ID(N'dbo.Users', N'U')").fetchone()[0]
        if exists:
            print(">> схема вже є, пропускаю coworking_db.sql")
        else:
            run_file(cur, ROOT / "db" / "coworking_db.sql")

    run_file(cur, ROOT / "db" / "002_email_verification.sql")
    run_file(cur, ROOT / "db" / "coworking_procedures.sql")

    if args.app_user:
        pwd = os.environ["APP_DB_PASSWORD"].replace("'", "''")
        cur.execute(
            "IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'coworking_api') "
            f"CREATE USER [coworking_api] WITH PASSWORD = N'{pwd}'"
        )
        cur.execute("GRANT EXECUTE ON SCHEMA::dbo TO [coworking_api]")
        print(">> користувач coworking_api створений (лише EXECUTE). Вкажи його в DB_USER/DB_PASSWORD для API.")

    print(">> готово")


if __name__ == "__main__":
    main()
