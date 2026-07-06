# 1. Force Administrator privileges natively in PowerShell
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    Exit
}

# 2. Ensure Chocolatey is installed
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Chocolatey not found. Installing..." -ForegroundColor Cyan
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex (New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')
}

# 3. Install Python
Write-Host "Installing Python via Chocolatey..." -ForegroundColor Cyan
choco install python3 --yes --no-progress

# 4. Refresh environment paths mid-session
$Env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 5. Run your hosted Python script
Write-Host "Running Post-Install Python Script..." -ForegroundColor Cyan
irm "https://raw.githubusercontent.com/Zsweezzy/Post-Install-Script/main/PostInstall.py" | python -

Write-Host "Setup finished! All tasks complete." -ForegroundColor Green
Read-Host "Press Enter to exit"