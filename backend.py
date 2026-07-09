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
DRY_RUN = False

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


def run_cmd(cmd, shell=False, dry_run=None):
    if dry_run is None:
        dry_run = DRY_RUN
    debug_print("RUN_CMD", cmd, "shell=" + str(shell), "dry_run=" + str(dry_run))
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0)

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


def install_apps(entries, callback=None, dry_run=False):
    """Installiert die ausgewählten Anwendungen gebündelt via Winget.

    Args:
        entries (list[dict]): Eine Liste von App-Einträgen. Jeder Eintrag
            muss ein Dictionary mit dem Key `"winget"` (der Paket-ID) sein.
            Beispiel: `[{"id": "vlc", "name": "VLC", "winget": "VideoLAN.VLC"}]`
        callback (callable, optional): Callback für Fortschrittsaktualisierungen.
            Signature: callback(stage, step, total, message)
        dry_run (bool): Wenn True, werden die Befehle nur angezeigt, aber nicht ausgeführt.

    Returns:
        None
    """
    if not entries:
        debug_print("DEBUG: no apps to install, skipping winget")
        return

    total = len(entries)
    for index, entry in enumerate(entries, start=1):
        message = f"Installiere App: {entry.get('name', entry.get('winget'))}"
        debug_print(message)
        if callback:
            callback("install", index, total, message)

        cmd_list = ["winget", "install", entry["winget"], "--silent", "--accept-source-agreements", "--accept-package-agreements"]
        cmd_str = " ".join(cmd_list)
        debug_print("DEBUG:", cmd_str)
        run_cmd(cmd_list, shell=False, dry_run=dry_run)


def apply_settings(entries, callback=None, dry_run=False):
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
        callback (callable, optional): Callback für Fortschrittsaktualisierungen.
            Signature: callback(stage, step, total, message)
        dry_run (bool): Wenn True, werden die Befehle nur angezeigt, aber nicht ausgeführt.

    Returns:
        None
    """
    total_commands = sum(len(entry.get("commands", [])) for entry in entries)
    current = 0
    for entry in entries:
        if "commands" not in entry:
            continue
        for command in entry["commands"]:
            current += 1
            message = f"Ausführen: {command}"
            debug_print(message)
            if callback:
                callback("setting", current, total_commands, message)
            result = run_cmd(command, shell=True, dry_run=dry_run)
            if result.returncode != 0 and "on_error" in entry and not dry_run:
                debug_print(f"  [!] Fehler aufgetreten. Starte Fallback (on_error)...")
                for fallback_command in entry["on_error"]:
                    current += 1
                    debug_print(f"     -> Fallback ausführen: {fallback_command}")
                    if callback:
                        callback("setting", current, total_commands, fallback_command)
                    run_cmd(fallback_command, shell=True, dry_run=dry_run)
                debug_print(f"  -> Wiederhole Original-Befehl...")
                run_cmd(command, shell=True, dry_run=dry_run)


def uninstall_apps(entries, callback=None, dry_run=False):
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
        callback (callable, optional): Callback für Fortschrittsaktualisierungen.
            Signature: callback(stage, step, total, message)
        dry_run (bool): Wenn True, werden die Befehle nur angezeigt, aber nicht ausgeführt.

    Returns:
        None
    """
    total = 0
    for entry in entries:
        if "winget" in entry:
            total += 1
        elif "appx" in entry:
            total += len(entry["appx"])
    current = 0

    for entry in entries:
        if "winget" in entry:
            current += 1
            message = f"Deinstalliere App: {entry.get('name', entry.get('winget'))}"
            debug_print(message)
            if callback:
                callback("uninstall", current, total, message)
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
            run_cmd(cmd, shell=False, dry_run=dry_run)
        elif "appx" in entry:
            for appx_package in entry["appx"]:
                current += 1
                message = f"Deinstalliere AppX: {appx_package}"
                debug_print(message)
                if callback:
                    callback("uninstall", current, total, message)
                powershell_cmd = f'powershell -Command "Get-AppxPackage *{appx_package}* | Remove-AppxPackage"'
                debug_print(f"  -> AppX-Befehl: {powershell_cmd}")
                cmd = ["powershell", "-Command", f"Get-AppxPackage *{appx_package}* | Remove-AppxPackage"]
                run_cmd(cmd, shell=False, dry_run=dry_run)