## Features planned
- A Tab mode to witch tabs between Gaming mode and "Enterprise" mode to have different options available for power, telemetry and apps.
- The Gaming mode should include registry edits for power consumptions, timeouts, gaming settings and telemetry. It should also include apps for gaming (e.g. MSI Afterburner, RTSS, CapFrameX and more).
- The Enterprise Tab will have options regarding microsoft products and other popular open-source options
- A config import and export option for quick configuration of apps to install and settings to change
- A default app uninstaller. 

## How it works

When first installing the script it tries to install chocolately if it isn't installed already. After doing so it uses Chocolately to install python to open the python file inside this repo. The Python file the opens the Post Installer itself. You then pick the apps you want to uninstall or install and the settings you want to get changed inside your windows.

## Install

to install the application run

```shell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest 'https://raw.githubusercontent.com/Zsweezzy/Post-Install-Script/main/InstallPythonRunFile.bat' -OutFile 'C:\Users\Public\install.bat'; Start-Process cmd.exe -ArgumentList '/c', 'C:\Users\Public\install.bat' -Wait; Remove-Item 'C:\Users\Public\install.bat' -ErrorAction SilentlyContinue"
```

inside your Powershell
