## Features

## Install
to install the application run 
```shell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest 'https://raw.githubusercontent.com/Zsweezzy/Post-Install-Script/main/InstallPythonRunFile.bat' -OutFile 'C:\Users\Public\install.bat'; Start-Process cmd.exe -ArgumentList '/c', 'C:\Users\Public\install.bat' -Wait; Remove-Item 'C:\Users\Public\install.bat' -ErrorAction SilentlyContinue"
```
inside your Powershell
