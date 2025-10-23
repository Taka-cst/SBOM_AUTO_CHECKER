# 運用・保守ガイド

## 📋 目次

1. [日常運用](#日常運用)
2. [監視とログ](#監視とログ)
3. [バックアップ](#バックアップ)
4. [トラブルシューティング](#トラブルシューティング)
5. [パフォーマンスチューニング](#パフォーマンスチューニング)
6. [セキュリティ](#セキュリティ)
7. [アップデート手順](#アップデート手順)

## 🔄 日常運用

### 起動と停止

**システム起動:**
```powershell
cd SBOM_AUTO_CHECKER
docker-compose up -d
```

**システム停止:**
```powershell
docker-compose down
```

**サービスの再起動:**
```powershell
# 全サービス
docker-compose restart

# 特定のサービス
docker-compose restart backend
docker-compose restart scanner
```

### 状態確認

**コンテナ状態の確認:**
```powershell
docker-compose ps
```

**リソース使用状況:**
```powershell
docker stats
```

**ディスク使用量:**
```powershell
docker system df
```

## 📊 監視とログ

### ログの確認

**全サービスのログ:**
```powershell
docker-compose logs -f
```

**特定サービスのログ:**
```powershell
docker-compose logs -f backend
docker-compose logs -f scanner
docker-compose logs -f postgres
```

**ログの保存:**
```powershell
docker-compose logs --no-color > logs_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt
```

### 重要なログメッセージ

#### 正常なログ

```
backend    | INFO: Application startup complete.
scanner    | INFO: Connected to redis://redis:6379/0
postgres   | LOG: database system is ready to accept connections
```

#### 警告ログ

```
scanner    | WARNING: NVD API rate limit approaching
backend    | WARNING: Database connection pool exhausted
```

#### エラーログ

```
backend    | ERROR: Database connection failed
scanner    | ERROR: Failed to download CVE data
frontend   | ERROR: API request timeout
```

### 監視項目

| 項目 | 確認方法 | 正常値 | 対応 |
|------|---------|--------|------|
| CPU使用率 | `docker stats` | <70% | スケールアップ |
| メモリ使用率 | `docker stats` | <80% | メモリ増設 |
| ディスク使用率 | `docker system df` | <80% | クリーンアップ |
| API応答時間 | `/health`エンドポイント | <1秒 | 最適化 |
| NVD更新状態 | アプリケーションログ | 12時間ごと | API確認 |

### ヘルスチェック

**APIヘルスチェック:**
```powershell
curl http://localhost:8000/health
```

**期待されるレスポンス:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "scanner": "healthy"
  }
}
```

## 💾 バックアップ

### データベースバックアップ

**手動バックアップ:**
```powershell
# バックアップディレクトリ作成
mkdir backups

# PostgreSQLバックアップ
docker-compose exec postgres pg_dump -U sbom_admin sbom_checker > backups/sbom_db_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql
```

**自動バックアップスクリプト (backup.ps1):**
```powershell
# backup.ps1
$BACKUP_DIR = "backups"
$TIMESTAMP = Get-Date -Format 'yyyyMMdd_HHmmss'
$BACKUP_FILE = "$BACKUP_DIR/sbom_db_$TIMESTAMP.sql"

# バックアップディレクトリ作成
if (!(Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR
}

# データベースバックアップ
docker-compose exec -T postgres pg_dump -U sbom_admin sbom_checker > $BACKUP_FILE

# 圧縮
Compress-Archive -Path $BACKUP_FILE -DestinationPath "$BACKUP_FILE.zip"
Remove-Item $BACKUP_FILE

# 7日以上古いバックアップを削除
Get-ChildItem $BACKUP_DIR -Filter "*.zip" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item

Write-Host "Backup completed: $BACKUP_FILE.zip"
```

**自動化 (タスクスケジューラー):**
```powershell
# 毎日午前3時にバックアップ実行
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\path\to\backup.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 3am
Register-ScheduledTask -TaskName "SBOM Backup" -Action $action -Trigger $trigger
```

### データベース復元

```powershell
# 復元前にサービス停止
docker-compose down

# データベースボリュームを削除
docker volume rm sbom_auto_checker_postgres_data

# サービス起動
docker-compose up -d postgres

# 少し待つ
Start-Sleep -Seconds 10

# バックアップから復元
Get-Content backups/sbom_db_20251016_030000.sql | docker-compose exec -T postgres psql -U sbom_admin sbom_checker

# 全サービス起動
docker-compose up -d
```

### アップロードファイルのバックアップ

```powershell
# アップロードファイルのバックアップ
docker cp sbom-backend:/app/uploads ./backups/uploads_$(Get-Date -Format 'yyyyMMdd')
```

## 🔧 トラブルシューティング

### 問題1: コンテナが起動しない

**症状:**
```
Error: Cannot start service backend: driver failed
```

**確認事項:**
```powershell
# Dockerの状態確認
docker info

# ログ確認
docker-compose logs backend

# ポートの競合確認
netstat -ano | findstr :8000
```

**解決方法:**
- Dockerデスクトップを再起動
- ポートを変更(.envファイル)
- メモリ割り当てを増やす

### 問題2: データベース接続エラー

**症状:**
```
ERROR: could not connect to server
```

**診断:**
```powershell
# PostgreSQL状態確認
docker-compose ps postgres

# データベース接続テスト
docker-compose exec postgres psql -U sbom_admin -d sbom_checker -c "SELECT 1;"

# ログ確認
docker-compose logs postgres
```

**解決方法:**
```powershell
# PostgreSQL再起動
docker-compose restart postgres

# 完全リセット(データ消失注意!)
docker-compose down -v
docker-compose up -d
```

### 問題3: NVD更新が失敗する

**症状:**
```
ERROR: Failed to download CVE data from NVD
```

**確認事項:**
```powershell
# スキャナーログ確認
docker-compose logs scanner | Select-String "NVD"

# インターネット接続確認
Test-NetConnection services.nvd.nist.gov -Port 443
```

**解決方法:**
- NVD APIキーを設定
- レート制限を確認
- プロキシ設定を確認
- 手動更新を実行

### 問題4: ディスク容量不足

**確認:**
```powershell
docker system df -v
```

**クリーンアップ:**
```powershell
# 未使用のイメージを削除
docker image prune -a

# 未使用のボリュームを削除
docker volume prune

# ビルドキャッシュをクリア
docker builder prune

# 完全クリーンアップ(注意!)
docker system prune -a --volumes
```

### 問題5: パフォーマンスが遅い

**診断:**
```powershell
# リソース使用状況
docker stats

# データベースクエリ分析
docker-compose exec postgres psql -U sbom_admin -d sbom_checker -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"
```

**最適化:**
- インデックスの追加
- クエリの最適化
- コンテナリソースの増加
- 古いデータの削除

## ⚡ パフォーマンスチューニング

### データベース最適化

**接続プール設定 (backend/app/database.py):**
```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,        # 増やす
    max_overflow=40,     # 増やす
    pool_pre_ping=True
)
```

**PostgreSQL設定調整:**
```sql
-- データベース内で実行
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET work_mem = '16MB';

-- 再起動
```

### Celeryワーカー数の調整

**docker-compose.ymlを編集:**
```yaml
scanner:
  command: celery -A app.celery_worker worker --loglevel=info --concurrency=4
```

### Nginxキャッシュ設定

**frontend/nginx.confに追加:**
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_pass http://backend:8000;
}
```

## 🔐 セキュリティ

### セキュリティチェックリスト

- [ ] `.env`ファイルのパスワードを強力なものに変更
- [ ] NVD APIキーの設定
- [ ] HTTPSの有効化
- [ ] ファイアウォール設定
- [ ] 定期的なアップデート
- [ ] ログの監視
- [ ] バックアップの確認

### パスワード変更

```powershell
# データベースパスワード変更
docker-compose exec postgres psql -U sbom_admin -d sbom_checker -c "ALTER USER sbom_admin WITH PASSWORD 'new_password';"

# .envファイルも更新
```

### アクセス制限

**本番環境では外部アクセスを制限:**

docker-compose.ymlから以下を変更:
```yaml
ports:
  - "127.0.0.1:8000:8000"  # ローカルホストのみ
```

## 🆙 アップデート手順

### マイナーアップデート

```powershell
# 1. 最新コードを取得
git pull origin main

# 2. イメージの再ビルド
docker-compose build

# 3. サービスの再起動
docker-compose down
docker-compose up -d

# 4. 動作確認
curl http://localhost:8000/health
```

### メジャーアップデート

```powershell
# 1. バックアップ
.\backup.ps1

# 2. 最新コードを取得
git pull origin main

# 3. マイグレーション確認
docker-compose run backend alembic upgrade head

# 4. イメージの再ビルド
docker-compose build --no-cache

# 5. サービスの再起動
docker-compose down
docker-compose up -d

# 6. 動作確認とテスト
```

## 📞 サポート

### ログ収集

問題報告時は以下を添付:

```powershell
# 診断情報の収集
docker-compose logs > full_logs.txt
docker-compose ps > container_status.txt
docker system df > disk_usage.txt
docker system info > system_info.txt
```

---

**最終更新: 2025年10月16日**
