@echo off
echo 运行批量标注工具演示...
echo.

REM 检查虚拟环境是否存在
if not exist venv (
    echo 虚拟环境不存在，正在创建...
    python -m venv venv
    echo 虚拟环境创建完成
)

REM 激活虚拟环境
call venv\Scripts\activate

REM 检查是否已安装依赖
pip list | findstr "batch-annotation-tool" > nul
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -e .
)

REM 创建输出目录
if not exist demo_output mkdir demo_output

REM 运行演示
python demo.py %*

REM 如果出错，暂停以查看错误信息
if errorlevel 1 (
    echo.
    echo 运行出错，请查看上面的错误信息
    pause
) else (
    echo.
    echo 演示运行完成，按任意键退出...
    pause > nul
)