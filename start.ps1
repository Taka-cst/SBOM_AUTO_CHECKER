#!/usr/bin/env pwsh
# SBOM Auto Checker - Quick Start Script
# このスクリプトで簡単にビルド・起動できます

param(
    [Parameter(Position=0)]
    [ValidateSet("build", "up", "down", "restart", "logs", "clean")]
    [string]$Command = "up"
)

# .envファイルの存在確認
if (-Not (Test-Path .env)) {
    Write-Host "⚠️  .env file not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run setup first:" -ForegroundColor Yellow
    Write-Host "  .\setup.ps1" -ForegroundColor White
    Write-Host ""
    exit 1
}

# BuildKitを有効化(高速ビルド)
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"

Write-Host "🚀 SBOM Auto Checker - Docker Manager" -ForegroundColor Cyan
Write-Host "BuildKit enabled for faster builds!" -ForegroundColor Green
Write-Host ""

switch ($Command) {
    "build" {
        Write-Host "📦 Building backend image..." -ForegroundColor Yellow
        docker-compose build backend
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Build completed successfully!" -ForegroundColor Green
        }
    }
    "up" {
        Write-Host "🔄 Starting all services..." -ForegroundColor Yellow
        docker-compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✅ All services started!" -ForegroundColor Green
            Write-Host ""
            Write-Host "🌐 Access URLs:" -ForegroundColor Cyan
            Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
            Write-Host "   Backend API: http://localhost:8000" -ForegroundColor White
            Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
            Write-Host ""
            Write-Host "📊 Check status: .\start.ps1 logs" -ForegroundColor Gray
        }
    }
    "down" {
        Write-Host "🛑 Stopping all services..." -ForegroundColor Yellow
        docker-compose down
        Write-Host "✅ All services stopped!" -ForegroundColor Green
    }
    "restart" {
        Write-Host "🔄 Restarting services..." -ForegroundColor Yellow
        docker-compose restart
        Write-Host "✅ Services restarted!" -ForegroundColor Green
    }
    "logs" {
        Write-Host "📋 Showing logs (Ctrl+C to exit)..." -ForegroundColor Yellow
        docker-compose logs -f
    }
    "clean" {
        Write-Host "🧹 Cleaning up (volumes will be removed)..." -ForegroundColor Red
        $confirmation = Read-Host "Are you sure? (y/N)"
        if ($confirmation -eq 'y') {
            docker-compose down -v
            Write-Host "✅ Cleanup completed!" -ForegroundColor Green
        } else {
            Write-Host "❌ Cancelled" -ForegroundColor Yellow
        }
    }
}
