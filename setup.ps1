# SBOM Auto Checker Setup Script for Windows

Write-Host "Starting SBOM Auto Checker setup..." -ForegroundColor Cyan

# 1. Create environment file
if (-Not (Test-Path .env)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host ".env file created successfully" -ForegroundColor Green
    Write-Host "Please edit .env file and configure the required settings" -ForegroundColor Yellow
} else {
    Write-Host ".env file already exists" -ForegroundColor Green
}

# 2. Fix shell script line endings
Write-Host "Converting shell scripts to LF line endings..." -ForegroundColor Yellow
Get-ChildItem -Recurse -Filter "*.sh" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match "`r`n") {
        $content = $content -replace "`r`n", "`n"
        [System.IO.File]::WriteAllText($_.FullName, $content, [System.Text.UTF8Encoding]::new($false))
        Write-Host "  Fixed: $($_.Name)" -ForegroundColor Gray
    }
}
Write-Host "Line ending conversion completed" -ForegroundColor Green

# 3. Check Docker version
Write-Host "Checking Docker environment..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "Docker environment verified" -ForegroundColor Green
    Write-Host "  $dockerVersion" -ForegroundColor Gray
    
    try {
        $composeVersion = docker compose version
        Write-Host "  $composeVersion" -ForegroundColor Gray
    } catch {
        $composeVersion = docker-compose --version
        Write-Host "  $composeVersion" -ForegroundColor Gray
    }
} catch {
    Write-Host "Docker is not installed" -ForegroundColor Red
    Write-Host "Please install from: https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor Yellow
    exit 1
}

# 4. Create required directories
Write-Host "Creating required directories..." -ForegroundColor Yellow
@("uploads", "backups") | ForEach-Object {
    if (-Not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ | Out-Null
    }
}
Write-Host "Directory creation completed" -ForegroundColor Green

# 5. Setup complete
Write-Host ""
Write-Host "✅ Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. (Optional) Edit .env file to customize settings:" -ForegroundColor White
Write-Host "   notepad .env" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the application:" -ForegroundColor White
Write-Host "   .\start.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Access in your browser:" -ForegroundColor White
Write-Host "   🌐 Frontend:  http://localhost:3000" -ForegroundColor Gray
Write-Host "   📡 Backend:   http://localhost:8000" -ForegroundColor Gray
Write-Host "   📚 API Docs:  http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
