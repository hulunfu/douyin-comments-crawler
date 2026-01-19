# PowerShell 启动脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "启动抖音视频解析 HTTP API 服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 检查虚拟环境
if (-Not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Error "未找到虚拟环境，请先运行 setup-douyin-mcp.ps1"
    exit 1
}

# 激活虚拟环境
. .venv\Scripts\Activate.ps1

# 检查依赖
try {
    python -c "import fastapi" 2>$null
} catch {
    Write-Host "正在安装依赖..." -ForegroundColor Yellow
    pip install -r requirements_api.txt
}

# 设置环境变量（可选）
# $env:DASHSCOPE_API_KEY = "你的API密钥"

# 启动服务
Write-Host ""
Write-Host "服务启动中..." -ForegroundColor Green
Write-Host "API 地址: http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "API 文档: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

# 优先使用完整功能版本
if (Test-Path "douyin_analysis_api_server.py") {
    python douyin_analysis_api_server.py
} else {
    python douyin_api_server.py
}
