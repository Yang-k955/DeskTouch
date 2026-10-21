@echo off
setlocal
cd /d "%~dp0"

rem 1) 优先使用已打包的成品（按版本号从新到旧）
for /f "delims=" %%D in ('dir /b /ad /o-n "outputs\release-*" 2^>nul') do (
  if exist "outputs\%%D\DeskTouch\DeskTouch.exe" (
    start "" "outputs\%%D\DeskTouch\DeskTouch.exe" %*
    exit /b 0
  )
)
if exist "outputs\release\DeskTouch\DeskTouch.exe" (
  start "" "outputs\release\DeskTouch\DeskTouch.exe" %*
  exit /b 0
)

rem 2) 回退到源码运行，优先无控制台的 pythonw
where pythonw >nul 2>nul
if not errorlevel 1 (
  start "" pythonw "%~dp0DeskTouch.py" %*
  exit /b 0
)
where pyw >nul 2>nul
if not errorlevel 1 (
  start "" pyw "%~dp0DeskTouch.py" %*
  exit /b 0
)

echo.
echo 未找到 Python（需要含 tkinter 的 3.11+）。
echo 安装后执行: pip install -r requirements.txt
echo.
pause
exit /b 1
