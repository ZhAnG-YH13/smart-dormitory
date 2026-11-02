<#
智慧宿舍门禁终端 —— 一键启动脚本

用法（双击 start_terminal.bat 也可）：
    powershell -ExecutionPolicy Bypass -File scripts\start_terminal.ps1
    powershell -ExecutionPolicy Bypass -File scripts\start_terminal.ps1 -NoBrowser
    powershell -ExecutionPolicy Bypass -File scripts\start_terminal.ps1 -Stop

会依次启动：
    1. 后端  FastAPI  : 8000   (uvicorn)
    2. 前端  Vite     : 5173   (npm run dev)
    3. HTTPS 代理     : 5443   (scripts/https_proxy.py -> 5173，供手机实时摄像头使用)
#>
param(
    [switch]$Stop,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'

$Root        = Split-Path -Parent $PSScriptRoot
$BackendDir  = Join-Path $Root 'backend'
$FrontendDir = Join-Path $Root 'frontend'
$ProxyScript = Join-Path $PSScriptRoot 'https_proxy.py'
$LogDir      = Join-Path $PSScriptRoot 'logs'

$BackendPort  = 8000
$FrontendPort = 5173
$ProxyPort    = 5443

function Test-Port([int]$Port) {
    $c = New-Object Net.Sockets.TcpClient
    try {
        $c.Connect('127.0.0.1', $Port)
        return $true
    } catch {
        return $false
    } finally {
        $c.Dispose()
    }
}

function Wait-Port([int]$Port, [int]$TimeoutSec = 45) {
    $end = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $end) {
        if (Test-Port $Port) { return $true }
        Start-Sleep -Milliseconds 800
    }
    return $false
}

function Get-LanIps {
    Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notmatch '^(127\.|169\.254\.)' } |
        Select-Object -ExpandProperty IPAddress -Unique
}

function Stop-OnPort([int]$Port) {
    $conns = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host ("  已停止端口 {0}（进程 {1}）" -f $Port, $c.OwningProcess)
    }
}

# ---------------- 停止模式 ----------------
if ($Stop) {
    Write-Host '正在停止门禁终端相关服务...' -ForegroundColor Yellow
    Stop-OnPort $ProxyPort
    Stop-OnPort $FrontendPort
    Stop-OnPort $BackendPort
    Write-Host '已停止。' -ForegroundColor Green
    return
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# ---------------- 环境检查 ----------------
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) {
    Write-Host '未找到 python，请先安装 Python 3.12 并加入 PATH。' -ForegroundColor Red
    exit 1
}

$nodeExe = (Get-Command node -ErrorAction SilentlyContinue).Source
if (-not $nodeExe) {
    # 便携版 Node 不在 PATH 时自动补上
    foreach ($dir in @('C:\node-v20.11.0-win-x64', (Join-Path $env:ProgramFiles 'nodejs'))) {
        if (Test-Path (Join-Path $dir 'node.exe')) {
            $nodeExe = Join-Path $dir 'node.exe'
            $env:Path = $dir + ';' + $env:Path
            break
        }
    }
}
if (-not $nodeExe) {
    Write-Host '未找到 Node.js，请安装 Node 18+ 或解压便携版到 C:\node-v20.11.0-win-x64。' -ForegroundColor Red
    exit 1
}
$npmCmd = Join-Path (Split-Path $nodeExe) 'npm.cmd'

Write-Host '检查运行环境...' -ForegroundColor Cyan

# 后端依赖（缺失时自动安装）
Push-Location $BackendDir
& $python -c 'import fastapi, uvicorn' 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host '  正在安装后端依赖（首次运行）...' -ForegroundColor Yellow
    & $python -m pip install -r requirements.txt
}
Pop-Location

# 前端依赖
if (-not (Test-Path (Join-Path $FrontendDir 'node_modules'))) {
    Write-Host '  正在安装前端依赖（首次运行，耗时较长）...' -ForegroundColor Yellow
    Push-Location $FrontendDir
    & $npmCmd install
    Pop-Location
}

if (-not (Test-Path $ProxyScript)) {
    Write-Host "缺少 $ProxyScript，无法启动 HTTPS 代理。" -ForegroundColor Red
    exit 1
}

# ---------------- 启动服务 ----------------
Write-Host ''
Write-Host '启动服务：' -ForegroundColor Cyan

if (Test-Port $BackendPort) {
    Write-Host ("  后端  {0}  已在运行，跳过" -f $BackendPort) -ForegroundColor DarkGray
} else {
    Start-Process -FilePath $python `
        -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', "$BackendPort") `
        -WorkingDirectory $BackendDir -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $LogDir 'backend.log') `
        -RedirectStandardError (Join-Path $LogDir 'backend.err.log') | Out-Null
    Write-Host ("  后端  {0}  启动中..." -f $BackendPort) -ForegroundColor Gray
}

if (Test-Port $FrontendPort) {
    Write-Host ("  前端  {0}  已在运行，跳过" -f $FrontendPort) -ForegroundColor DarkGray
} else {
    Start-Process -FilePath $npmCmd -ArgumentList @('run', 'dev') `
        -WorkingDirectory $FrontendDir -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $LogDir 'frontend.log') `
        -RedirectStandardError (Join-Path $LogDir 'frontend.err.log') | Out-Null
    Write-Host ("  前端  {0}  启动中..." -f $FrontendPort) -ForegroundColor Gray
}

$backendOk  = Wait-Port $BackendPort
$frontendOk = Wait-Port $FrontendPort

if (-not $backendOk) {
    Write-Host ("后端未能在规定时间内启动，请查看 {0}" -f (Join-Path $LogDir 'backend.err.log')) -ForegroundColor Red
}
if (-not $frontendOk) {
    Write-Host ("前端未能在规定时间内启动，请查看 {0}" -f (Join-Path $LogDir 'frontend.err.log')) -ForegroundColor Red
}

if (-not $backendOk -or -not $frontendOk) { exit 1 }

if (Test-Port $ProxyPort) {
    Write-Host ("  代理  {0}  已在运行，跳过" -f $ProxyPort) -ForegroundColor DarkGray
} else {
    Start-Process -FilePath $python -ArgumentList @($ProxyScript, '--port', "$ProxyPort", '--target', "$FrontendPort") `
        -WorkingDirectory $Root -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $LogDir 'proxy.log') `
        -RedirectStandardError (Join-Path $LogDir 'proxy.err.log') | Out-Null
    Write-Host ("  代理  {0}  启动中..." -f $ProxyPort) -ForegroundColor Gray
    if (-not (Wait-Port $ProxyPort)) {
        Write-Host ("HTTPS 代理启动失败，请查看 {0}" -f (Join-Path $LogDir 'proxy.err.log')) -ForegroundColor Red
    }
}

# ---------------- 输出访问地址 ----------------
$lanIps = @(Get-LanIps)
Write-Host ''
Write-Host '============================================================' -ForegroundColor Green
Write-Host ' 门禁终端已就绪' -ForegroundColor Green
Write-Host '============================================================' -ForegroundColor Green
Write-Host ' 电脑（本机）  : http://localhost:5173/terminal'
if ($lanIps.Count -gt 0) {
    foreach ($ip in $lanIps) {
        Write-Host (" 手机/平板     : https://{0}:{1}/terminal   （接受自签名证书后使用）" -f $ip, $ProxyPort)
    }
    Write-Host (" 后端接口文档  : http://{0}:{1}/docs" -f $lanIps[0], $BackendPort)
} else {
    Write-Host ' 未检测到局域网 IP，手机端暂不可用' -ForegroundColor Yellow
}
Write-Host (" 日志目录      : {0}" -f $LogDir)
Write-Host (' 停止服务      : powershell -ExecutionPolicy Bypass -File "{0}" -Stop' -f $PSCommandPath)
Write-Host '============================================================' -ForegroundColor Green

if (-not $NoBrowser) {
    Start-Process 'http://localhost:5173/terminal'
}
