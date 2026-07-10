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

echo ==========================================
echo   Starting Environment Setup
echo ==========================================

:: === NEU: Sicherheitsabfrage vor dem Download/Setup ===
echo [?] Done preparing.
set /p answer="Are you sure you want to start the setup and download? (Y/N): "
if /i "%answer%" neq "Y" (
    echo.
    echo [-] Setup terminated. Script will now close.
    pause
    exit /b
)
echo [+] Setup confirmed. Processing...
echo ------------------------------------------

:: 2. Ensure Chocolatey is installed
echo Checking if Chocolatey is installed...
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

echo ==========================================
echo   Cloning Repository and Running Script
echo ==========================================

:: 5. Define Repository Target
set "REPO_URL=https://github.com/Zsweezzy/Post-Install-Script.git"
set "FOLDER_NAME=Post-Install-Script"
set "RAW_INSTALLER_URL=https://raw.githubusercontent.com/Zsweezzy/Post-Install-Script/main/InstallPythonRunFile.bat"
set "RAW_MAIN_SCRIPT_URL=https://raw.githubusercontent.com/Zsweezzy/Post-Install-Script/main/PostInstall.py"

:: If folder already exists, delete it or pull updates. We delete it here for a clean install.
echo Checking if the folder "%FOLDER_NAME%" exists...
if exist "%FOLDER_NAME%" rd /s /q "%FOLDER_NAME%"

:: Clone the repo
echo Cloning the repository from %REPO_URL%...
git clone %REPO_URL%

:: Move into the cloned directory
echo moving into the folder "%FOLDER_NAME%"...
cd %FOLDER_NAME%

:: Verify the downloaded main script against GitHub raw content
if exist "%~dp0\check_remote_hash.py" (
    echo Checking downloaded main script against GitHub raw content...
    python "%~dp0\check_remote_hash.py" "%RAW_MAIN_SCRIPT_URL%" "%~dp0%FOLDER_NAME%\PostInstall.py"
    if errorlevel 1 (
        echo [X] Main script hash check failed.
        pause
        exit /b 1
    )
)

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