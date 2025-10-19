# SBOM Vulnerability Checker

SBOM (Software Bill of Materials) ファイルをアップロードし、脆弱性データベースと照合して診断結果を表示するWebアプリケーションです。

## 🌟 主な機能

- **SBOMファイルアップロード**: CycloneDX、SPDX形式に対応
- **自動脆弱性診断**: Trivy (Aqua Security) を使用した高精度スキャン
- **リアルタイム結果表示**: 視覚的にわかりやすいダッシュボード
- **脆弱性レポート**: JSON/CSV形式でのエクスポート
- **定期的なDB更新**: 12時間ごとに脆弱性DBを自動更新
- **複数データソース**: NVD、GitHub Advisory、その他の脆弱性データベースに対応

## 📋 システム要件

- Docker 20.10以降
- Docker Compose 2.0以降
- 最低8GBのRAM
- 20GB以上のディスク空き容量

## 🚀 クイックスタート

### 📖 初めての方へ

```
┌─────────────────────────────────────────┐
│  1️⃣ git clone でリポジトリをダウンロード │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  2️⃣ .\setup.ps1 でセットアップ(初回のみ) │
│     - .envファイル作成                   │
│     - 改行コード修正                     │
│     - Docker環境チェック                 │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  3️⃣ .\start.ps1 でアプリ起動            │
│     - BuildKit高速ビルド                │
│     - 全サービス自動起動                 │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  🌐 http://localhost:3000 でアクセス!   │
└─────────────────────────────────────────┘
```

### 🎯 超簡単! 3ステップで起動

#### 1. リポジトリをクローン
```bash
git clone https://github.com/Taka-cst/SBOM_AUTO_CHECKER
cd SBOM_AUTO_CHECKER
```

#### 2. セットアップを実行 (初回のみ)
```powershell
# Windows
.\setup.ps1

# Linux/Mac
chmod +x setup.sh
./setup.sh
```

このスクリプトが自動的に:
- ✅ `.env`ファイルを作成
- ✅ 改行コード(CRLF→LF)を修正
- ✅ Docker環境をチェック
- ✅ 必要なディレクトリを作成

#### 3. アプリケーションを起動
```powershell
# Windows
.\start.ps1

# Linux/Mac
./start.sh
```

**たったこれだけ!** BuildKitによる高速ビルドで起動します 🚀

アクセスURL:
- 🌐 フロントエンド: http://localhost:3000
- 📡 バックエンドAPI: http://localhost:8000
- 📚 API ドキュメント: http://localhost:8000/docs

### その他のコマンド

```powershell
# Windows
.\start.ps1 build      # イメージをビルド
.\start.ps1 up         # サービスを起動(デフォルト)
.\start.ps1 down       # サービスを停止
.\start.ps1 restart    # サービスを再起動
.\start.ps1 logs       # ログを表示
.\start.ps1 clean      # 完全クリーンアップ(データも削除)

# Linux/Mac
./start.sh build
./start.sh up
./start.sh down
./start.sh restart
./start.sh logs
./start.sh clean
```

### 従来の方法でセットアップする場合

#### Windows環境

```powershell
# リポジトリのクローン
git clone <repository-url>
cd SBOM_AUTO_CHECKER

# 環境変数ファイルの作成
Copy-Item .env.example .env

# .envファイルを編集して必要な設定を行う
notepad .env

# Docker Composeで起動
docker-compose up -d

# ブラウザでアクセス
# http://localhost:3000
```

#### Linux/Mac環境

```bash
# リポジトリのクローン
git clone <repository-url>
cd SBOM_AUTO_CHECKER

# 環境変数ファイルの作成
cp .env.example .env

# .envファイルを編集して必要な設定を行う
nano .env

# シェルスクリプトに実行権限を付与（重要！）
find . -name "*.sh" -type f -exec chmod +x {} \;

# Docker Composeで起動
docker-compose up -d

# ブラウザでアクセス
# http://localhost:3000
```

## ⚠️ トラブルシューティング

### `.env file not found!` というエラーが出る

まず`setup.ps1`または`setup.sh`を実行してください:

```powershell
# Windows
.\setup.ps1

# Linux/Mac
./setup.sh
```

### シェルスクリプトが見つからないエラーが出る場合

Windowsでクローンした場合、改行コードがCRLFになっている可能性があります。
`setup.ps1`または`setup.sh`を実行すると自動的に修正されます。

手動で修正する場合:
```bash
# Linux/Mac環境で実行
find . -name "*.sh" -type f -exec dos2unix {} \;

# または
find . -name "*.sh" -type f -exec sed -i 's/\r$//' {} \;
```

### .envファイルが読み込まれない場合

- ✅ `.env`ファイルが正しく作成されているか確認
- ✅ 改行コードがLFになっているか確認
- ✅ 必要な環境変数がすべて設定されているか確認

### Dockerが起動しない場合

- ✅ Docker Desktopがインストールされているか確認
- ✅ Docker Desktopが起動しているか確認
- ✅ WSL2が有効になっているか確認(Windows)

## 📚 ドキュメント

- [アーキテクチャ設計書](docs/ARCHITECTURE.md)
- [環境構築ガイド](docs/SETUP.md)
- [API仕様書](docs/API.md)
- [ユーザーマニュアル](docs/USER_MANUAL.md)
- [運用・保守ガイド](docs/OPERATIONS.md)
- [開発ガイド](docs/DEVELOPMENT.md)
- [Docker高速化ガイド](docs/DOCKER_OPTIMIZATION.md) ⚡ New!

## 🏗️ プロジェクト構造

```
SBOM_AUTO_CHECKER/
├── backend/          # バックエンドAPI (FastAPI)
├── frontend/         # フロントエンド (React)
├── scanner/          # 脆弱性スキャナー
├── database/         # データベース初期化スクリプト
├── docs/            # ドキュメント
├── docker-compose.yml
└── README.md
```

## 🔧 技術スタック

- **バックエンド**: Python 3.11 + FastAPI
- **フロントエンド**: React 18 + TypeScript + Vite
- **データベース**: PostgreSQL 15
- **コンテナ**: Docker + Docker Compose
- **脆弱性スキャナー**: Trivy (Aqua Security)
- **タスクキュー**: Celery + Redis
- **脆弱性DB**: NVD, GitHub Advisory, OSV など (Trivy経由)

## 📄 ライセンス

MIT License

## 👥 貢献

プルリクエストを歓迎します!

## 📞 サポート

問題が発生した場合は、Issueを作成してください。
