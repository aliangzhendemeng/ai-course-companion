@echo off
REM AI 慕课学伴 一键启动脚本（Windows）
REM
REM 同时启动后端（:8000）与前端（:3000），自动打开浏览器。
REM 关闭本窗口即停止两个服务（请勿直接点右上角 X 后立即再次启动，先确认端口释放）。
REM
REM 用法：双击本文件，或在命令行运行  start_app.bat

setlocal
cd /d "%~dp0"

set BACKEND_PORT=8000
set FRONTEND_PORT=3000

REM ---- 依赖检查 ----
if not exist "venv\Scripts\python.exe" (
  echo [错误] 未找到后端虚拟环境 venv\。
  echo   请先执行： python -m venv venv ^&^& venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)
if not exist "frontend-next\node_modules" (
  echo [错误] 未找到前端依赖 frontend-next\node_modules。
  echo   请先执行： cd frontend-next ^&^& npm install
  pause
  exit /b 1
)

REM ---- 端口占用检查 ----
netstat -ano | findstr ":%BACKEND_PORT% " | findstr LISTENING >nul 2>&1
if %errorlevel%==0 (
  echo [错误] 端口 %BACKEND_PORT% 已被占用（后端需要）。请关闭占用程序后重试。
  pause
  exit /b 1
)
netstat -ano | findstr ":%FRONTEND_PORT% " | findstr LISTENING >nul 2>&1
if %errorlevel%==0 (
  echo [错误] 端口 %FRONTEND_PORT% 已被占用（前端需要）。请关闭占用程序后重试。
  pause
  exit /b 1
)

echo [启动] 后端  -^> http://localhost:%BACKEND_PORT%
start "AI慕课学伴-后端" /min cmd /c "venv\Scripts\python.exe run.py"

echo [启动] 前端  -^> http://localhost:%FRONTEND_PORT%
start "AI慕课学伴-前端" /min cmd /c "cd frontend-next && node_modules\.bin\next dev -p %FRONTEND_PORT%"

REM ---- 等待前端就绪后打开浏览器 ----
echo [启动] 等待前端就绪…
set /a COUNT=0
:waitloop
timeout /t 1 /nobreak >nul
curl -s -o nul http://localhost:%FRONTEND_PORT% 2>nul
if %errorlevel%==0 goto opened
set /a COUNT+=1
if %COUNT% LSS 60 goto waitloop
echo [提示] 前端启动较慢，请稍后手动访问 http://localhost:%FRONTEND_PORT%
goto done

:opened
echo [启动] 打开浏览器…
start "" http://localhost:%FRONTEND_PORT%

:done
echo.
echo [启动] 两个服务已启动（在独立的迷你窗口中运行）。
echo [提示] 关闭对应的"后端/前端"窗口即可停止服务。
echo.
pause
