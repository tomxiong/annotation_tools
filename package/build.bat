@echo off
echo === 全景图像标注工具打包脚本 ===

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python环境，请先安装Python
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist ".venv" (
    echo 创建虚拟环境...
    python -m venv .venv
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 安装依赖
echo 正在安装依赖...
pip install -r requirements.txt

REM 构建可执行文件
echo 正在构建可执行文件...
python build.py

echo.
echo 打包完成!
echo 可执行文件位置: .\dist\
echo.
pause