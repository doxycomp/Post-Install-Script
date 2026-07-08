"""Backend des Post Installers — hier arbeitet Maxi. :)

Die GUI (gui.py) ruft genau diese drei Funktionen auf. Jede bekommt eine
Liste von Einträgen aus der config.json übergeben — normale dicts, kein OOP
nötig. Jeder Eintrag hat "id" und "name", App-Einträge zusätzlich "choco"
(den Chocolatey-Paketnamen).

Welche Felder ein Eintrag hat, steht in der config.json:
    apps:        "choco" und "winget" (Paketnamen, einer reicht zum Installieren)
    winsettings: "commands" (Liste von Shell-Befehlen: reg add / powercfg)
    uninstalls:  "winget" (Paketname) ODER "appx" (Liste von AppX-Paketnamen
                 für Remove-AppxPackage)
"""


def install_apps(entries):
    """Installiert die angehakten Apps (z. B. via winget/choco install)."""
    for entry in entries:
        # TODO(Maxi): winget oder choco install aufrufen, Exit-Code prüfen, loggen
        print(f"[install] {entry['name']} (winget: {entry.get('winget')}, choco: {entry.get('choco')})")


def apply_settings(entries):
    """Wendet die eingeschalteten Windows-Settings an (Registry/powercfg)."""
    for entry in entries:
        for command in entry["commands"]:
            # TODO(Maxi): Befehl ausführen (subprocess.run), Exit-Code prüfen, loggen
            print(f"[setting] {entry['name']}: {command}")


def uninstall_apps(entries):
    """Deinstalliert die angehakten Standard-Apps."""
    for entry in entries:
        # TODO(Maxi): "winget" -> winget uninstall, "appx" -> Remove-AppxPackage
        targets = entry.get("winget") or entry.get("appx")
        print(f"[uninstall] {entry['name']} -> {targets}")
