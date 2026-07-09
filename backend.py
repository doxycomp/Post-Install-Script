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

def install_apps(entries):
    """Installiert die ausgewählten Anwendungen gebündelt via Winget.

    Args:
        entries (list[dict]): Eine Liste von App-Einträgen. Jeder Eintrag
            muss ein Dictionary mit dem Key `"winget"` (der Paket-ID) sein.
            Beispiel: `[{"id": "vlc", "name": "VLC", "winget": "VideoLAN.VLC"}]`

    Returns:
        None
    """
    # kopieren der Basis-Liste, damit bei mehrmaligem Aufruf nicht die alten Apps nerven
    cmd_list = ["winget", "install"] + [entry["winget"] for entry in entries]
    print("DEBUG:", " ".join(cmd_list))
    subprocess.run(cmd_list, shell=True) # Führt winget aus

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
        print(f"[Setting] Starte: {entry['name']}")
        for command in entry["commands"]:
            print(f"Führe aus: {command}")
            result = subprocess.run(command, shell=True) # Befehl ausführen
            if result.returncode != 0 and "on_error" in entry: # Wenn der Befehl fehlschlägt (Exit-Code ungleich 0) und ein Fallback existiert
                print(f"  [!] Fehler aufgetreten. Starte Fallback (on_error)...")
                for fallback_command in entry["on_error"]:
                    print(f"     -> Fallback ausführen: {fallback_command}")
                    subprocess.run(fallback_command, shell=True)
                print(f"  -> Wiederhole Original-Befehl...") # Nach dem Fallback versuchen wir den Originalbefehl einfach noch einmal
                subprocess.run(command, shell=True)


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
        print(f"[Uninstall] Starte Deinstallation für: {entry['name']}")
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
            print(f"  -> Winget-Befehl: {' '.join(cmd)}")
            subprocess.run(cmd, shell=True)
        
        elif "appx" in entry: # Fall 2: Deinstallation via AppX (PowerShell)
            for appx_package in entry["appx"]: # Da 'appx' eine Liste ist, gehen wir jeden Paketnamen einzeln durch  
                powershell_cmd = f"powershell -Command \"Get-AppxPackage *{appx_package}* | Remove-AppxPackage\"" # Get-AppxPackage sucht das Paket, Remove-AppxPackage löscht es für den aktuellen User
                print(f"  -> AppX-Befehl: {powershell_cmd}")
                subprocess.run(powershell_cmd, shell=True)