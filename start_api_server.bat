@echo off
chcp 65001 >nul
echo ========================================
echo 启动抖音视频解析 HTTP API 服务
echo ========================================

REM 检查虚拟环境是否存在
if not exist ".venv\Scripts\activate.bat" (
    echo 错误: 未找到虚拟环境，请先运行 setup-douyin-mcp.ps1
    pause
    exit /b 1
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 检查依赖是否安装
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements_api.txt
)

REM 设置环境变量（可选）
REM set DASHSCOPE_API_KEY=你的API密钥

REM 启动服务
echo.
echo 服务启动中...
echo API 地址: http://127.0.0.1:8000
echo API 文档: http://127.0.0.1:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

REM 优先使用完整功能版本
if exist "douyin_analysis_api_server.py" (
    python douyin_analysis_api_server.py
) else (
    python douyin_api_server.py
)

pause
