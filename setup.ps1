# SBOM Auto Checker Setup Script for Windows

Write-Host "SBOM Auto Checker セットアップを開始します..." -ForegroundColor Cyan

# 1. 環境変数ファイルの作成
if (-Not (Test-Path .env)) {
    Write-Host ".envファイルを作成しています..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host ".envファイルが作成されました" -ForegroundColor Green
    Write-Host ".envファイルを編集して、必要な設定を行ってください" -ForegroundColor Yellow
} else {
    Write-Host ".envファイルは既に存在します" -ForegroundColor Green
}

# 2. シェルスクリプトの改行コード修正（Docker内で実行されるため）
Write-Host "シェルスクリプトの改行コードをLFに変換しています..." -ForegroundColor Yellow
Get-ChildItem -Recurse -Filter "*.sh" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match "`r`n") {
        $content = $content -replace "`r`n", "`n"
        [System.IO.File]::WriteAllText($_.FullName, $content, [System.Text.UTF8Encoding]::new($false))
        Write-Host "  OK: $($_.Name)" -ForegroundColor Gray
    }
}
Write-Host "改行コードの変換が完了しました" -ForegroundColor Green

# 3. Dockerのバージョン確認
Write-Host "Docker環境を確認しています..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "Docker環境が確認できました" -ForegroundColor Green
    Write-Host "  $dockerVersion" -ForegroundColor Gray
    
    try {
        $composeVersion = docker compose version
        Write-Host "  $composeVersion" -ForegroundColor Gray
    } catch {
        $composeVersion = docker-compose --version
        Write-Host "  $composeVersion" -ForegroundColor Gray
    }
} catch {
    Write-Host "Dockerがインストールされていません" -ForegroundColor Red
    Write-Host "https://docs.docker.com/desktop/install/windows-install/ からインストールしてください" -ForegroundColor Yellow
    exit 1
}

# 4. 必要なディレクトリの作成
Write-Host "必要なディレクトリを作成しています..." -ForegroundColor Yellow
@("uploads", "backups") | ForEach-Object {
    if (-Not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ | Out-Null
    }
}
Write-Host "ディレクトリの作成が完了しました" -ForegroundColor Green

# 5. セットアップ完了
Write-Host ""
Write-Host "セットアップが完了しました!" -ForegroundColor Green
Write-Host ""
Write-Host "次のステップ:" -ForegroundColor Cyan
Write-Host "1. .envファイルを編集して設定を行ってください:" -ForegroundColor White
Write-Host "   notepad .env" -ForegroundColor Gray
Write-Host ""
Write-Host "2. アプリケーションを起動してください:" -ForegroundColor White
Write-Host "   docker-compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "3. ブラウザでアクセスしてください:" -ForegroundColor White
Write-Host "   http://localhost:3000" -ForegroundColor Gray
Write-Host ""
