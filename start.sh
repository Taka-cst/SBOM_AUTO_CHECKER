#!/bin/bash
# SBOM Auto Checker - Quick Start Script (Linux/Mac)
# このスクリプトで簡単にビルド・起動できます

set -e

# .envファイルの存在確認
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Please run setup first:"
    echo "  ./setup.sh"
    echo ""
    exit 1
fi

# BuildKitを有効化(高速ビルド)
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

COMMAND=${1:-up}

echo "🚀 SBOM Auto Checker - Docker Manager"
echo "BuildKit enabled for faster builds!"
echo ""

case "$COMMAND" in
    build)
        echo "📦 Building backend image..."
        docker-compose build backend
        echo "✅ Build completed successfully!"
        ;;
    up)
        echo "🔄 Starting all services..."
        docker-compose up -d
        echo ""
        echo "✅ All services started!"
        echo ""
        echo "🌐 Access URLs:"
        echo "   Frontend: http://localhost:3000"
        echo "   Backend API: http://localhost:8000"
        echo "   API Docs: http://localhost:8000/docs"
        echo ""
        echo "📊 Check status: ./start.sh logs"
        ;;
    down)
        echo "🛑 Stopping all services..."
        docker-compose down
        echo "✅ All services stopped!"
        ;;
    restart)
        echo "🔄 Restarting services..."
        docker-compose restart
        echo "✅ Services restarted!"
        ;;
    logs)
        echo "📋 Showing logs (Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
    clean)
        echo "🧹 Cleaning up (volumes will be removed)..."
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v
            echo "✅ Cleanup completed!"
        else
            echo "❌ Cancelled"
        fi
        ;;
    *)
        echo "Usage: ./start.sh {build|up|down|restart|logs|clean}"
        exit 1
        ;;
esac
