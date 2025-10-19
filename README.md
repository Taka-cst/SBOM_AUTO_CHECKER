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

```powershell
# リポジトリのクローン
git clone <repository-url>
cd SBOM_AUTO_CHECKER

# Docker Composeで起動
docker-compose up -d

# ブラウザでアクセス
# http://localhost:3000
```

## 📚 ドキュメント

- [アーキテクチャ設計書](docs/ARCHITECTURE.md)
- [環境構築ガイド](docs/SETUP.md)
- [API仕様書](docs/API.md)
- [ユーザーマニュアル](docs/USER_MANUAL.md)
- [運用・保守ガイド](docs/OPERATIONS.md)
- [開発ガイド](docs/DEVELOPMENT.md)

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
