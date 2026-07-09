"""Backend des Post Installers.

Dieses Modul stellt die Kernfunktionen zur Systemkonfiguration, App-Installation 
und Deinstallation bereit. Es wird direkt von der GUI (`gui.py`) aufgerufen.

Sämtliche Funktionen arbeiten zustandslos und erwarten Listen von Konfigurations-
Dictionaries (`dict`), die dynamisch aus der `config.json` geladen werden.

### JSON-Struktur der Einträge (Übersicht)
* **apps:** Enthält `winget` (String) als Paket-ID.
* **winsettings:** Enthält eine Liste von Shell-Befehlen unter `commands` sowie optionale Fallbacks unter `on_error`.
* **uninstalls:** Nutzt entweder `winget` (String) oder `appx` (Liste von Strings).
"""
# Definiert für pdoc, welche Funktionen öffentlich dokumentiert werden sollen.
__all__ = ["install_apps", "apply_settings", "uninstall_apps"]

import subprocess
import os
import platform
import sys

DEBUG = False
HIDE_CMD_WINDOW = True

ENV = os.environ.copy()
if platform.system() == "Windows":
    try:
        import winreg
    except ImportError:
        winreg = None

    system_paths = [
        os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32"),
        os.environ.get("SystemRoot", r"C:\Windows"),
        os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), r"System32\Wbem"),
        os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), r"System32\WindowsPowerShell\v1.0"),
    ]

    windows_apps = os.path.join(os.environ.get("LOCALAPPDATA", r"%LOCALAPPDATA%"), r"Microsoft\WindowsApps")
    if os.path.isdir(windows_apps):
        system_paths.append(windows_apps)

    registry_path = ""
    if winreg is not None:
        for hive, path_key in [
            (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
            (winreg.HKEY_CURRENT_USER, r"Environment"),
        ]:
            try:
                with winreg.OpenKey(hive, path_key) as key:
                    value, _ = winreg.QueryValueEx(key, "PATH")
                    if value:
                        registry_path += os.pathsep + value
            except OSError:
                continue

    current_path = ENV.get("PATH", "")
    all_paths = os.pathsep.join([p for p in system_paths if p])
    if registry_path:
        all_paths = os.pathsep.join([all_paths, registry_path.lstrip(os.pathsep)])
    if current_path:
        all_paths = os.pathsep.join([all_paths, current_path])
    ENV["PATH"] = all_paths


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def run_cmd(cmd, shell=False):
    startupinfo = None
    creationflags = 0
    if platform.system() == "Windows" and HIDE_CMD_WINDOW:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = subprocess.CREATE_NO_WINDOW

    try:
        return subprocess.run(cmd, shell=shell, env=ENV,
                              startupinfo=startupinfo,
                              creationflags=creationflags)
    except FileNotFoundError:
        if platform.system() == "Windows":
            if isinstance(cmd, (list, tuple)):
                cmd = subprocess.list2cmdline(cmd)
            return subprocess.run(cmd, shell=True, env=ENV,
                                  startupinfo=startupinfo,
                                  creationflags=creationflags)
        raise


def install_apps(entries):
    """Installiert die ausgewählten Anwendungen gebündelt via Winget.

    Args:
        entries (list[dict]): Eine Liste von App-Einträgen. Jeder Eintrag
            muss ein Dictionary mit dem Key `"winget"` (der Paket-ID) sein.
            Beispiel: `[{"id": "vlc", "name": "VLC", "winget": "VideoLAN.VLC"}]`

    Returns:
        None
    """
    if not entries:
        debug_print("DEBUG: no apps to install, skipping winget")
        return

    cmd_list = ["winget", "install"] + [entry["winget"] for entry in entries]
    cmd_str = subprocess.list2cmdline(cmd_list)
    debug_print("DEBUG:", cmd_str)
    run_cmd(cmd_str, shell=True) # Führt winget aus

def apply_settings(entries):
    """Wendet Windows-Systemeinstellungen via Registry (`reg add`) oder `powercfg` an.

    Die Funktion verarbeitet jeden Befehl nacheinander. Sollte ein Befehl fehlschlagen
    (Exit-Code != 0) und ein optionaler `"on_error"`-Fallback-Befehl im Eintrag
    hinterlegt sein, wird dieser ausgeführt, bevor der Originalbefehl erneut versucht wird.

    Args:
        entries (list[dict]): Eine Liste von Einstellungs-Einträgen.
            Erwartete Keys pro Dictionary:
            * `"name"` (str): Anzeigename der Einstellung.
            * `"commands"` (list[str]): Liste auszuführender Shell-Befehle.
            * `"on_error"` (list[str], optional): Fallback-Befehle bei Fehlern.

    Returns:
        None
    """
    for entry in entries:
        # Falls kein command da, dann überspringen
        if "commands" not in entry:
            continue
        debug_print(f"[Setting] Starte: {entry['name']}")
        for command in entry["commands"]:
            debug_print(f"Führe aus: {command}")
            result = run_cmd(command, shell=True) # Befehl ausführen
            if result.returncode != 0 and "on_error" in entry: # Wenn der Befehl fehlschlägt (Exit-Code ungleich 0) und ein Fallback existiert
                debug_print(f"  [!] Fehler aufgetreten. Starte Fallback (on_error)...")
                for fallback_command in entry["on_error"]:
                    debug_print(f"     -> Fallback ausführen: {fallback_command}")
                    run_cmd(fallback_command, shell=True)
                debug_print(f"  -> Wiederhole Original-Befehl...") # Nach dem Fallback versuchen wir den Originalbefehl einfach noch einmal
                run_cmd(command, shell=True)


def uninstall_apps(entries):
    """Deinstalliert Windows-Standard-Apps und Bloatware.

    Die Funktion unterscheidet automatisch zwischen zwei Deinstallations-Mechanismen:
    1. **Winget:** Nutzt die native Winget-Deinstallation über die Paket-ID.
    2. **AppX (PowerShell):** Nutzt eine PowerShell-Pipeline mit Wildcards (`*`),
       um auch versionsspezifische AppX-Pakete des aktuellen Benutzers restlos zu entfernen.

    Args:
        entries (list[dict]): Eine Liste von Deinstallations-Einträgen.
            Erwartete Keys pro Dictionary:
            * `"name"` (str): Name der zu entfernenden App.
            * `"winget"` (str, optional): Winget ID der Anwendung.
            * `"appx"` (list[str], optional): Liste von AppX-Paketnamen.

    Returns:
        None
    """
    for entry in entries:
        debug_print(f"[Uninstall] Starte Deinstallation für: {entry['name']}")
        if "winget" in entry: # Fall 1: Deinstallation via Winget
            winget_id = entry["winget"]
            cmd = [
                "winget",
                "uninstall",
                "--id",
                winget_id,
                "--silent",
                "--accept-source-agreements",
            ]
            debug_print(f"  -> Winget-Befehl: {' '.join(cmd)}")
            run_cmd(cmd, shell=False)
        
        elif "appx" in entry: # Fall 2: Deinstallation via AppX (PowerShell)
            for appx_package in entry["appx"]: # Da 'appx' eine Liste ist, gehen wir jeden Paketnamen einzeln durch  
                powershell_cmd = f"powershell -Command \"Get-AppxPackage *{appx_package}* | Remove-AppxPackage\"" # Get-AppxPackage sucht das Paket, Remove-AppxPackage löscht es für den aktuellen User
                debug_print(f"  -> AppX-Befehl: {powershell_cmd}")
                run_cmd(powershell_cmd, shell=True)