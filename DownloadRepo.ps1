# Source URL
$url = "https://raw.githubusercontent.com/Zsweezzy/Post-Install-Script/main/PostInstall.py"
# Destation file
$dest = "$env:USERPROFILE\Downloads\PostInstall.py"
# Extract the directory path and create it if it doesn't exist
$dir = Split-Path $dest
if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir -Force
}
# Download the file
Invoke-WebRequest -Uri $url -OutFile $dest