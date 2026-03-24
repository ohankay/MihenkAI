param(
    [string]$OutputTar = "./mihenkai_images.tar"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI bulunamadi. Docker Desktop/Docker Engine kurulu olmali."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir

try {
    Write-Step "Backend/Worker/Frontend image'larini build et"
    docker compose build backend worker frontend

    Write-Step "DB ve Redis image'larini indir"
    docker pull postgres:15-alpine
    docker pull redis:7-alpine

    $images = @(
        "mihenkai-backend:latest",
        "mihenkai-worker:latest",
        "mihenkai-frontend:latest",
        "postgres:15-alpine",
        "redis:7-alpine"
    )

    Write-Step "Image varligini dogrula"
    foreach ($image in $images) {
        docker image inspect $image | Out-Null
    }

    $outputPath = Resolve-Path (Split-Path -Parent $OutputTar) -ErrorAction SilentlyContinue
    if (-not $outputPath) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $OutputTar) -Force | Out-Null
    }

    $fullTarPath = [System.IO.Path]::GetFullPath($OutputTar)

    Write-Step "Image'lari tar dosyasina export et: $fullTarPath"
    docker save -o $fullTarPath $images

    Write-Step "SHA256 checksum olustur"
    $hash = Get-FileHash -Path $fullTarPath -Algorithm SHA256
    $hashLine = "{0} *{1}" -f $hash.Hash.ToLowerInvariant(), (Split-Path -Leaf $fullTarPath)
    $hashPath = "$fullTarPath.sha256"
    Set-Content -Path $hashPath -Value $hashLine -Encoding ascii

    Write-Host "`nTamamlandi." -ForegroundColor Green
    Write-Host "TAR   : $fullTarPath"
    Write-Host "SHA256: $hashPath"
    Write-Host "`nOffline makinede:"
    Write-Host "  docker load -i $(Split-Path -Leaf $fullTarPath)"
    Write-Host "  docker compose up -d --no-build"
}
finally {
    Pop-Location
}
