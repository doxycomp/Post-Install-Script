@echo off
:: 1. Check for Administrator Privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :run_script
) else (
    echo Requesting Administrator privileges...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:run_script
:: Move to the folder where the batch file is running
cd /d "%~dp0"
set "temp_ps1=%temp%\temp_post_install.ps1"

echo Creating temporary script...

:: 2. Write PowerShell code to temporary file
(
echo # 1. Ensure Chocolatey is installed
echo if ^(-not ^(Get-Command choco -ErrorAction SilentlyContinue^)^) {
echo     Write-Host "Chocolatey not found. Installing..." -ForegroundColor Cyan
echo     Set-ExecutionPolicy Bypass -Scope Process -Force
echo     [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
echo     iex ^(New-Object System.Net.WebClient^).DownloadString^('https://community.chocolatey.org/install.ps1'^)
echo }
echo.
echo # 2. Install Python
echo Write-Host "Installing Python via Chocolatey..." -ForegroundColor Cyan
echo choco install python3 --yes --no-progress
echo.
echo # 3. Refresh environment paths mid-session
echo $Env:Path = [System.Environment]::GetEnvironmentVariable^("Path","Machine"^) + ";" + [System.Environment]::GetEnvironmentVariable^("Path","User"^)
echo.
echo # 4. Run your hosted Python script
echo Write-Host "Running Post-Install Python Script..." -ForegroundColor Cyan
echo irm "https://raw.githubusercontent.com/Zsweezzy/Post-Install-Script/main/PostInstall.py" ^| python -
) > "%temp_ps1%"

:: 3. Execute PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -File "%temp_ps1%"

:: 4. Cleanup temporary files
if exist "%temp_ps1%" del "%temp_ps1%"

echo.
echo Setup finished!
pause