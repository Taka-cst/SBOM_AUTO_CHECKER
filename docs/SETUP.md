# 環境構築ガイド

## 📋 前提条件

### 必須ソフトウェア

| ソフトウェア | バージョン | 用途 |
|------------|----------|------|
| Docker | 20.10以降 | コンテナ実行環境 |
| Docker Compose | 2.0以降 | マルチコンテナ管理 |

### システム要件

- **OS**: Windows 10/11, macOS 11以降, Linux(Ubuntu 20.04以降推奨)
- **RAM**: 最低8GB、推奨16GB
- **ディスク**: 20GB以上の空き容量
- **CPU**: 2コア以上推奨

### ネットワーク要件

- インターネット接続(初回セットアップ時)
- NVD API アクセス可能(https://services.nvd.nist.gov/)
- ポート3000, 8000が利用可能

## 🚀 クイックスタート

### Windows (PowerShell)

```powershell
# 1. リポジトリのクローン
git clone <repository-url>
cd SBOM_AUTO_CHECKER

# 2. 環境変数ファイルの作成
Copy-Item .env.example .env

# 3. Docker Composeで起動
docker-compose up -d

# 4. ログ確認
docker-compose logs -f

# 5. ブラウザでアクセス
# http://localhost:3000
```

### macOS / Linux

```bash
# 1. リポジトリのクローン
git clone <repository-url>
cd SBOM_AUTO_CHECKER

# 2. 環境変数ファイルの作成
cp .env.example .env

# 3. Docker Composeで起動
docker-compose up -d

# 4. ログ確認
docker-compose logs -f

# 5. ブラウザでアクセス
# http://localhost:3000
```

## ⚙️ 詳細セットアップ手順

### 1. Dockerのインストール

#### Windows

1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) をダウンロード
2. インストーラーを実行
3. WSL 2 バックエンドを有効化(推奨)
4. インストール完了後、Docker Desktopを起動

**確認:**
```powershell
docker --version
docker-compose --version
```

#### macOS

```bash
# Homebrewでインストール
brew install --cask docker

# または公式サイトからダウンロード
# https://www.docker.com/products/docker-desktop/
```

#### Linux (Ubuntu)

```bash
# Docker のインストール
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose のインストール
sudo apt-get update
sudo apt-get install docker-compose-plugin

# 現在のユーザーをdockerグループに追加
sudo usermod -aG docker $USER

# ログアウト/ログインして反映
```

### 2. プロジェクトのセットアップ

```powershell
# プロジェクトディレクトリに移動
cd SBOM_AUTO_CHECKER

# ディレクトリ構造の確認
tree /F  # Windows
# または
ls -R    # macOS/Linux
```

### 3. 環境変数の設定

`.env`ファイルを編集します:

```env
# アプリケーション設定
APP_NAME=SBOM Vulnerability Checker
APP_ENV=production
DEBUG=false

# データベース設定
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=sbom_checker
POSTGRES_USER=sbom_admin
POSTGRES_PASSWORD=your_secure_password_here

# Redis設定
REDIS_HOST=redis
REDIS_PORT=6379

# バックエンドAPI設定
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_WORKERS=4

# フロントエンド設定
FRONTEND_PORT=3000
VITE_API_URL=http://localhost:8000

# NVD API設定(オプション - レート制限緩和のため)
NVD_API_KEY=your_nvd_api_key_here

# セキュリティ設定
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1

# ファイルアップロード設定
MAX_UPLOAD_SIZE=52428800  # 50MB in bytes

# スキャナー設定
SCANNER_UPDATE_INTERVAL=43200  # 12時間(秒)
SCANNER_BATCH_SIZE=100

# ログ設定
LOG_LEVEL=INFO
```

**重要:** 本番環境では必ず以下を変更してください:
- `POSTGRES_PASSWORD`: 強力なパスワード
- `SECRET_KEY`: ランダムな文字列
- `NVD_API_KEY`: NVDから取得したAPIキー(推奨)

### 4. NVD APIキーの取得(推奨)

NVDのAPIキーを取得することで、レート制限が緩和されます。

1. [NVD API Key Request](https://nvd.nist.gov/developers/request-an-api-key) にアクセス
2. メールアドレスを入力して申請
3. 受信したAPIキーを`.env`の`NVD_API_KEY`に設定

### 5. Docker Composeでの起動

```powershell
# すべてのコンテナをビルドして起動
docker-compose up --build -d

# 起動状態の確認
docker-compose ps

# 期待される出力:
# NAME                    SERVICE       STATUS       PORTS
# sbom-frontend           frontend      running      0.0.0.0:3000->3000/tcp
# sbom-backend            backend       running      0.0.0.0:8000->8000/tcp
# sbom-scanner            scanner       running      
# sbom-postgres           postgres      running      5432/tcp
# sbom-redis              redis         running      6379/tcp
```

### 6. 初回データベースセットアップ

```powershell
# データベースマイグレーションの実行
docker-compose exec backend python -m alembic upgrade head

# 初期データの投入(オプション)
docker-compose exec backend python scripts/seed_data.py
```

### 7. 動作確認

#### バックエンドAPI確認

ブラウザまたはcurlで確認:

```powershell
# ヘルスチェック
curl http://localhost:8000/health

# APIドキュメント
# http://localhost:8000/docs にアクセス
```

#### フロントエンド確認

ブラウザで `http://localhost:3000` にアクセス

#### 脆弱性DBの初期ダウンロード確認

```powershell
# スキャナーログを確認
docker-compose logs scanner

# データベース内のCVE数を確認
docker-compose exec postgres psql -U sbom_admin -d sbom_checker -c "SELECT COUNT(*) FROM vulnerabilities;"
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. ポートが既に使用されている

**エラー:**
```
Error: bind: address already in use
```

**解決方法:**

```powershell
# Windows: 使用中のポートを確認
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# プロセスを終了するか、.envファイルでポート番号を変更
```

#### 2. Docker Desktopが起動していない(Windows/macOS)

**エラー:**
```
Cannot connect to the Docker daemon
```

**解決方法:**
- Docker Desktopを起動してください

#### 3. メモリ不足

**エラー:**
```
Container killed due to memory limit
```

**解決方法:**

Docker Desktopの設定でメモリ割り当てを増やします:
- Settings → Resources → Memory → 8GB以上に設定

#### 4. NVDダウンロードが遅い

**解決方法:**

APIキーを設定するか、初期データのインポートを利用:

```powershell
# 事前にダウンロードしたCVEデータをインポート
docker-compose exec backend python scripts/import_nvd_data.py --file /path/to/nvd-data.json
```

#### 5. データベース接続エラー

**エラー:**
```
could not connect to server: Connection refused
```

**解決方法:**

```powershell
# データベースコンテナの状態を確認
docker-compose ps postgres

# 再起動
docker-compose restart postgres

# ログ確認
docker-compose logs postgres
```

## 🔄 アップデート手順

```powershell
# 1. 最新コードを取得
git pull origin main

# 2. コンテナを停止
docker-compose down

# 3. イメージを再ビルド
docker-compose build --no-cache

# 4. マイグレーション実行
docker-compose run backend python -m alembic upgrade head

# 5. 再起動
docker-compose up -d
```

## 🧹 クリーンアップ

### すべてのコンテナとデータを削除

```powershell
# コンテナ、ネットワーク、ボリュームをすべて削除
docker-compose down -v

# イメージも削除する場合
docker-compose down -v --rmi all
```

### データベースのみリセット

```powershell
# データベースボリュームを削除
docker-compose down
docker volume rm sbom_auto_checker_postgres_data
docker-compose up -d
```

## 📊 動作確認チェックリスト

- [ ] Docker Desktop / Docker Engineが起動している
- [ ] `docker-compose ps`で全サービスが"running"状態
- [ ] http://localhost:3000 でフロントエンドにアクセス可能
- [ ] http://localhost:8000/docs でAPI Docsにアクセス可能
- [ ] サンプルSBOMファイルをアップロードできる
- [ ] スキャン結果が表示される
- [ ] `docker-compose logs scanner`でNVD更新ログが確認できる

## 🔐 セキュリティ設定(本番環境)

本番環境にデプロイする場合の追加設定:

1. **HTTPS化**
   - Nginx や Traefik でリバースプロキシを設定
   - Let's Encrypt で SSL証明書を取得

2. **環境変数の保護**
   - `.env`ファイルを`.gitignore`に追加
   - パスワードを強力なものに変更
   - シークレット管理ツールの使用(AWS Secrets Manager等)

3. **ファイアウォール設定**
   - 必要なポートのみ開放
   - データベースポートは外部公開しない

4. **定期バックアップ**
   - データベースの定期バックアップ設定
   - バックアップスクリプトの自動実行

## 🆘 サポート

問題が解決しない場合:

1. ログを確認: `docker-compose logs`
2. GitHubでIssueを作成
3. [docs/OPERATIONS.md](OPERATIONS.md) の詳細トラブルシューティングを参照

## 📚 次のステップ

環境構築が完了したら:

- [ユーザーマニュアル](USER_MANUAL.md) でアプリケーションの使い方を確認
- [API仕様書](API.md) でAPI詳細を確認
- [開発ガイド](DEVELOPMENT.md) で開発方法を確認
