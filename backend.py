"""Backend des Post Installers — hier arbeitet Maxi. :)

Die GUI (gui.py) ruft genau diese drei Funktionen auf. Jede bekommt eine
Liste von Einträgen aus der config.json übergeben — normale dicts, kein OOP
nötig. Jeder Eintrag hat "id" und "name", App-Einträge zusätzlich "choco"
(den Chocolatey-Paketnamen).

Beispiel-Eintrag aus "apps":
    {"id": "app_7zip", "name": "7-Zip", "choco": "7zip"}
"""


def install_apps(entries):
    """Installiert die angehakten Apps (z. B. via choco install <name>)."""
    for entry in entries:
        # TODO(Maxi): choco install aufrufen, Exit-Code prüfen, loggen
        print(f"[install] {entry['name']} (choco: {entry['choco']})")


def apply_settings(entries):
    """Wendet die eingeschalteten Windows-Settings an (Registry/powercfg)."""
    for entry in entries:
        # TODO(Maxi): je nach entry["id"] das passende Regedit/Kommando ausführen
        print(f"[setting] {entry['name']} ({entry['id']})")


def uninstall_apps(entries):
    """Deinstalliert die angehakten Standard-Apps."""
    for entry in entries:
        # TODO(Maxi): Deinstallation, z. B. via winget uninstall / Remove-AppxPackage
        print(f"[uninstall] {entry['name']} ({entry['id']})")
