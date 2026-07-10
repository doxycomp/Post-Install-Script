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

(
  echo ==========================================
  echo   POST INSTALLER
  echo ==========================================
  echo.
  echo   Es werden jetzt:
  echo    - Chocolatey installiert ^(falls noetig^)
  echo    - Python installiert
  echo    - ein Setup-Skript aus dem Internet geladen und ausgefuehrt
  echo.
  echo   Quelle: github.com/Zsweezzy/Post-Install-Script
  echo.
)

choice /C YN /T 10 /D N /M "Are you sure you want to start the setup and download?"
if errorlevel 2 (
echo not available
exit /b
)

(
echo ==========================================
echo   Starting Environment Setup
echo ==========================================
)

:: 2. Ensure Chocolatey is installed
choco -v >nul 2>&1
if %errorLevel% neq 0 (
    echo Chocolatey not found. Installing...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
)

:: 3. Install Python and Git via Chocolatey
echo Installing Python and Git via Chocolatey...
choco install python3 git --yes --no-progress

:: 4. Refresh environment paths so 'git' and 'python' work immediately
echo Refreshing Environment Path...
set "PATH=%SystemRoot%\system32;%SystemRoot%;%SystemRoot%\System32\Wbem;%SYSTEMROOT%\System32\WindowsPowerShell\v1.0\"
for /f "skip=2 tokens=1,2*" %%A in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "PATH=%%C"
for /f "skip=2 tokens=1,2*" %%A in ('reg query "HKCU\Environment" /v Path') do set "PATH=%PATH%;%%C"

(
echo ==========================================
echo   Cloning Repository and Running Script
echo ==========================================
)

:: 5. Define Repository Target
set "REPO_URL=https://github.com/Zsweezzy/Post-Install-Script.git"
set "FOLDER_NAME=Post-Install-Script"

:: If folder already exists, delete it or pull updates. We delete it here for a clean install.
if exist "%FOLDER_NAME%" rd /s /q "%FOLDER_NAME%"

:: Clone the repo
git clone %REPO_URL%

:: Move into the cloned directory
cd %FOLDER_NAME%

set "expected=03205AFFB3F5F89D9A8A2755FD866E9C73EDA3CC9EBD7F9FA7851015F11AB3CE"
powershell -NoProfile -Command ^
"
$actual = (Get-FileHash .\PostInstall.py).Hash
if ($actual -ne '%EXPECTED%') {
Write-Host 'ERROR NOT SO FAST!!!!111' -ForegroundColor Red
exit 1
}
"
if errorlevel 1 (
exit /b
)
echo "Geht klar"

:: 6. Optional: Install requirements if you have a requirements.txt file
if exist "requirements.txt" (
    echo Installing required Python packages...
    pip install -r requirements.txt --quiet
)

:: 7. Run the local Python file
if exist "%~dp0\pythonw.exe" (
    echo Launching PostInstaller GUI in windowless mode...
    pythonw PostInstall.py
) else (
    echo Launching PostInstaller GUI...
    python PostInstall.py
)

echo.
echo Setup finished!