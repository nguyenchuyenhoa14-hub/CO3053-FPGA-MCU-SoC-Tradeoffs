@echo off
rem ===========================================================================
rem  1-CLICK DEMO BENCHMARK RUNNER (CO3053 EMBEDDED SYSTEMS)
rem ===========================================================================
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

python run_demo.py
if %errorlevel% neq 0 (
    echo [ERROR] Demo execution encountered errors.
    pause
    exit /b %errorlevel%
)

echo.
echo Press any key to open GTKWave with fir_simulation.vcd (or close this window)...
pause > nul

if exist "C:\iverilog\gtkwave\bin\gtkwave.exe" (
    start "" "C:\iverilog\gtkwave\bin\gtkwave.exe" outputs\fir_simulation.vcd
)
