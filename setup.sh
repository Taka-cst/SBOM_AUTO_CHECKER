#!/bin/bash

# SBOM Auto Checker Setup Script for Linux/Mac

set -e

echo "🚀 SBOM Auto Checker セットアップを開始します..."

# 1. 環境変数ファイルの作成
if [ ! -f .env ]; then
    echo "📝 .envファイルを作成しています..."
    cp .env.example .env
    echo "✅ .envファイルが作成されました"
    echo "⚠️  .envファイルを編集して、必要な設定を行ってください"
else
    echo "✅ .envファイルは既に存在します"
fi

# 2. シェルスクリプトの改行コード修正
echo "🔧 シェルスクリプトの改行コードを修正しています..."
find . -name "*.sh" -type f -exec sed -i 's/\r$//' {} \; 2>/dev/null || true
echo "✅ 改行コードの修正が完了しました"

# 3. シェルスクリプトに実行権限を付与
echo "🔐 シェルスクリプトに実行権限を付与しています..."
find . -name "*.sh" -type f -exec chmod +x {} \;
echo "✅ 実行権限の付与が完了しました"

# 4. Dockerのバージョン確認
echo "🐳 Docker環境を確認しています..."
if ! command -v docker &> /dev/null; then
    echo "❌ Dockerがインストールされていません"
    echo "   https://docs.docker.com/get-docker/ からインストールしてください"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Composeがインストールされていません"
    exit 1
fi

echo "✅ Docker環境が確認できました"
docker --version
docker compose version 2>/dev/null || docker-compose --version

# 5. 必要なディレクトリの作成
echo "📁 必要なディレクトリを作成しています..."
mkdir -p uploads backups
echo "✅ ディレクトリの作成が完了しました"

# 6. セットアップ完了
echo ""
echo "✅ セットアップが完了しました!"
echo ""
echo "次のステップ:"
echo "1. (オプション) .envファイルを編集して設定をカスタマイズ:"
echo "   nano .env"
echo ""
echo "2. アプリケーションを起動:"
echo "   ./start.sh"
echo ""
echo "3. ブラウザでアクセス:"
echo "   🌐 Frontend:  http://localhost:3000"
echo "   📡 Backend:   http://localhost:8000"
echo "   📚 API Docs:  http://localhost:8000/docs"
echo ""
