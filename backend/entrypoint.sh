#!/bin/bash
# データベース接続を待機するスクリプト

set -e

host="$POSTGRES_HOST"
port="$POSTGRES_PORT"
db="$POSTGRES_DB"
user="$POSTGRES_USER"

echo "Waiting for PostgreSQL at $host:$port..."

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -p "$port" -U "$user" -d "$db" -c '\q' 2>/dev/null; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

>&2 echo "PostgreSQL is up - executing command"

# データベース初期化(テーブル作成)
python << 'EOF'
from app.database import init_db
print("Initializing database...")
init_db()
print("Database initialized!")
EOF

# メインアプリケーションを起動
exec "$@"
