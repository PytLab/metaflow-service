import os
import sys
import argparse
from subprocess import Popen
from urllib.parse import quote
import psycopg2


def check_if_goose_table_exists(db_connection_string: str):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    try:
        cur.execute("SELECT schemaname,tablename FROM pg_tables")
        tables = [name for schema, name in cur.fetchall() if schema == "public"]
        if "goose_db_version" not in tables:
            print(
                f"Goose migration table not found among tables in schema public. Found: {', '.join(tables)}",
                file=sys.stderr,
            )
            return False
        else:
            print(f"Goose migration table found in schema public", file=sys.stderr)
            return True
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Run goose migrations")
    parser.add_argument("--only-if-empty-db", default=False, action="store_true")
    args = parser.parse_args()

    db_connection_string = "postgresql://{}:{}@{}:{}/{}?sslmode=disable".format(
        quote(os.environ["MF_METADATA_DB_USER"]),
        quote(os.environ["MF_METADATA_DB_PSWD"]),
        os.environ["MF_METADATA_DB_HOST"],
        os.environ["MF_METADATA_DB_PORT"],
        os.environ["MF_METADATA_DB_NAME"],
    )

    if args.only_if_empty_db:
        if check_if_goose_table_exists(db_connection_string):
            print(
                f"Skipping migrations since --only-if-empty-db flag is used",
                file=sys.stderr,
            )
            sys.exit(0)

    p = Popen(
        [
            "/go/bin/goose",
            "-dir",
            "/root/services/migration_service/migration_files/",
            "postgres",
            db_connection_string,
            "up",
        ]
    )
    if p.wait() != 0:
        raise Exception("Failed to run initial migration")


if __name__ == "__main__":
    main()
