@echo off
chcp 65001 >nul
echo ========================================
echo EAIP Viewer - Windows 打包工具
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo [1/3] 检查依赖...
python -c "import nuitka" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Nuitka 未安装，正在安装...
    pip install nuitka ordered-set zstandard
    if errorlevel 1 (
        echo [错误] 安装失败
        pause
        exit /b 1
    )
)

echo [2/3] 检查项目依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 安装项目依赖失败
    pause
    exit /b 1
)

echo [3/3] 开始打包...
echo.
python build_windows.py

pause
