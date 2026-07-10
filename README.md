# Post Install Script

A powerful Windows post-installation utility with a modern Tkinter GUI, automated app installation, Windows registry tweaks, app removal, and a customizable theme layer.

## What this does

- Installs apps using `winget`
- Applies Windows settings via `reg add` and `powercfg`
- Removes built-in Windows apps and bloatware using `winget` or AppX uninstalls
- Automatically installs Git, Python and Chocolatey if needed
- Runs the UI without leaving an extra console window open
- Stores theme and debug preferences in `gui_settings.json`
- Loads app/settings/uninstall definitions from `config.json`
- Supports presets and save/load of your selected items

## Quick install

Open PowerShell as Administrator and run:

```powershell
powershell -nop -ep bypass -c "Invoke-WebRequest 'https://raw.githubusercontent.com/Zsweezzy/Post-Install-Script/main/InstallPythonRunFile.bat' -OutFile 'C:\Users\Public\install.bat'; Start-Process cmd.exe -ArgumentList '/c', 'C:\Users\Public\install.bat' -Wait; Remove-Item 'C:\Users\Public\install.bat' -ea 0"
```

This does the following:

1. Elevates to Administrator privileges
2. Installs Chocolatey if it is missing
3. Installs Python and Git via Chocolatey
4. Clones the repository from GitHub
5. Launches `PostInstall.py` through `pythonw` when available so no extra console window remains

## How to use it

1. Start the app from `PostInstall.py` or via `InstallPythonRunFile.bat`
2. Browse the tabs and choose the apps, Windows tweaks, or uninstall actions you want
3. Use `Alles abwählen` to clear all selections instantly
4. Use `Speichern` to export the selected items to a JSON preset
5. Use `Laden` to import a previously saved preset
6. Click `Go!` to execute the selected actions
7. Watch progress in the progress bar and read the stage text
8. Close the completion popup when finished
9. Use the per-tab search box (top of the sidebar) to quickly filter items
  by name, id, description or compatibility. The search is case-insensitive
  and filters only the currently selected category within the active tab.

## UI overview

### Tabs

- **Apps**
  - Select applications to install
  - Categories like Office, Browser, Tools, and Gaming are loaded from `config.json`

- **Reg/WinSettings**
  - Apply Windows settings and tweaks
  - Executes registry changes and power plan commands
  - Includes categories such as Power, Gaming, Privacy, and Explorer

- **Uninstalls**
  - Remove built-in Microsoft apps and bloatware
  - Uses `winget uninstall` when available or AppX removal for system apps

- **App Settings**
  - Customize the GUI appearance and behavior
  - Change theme, accent, font, transparency, rounded corners, and emoji icons
  - Enable `Debug` mode to show backend output and keep command windows visible

### Footer actions

- `Alles abwählen` — deselects every checkbox in the current selection state
- `Speichern` — saves the current selection as a JSON preset
- `Laden` — loads a saved preset from disk
- `Go!` — runs the selected install/settings/uninstall actions

### Search

- Each main tab (Apps / Reg/WinSettings / Uninstalls) has a small search box
  at the top of the left sidebar. Typing there filters the entries shown for
  the currently selected category. The search looks at `name`, `id`,
  `description` and `compatibility` fields from `config.json`.

### Progress and feedback

- The footer includes a determinate progress bar
- The status text updates with the current command or install stage
- When the run completes, a popup window confirms success

## Supported workflows

### Install example apps

Try installing combinations of these popular apps:

- `LibreOffice` — full office suite
- `Firefox` — browser
- `PowerToys` — Windows power user utilities
- `Steam` — game launcher

### Apply example system tweaks

Useful Windows configuration changes:

- `Energiesparplan: Höchstleistung` — set the power plan to high performance
- `Standby-Timeout deaktivieren` — prevent sleep on AC power
- `Telemetrie reduzieren` — lower telemetry collection
- `Windows Dark Mode` — enable dark mode for apps and system UI

### Uninstall example apps

Remove common Windows preinstalled bloat:

- `OneDrive` — uninstall Microsoft OneDrive AppX package
- `Xbox Apps` — remove Xbox-related built-in apps
- `Candy Crush` — remove Candy Crush Flash or Saga bloatware
- `Microsoft News / Wetter` — uninstall built-in news and weather apps

## Configuration files

- `config.json`
  - Defines all available apps, Windows settings, and uninstall entries
  - The GUI is built dynamically from this file
  - Adding or removing options only requires editing this JSON file

- `gui_settings.json`
  - Saves theme, accent, font, transparency, rounded corners, icons, and debug mode
  - Automatically loaded at startup

- `presets/*.json`
  - Built-in selection presets
  - Use the preset buttons in the app header to load a preset quickly

## Backend behavior

- `backend.py` handles all execution logic
- `winget` commands are executed with a robust PATH setup for Windows
- If `winget` is not directly executable, the backend falls back to shell execution
- `apply_settings` runs each configured command and optionally retries with fallback commands stored in `on_error`
- `uninstall_apps` supports both `winget` and AppX removal pipelines

## Dependencies and imports

- Runtime: Python 3.11 or newer
- No mandatory external Python packages are required for normal operation
- Standard library imports used by the project:
  - `about.py`: `base64`, `io`, `json`, `math`, `random`, `threading`, `time`, `tkinter`, `urllib.request`, `wave`, `pathlib.Path`
  - `backend.py`: `subprocess`, `os`, `platform`, `sys`, `winreg` (only on Windows)
  - `gui.py`: `ctypes`, `json`, `random`, `threading`, `tkinter`, `tkinter.font`, `pathlib.Path`, `tkinter.colorchooser`, `tkinter.filedialog`, `tkinter.messagebox`, `tkinter.ttk`
  - `PostInstall.py`: `gui`
- External tools and Windows requirements:
  - `winget` for app install/uninstall actions
  - `PowerShell` for AppX removal and installer bootstrap commands
  - `Chocolatey`, `Python`, and `Git` are installed automatically when using `InstallPythonRunFile.bat`
- Optional extras from `pyproject.toml`:
  - `music`: `libxmplite` for tracker music in the about window
  - `dev`: `ruff`, `pdoc` for development and documentation

## Tools and apps used

- Development environment: `Visual Studio Code`
- Python runtime used during development: `Python 3.14` (compatible with Python 3.11+)
- Version control: `Git` and `GitHubDesktop`
- Windows package tools: `winget`, `PowerShell`, `Chocolatey`
- AI-assisted authoring and review tools referenced in this project: GitHub Copilot, Claude Fable 5 and Google Gemini,

## Recommended examples

### Example 1: Fresh browser + utilities

1. Select `Firefox`
2. Select `PowerToys`
3. Click `Go!`

### Example 2: Gaming PC setup

1. Select `Steam`
2. Select `Discord`
3. Select `MSI Afterburner`
4. Apply `Windows Game Mode aktivieren`
5. Click `Go!`

### Example 3: Productivity setup

1. Select `LibreOffice`
2. Select `Sumatra PDF`
3. Select `Everything (Suche)`
4. Apply `Dateiendungen anzeigen`
5. Click `Go!`

### Example 4: Clean Windows cleanup

1. Select `OneDrive`
2. Select `Xbox Apps`
3. Select `Candy Crush`
4. Click `Go!`

## Notes

- This tool is designed for Windows only
- Run the installer as Administrator for the best result
- `winget` and `PowerShell` are required for app management and AppX removal
- Debug mode is helpful if a command fails or if you want to see the execution window

## Contributing

Feel free to extend `config.json` with more apps, settings, or uninstall entries. The app UI will update automatically when the configuration changes.

## License

This repository is released under the terms of its included `LICENSE`.