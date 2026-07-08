"""Frontend für den Post Installer.

Liest config.json (App-Katalog, Windows-Settings, Uninstalls) und baut
daraus die komplette Oberfläche — nichts ist hartkodiert. Neue Apps oder
Settings kommen also nur in die config.json, nicht hierher.

Anbindung ans Backend (backend.py) über drei einfache Funktionen:

    backend.install_apps(entries)    # Liste von dicts aus config.json ("apps")
    backend.apply_settings(entries)  # dito ("winsettings")
    backend.uninstall_apps(entries)  # dito ("uninstalls")

Jeder Eintrag hat mindestens "id" und "name", App-Einträge zusätzlich
"choco" (Chocolatey-Paketname). Mehr muss das Backend nicht wissen.
"""

import ctypes
import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    import backend
except ImportError:
    backend = None

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
PRESET_DIR = BASE_DIR / "presets"

# ---------------------------------------------------------------- Farben ----
# Angelehnt an den Windows-11-Dark-Look
BG = "#202020"          # Fensterhintergrund
BG_CARD = "#2b2b2b"     # Karten/Zeilen
BG_SIDEBAR = "#191919"  # linke Navigation
BG_HOVER = "#303030"
BG_ACTIVE = "#1f3a56"   # aktiver Sidebar-Eintrag (Steam-Look)
ACCENT = "#60cdff"      # Windows-11-Akzentblau
TEXT = "#f0f0f0"
TEXT_DIM = "#9d9d9d"

FONT = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 8)
FONT_TITLE = ("Segoe UI Semibold", 16)

# Auswahl-Zustand der gesamten GUI:
#   VARS[id]    -> tk.BooleanVar (Checkbox/Schalter an oder aus)
#   ENTRIES[id] -> ("apps"|"winsettings"|"uninstalls", eintrag-dict)
VARS = {}
ENTRIES = {}


def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def enable_dark_titlebar(root):
    """Windows 11: auch die Titelleiste dunkel schalten (best effort)."""
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), 4)
    except Exception:
        pass  # auf älteren Windows-Versionen einfach hell lassen


# ------------------------------------------------------------- Widgets ----

class Toggle(tk.Canvas):
    """Kleiner Ein/Aus-Schalter im Windows-11-Stil (Canvas-basiert)."""

    def __init__(self, parent, variable, bg=BG_CARD):
        super().__init__(parent, width=44, height=22, bg=bg,
                         highlightthickness=0, cursor="hand2")
        self.variable = variable
        self.bind("<Button-1>", lambda _e: self.variable.set(not self.variable.get()))
        variable.trace_add("write", lambda *_: self._draw())
        self._draw()

    def _draw(self):
        self.delete("all")
        on = self.variable.get()
        track = ACCENT if on else "#4d4d4d"
        # Track: zwei Kreise + Rechteck ergeben eine abgerundete Pille
        self.create_oval(1, 1, 21, 21, fill=track, outline=track)
        self.create_oval(23, 1, 43, 21, fill=track, outline=track)
        self.create_rectangle(11, 1, 33, 21, fill=track, outline=track)
        # Knopf
        x = 26 if on else 4
        knob = "#101010" if on else "#c5c5c5"
        self.create_oval(x, 4, x + 14, 18, fill=knob, outline=knob)


def scrollable_frame(parent, bg=BG):
    """Vertikal scrollbarer Bereich; gibt den inneren Frame zurück."""
    canvas = tk.Canvas(parent, bg=bg, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=bg)
    window = canvas.create_window((0, 0), window=inner, anchor="nw")

    inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
    canvas.configure(yscrollcommand=scrollbar.set)

    def _on_wheel(event):
        canvas.yview_scroll(-1 * (event.delta // 120), "units")

    canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _on_wheel))
    canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return inner


def get_var(entry_id, kind, entry):
    """BooleanVar für einen Config-Eintrag anlegen (oder wiederverwenden)."""
    if entry_id not in VARS:
        VARS[entry_id] = tk.BooleanVar(value=False)
        ENTRIES[entry_id] = (kind, entry)
    return VARS[entry_id]


def build_entry_row(parent, entry, kind, use_toggle):
    """Eine Zeile im Content-Bereich: Name links, Schalter/Checkbox."""
    row = tk.Frame(parent, bg=BG_CARD)
    row.pack(fill="x", pady=3, padx=2)
    var = get_var(entry["id"], kind, entry)

    if use_toggle:
        tk.Label(row, text=entry["name"], bg=BG_CARD, fg=TEXT, font=FONT,
                 anchor="w").pack(side="left", fill="x", expand=True, padx=12, pady=9)
        Toggle(row, var).pack(side="right", padx=12)
    else:
        check = tk.Checkbutton(row, text=entry["name"], variable=var,
                               bg=BG_CARD, fg=TEXT, font=FONT, anchor="w",
                               activebackground=BG_CARD, activeforeground=TEXT,
                               selectcolor=BG_SIDEBAR, highlightthickness=0, bd=0)
        check.pack(side="left", fill="x", expand=True, padx=8, pady=6)


def build_split_tab(notebook, title, sections, kind, use_toggle=False):
    """Ein Tab mit Steam-artiger Sidebar links und Content rechts."""
    tab = tk.Frame(notebook, bg=BG)
    notebook.add(tab, text=f"  {title}  ")

    sidebar = tk.Frame(tab, bg=BG_SIDEBAR, width=185)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    content_holder = tk.Frame(tab, bg=BG)
    content_holder.pack(side="left", fill="both", expand=True, padx=(16, 8), pady=12)

    tk.Label(sidebar, text="KATEGORIEN", bg=BG_SIDEBAR, fg=TEXT_DIM,
             font=FONT_SMALL, anchor="w", padx=16, pady=10).pack(fill="x")

    labels = {}

    def select(category):
        for cat, lbl in labels.items():
            active = cat == category
            lbl.configure(bg=BG_ACTIVE if active else BG_SIDEBAR,
                          fg=TEXT if active else TEXT_DIM)
        for child in content_holder.winfo_children():
            child.destroy()
        inner = scrollable_frame(content_holder)
        tk.Label(inner, text=category, bg=BG, fg=TEXT, font=FONT_TITLE,
                 anchor="w").pack(fill="x", pady=(0, 10))
        for entry in sections[category]:
            build_entry_row(inner, entry, kind, use_toggle)

    def make_label(category):
        lbl = tk.Label(sidebar, text=category, bg=BG_SIDEBAR, fg=TEXT_DIM,
                       font=FONT, anchor="w", padx=16, pady=8, cursor="hand2")
        lbl.pack(fill="x")
        lbl.bind("<Button-1>", lambda _e: select(category))
        lbl.bind("<Enter>", lambda _e: lbl["bg"] == BG_SIDEBAR and lbl.configure(bg=BG_HOVER))
        lbl.bind("<Leave>", lambda _e: lbl["bg"] == BG_HOVER and lbl.configure(bg=BG_SIDEBAR))
        labels[category] = lbl

    for category in sections:
        make_label(category)
    if sections:
        select(next(iter(sections)))


# ------------------------------------------------------ Presets & Save ----

def apply_selection(selected_ids):
    """Alles abwählen, dann die übergebenen IDs anhaken."""
    for var in VARS.values():
        var.set(False)
    unknown = [i for i in selected_ids if i not in VARS]
    for entry_id in selected_ids:
        if entry_id in VARS:
            VARS[entry_id].set(True)
    if unknown:
        messagebox.showwarning(
            "Unbekannte Einträge",
            "Diese IDs stehen nicht (mehr) in der config.json:\n" + "\n".join(unknown))


def load_preset(path):
    with open(path, encoding="utf-8") as f:
        preset = json.load(f)
    apply_selection(preset.get("selected", []))


def save_selection():
    path = filedialog.asksaveasfilename(
        defaultextension=".json", filetypes=[("JSON", "*.json")],
        initialdir=BASE_DIR, title="Auswahl speichern")
    if not path:
        return
    selected = [entry_id for entry_id, var in VARS.items() if var.get()]
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"name": Path(path).stem, "selected": selected}, f, indent=2)


def load_selection():
    path = filedialog.askopenfilename(
        filetypes=[("JSON", "*.json")], initialdir=BASE_DIR, title="Auswahl laden")
    if path:
        load_preset(path)


def run_go():
    """Auswahl einsammeln und ans Backend übergeben."""
    picked = {"apps": [], "winsettings": [], "uninstalls": []}
    for entry_id, var in VARS.items():
        if var.get():
            kind, entry = ENTRIES[entry_id]
            picked[kind].append(entry)

    total = sum(len(v) for v in picked.values())
    if total == 0:
        messagebox.showinfo("Nichts ausgewählt", "Bitte erst etwas auswählen.")
        return

    summary = (f"{len(picked['apps'])} Apps installieren\n"
               f"{len(picked['winsettings'])} Einstellungen anwenden\n"
               f"{len(picked['uninstalls'])} Apps deinstallieren")
    if not messagebox.askokcancel("Los geht's?", summary):
        return

    if backend is None:
        messagebox.showinfo(
            "Backend fehlt noch",
            "backend.py wurde nicht gefunden — hier würde jetzt Folgendes passieren:\n\n" + summary)
        return

    backend.install_apps(picked["apps"])
    backend.apply_settings(picked["winsettings"])
    backend.uninstall_apps(picked["uninstalls"])


# -------------------------------------------------------------- Aufbau ----

def build_button(parent, text, command, primary=False):
    btn = tk.Button(parent, text=text, command=command, font=FONT,
                    bg=ACCENT if primary else BG_CARD,
                    fg="#101010" if primary else TEXT,
                    activebackground="#8adcff" if primary else BG_HOVER,
                    activeforeground="#101010" if primary else TEXT,
                    relief="flat", padx=18, pady=6, cursor="hand2", bd=0)
    return btn


def main():
    config = load_config()

    root = tk.Tk()
    root.title("Post Installer")
    root.geometry("900x640")
    root.minsize(720, 520)
    root.configure(bg=BG)
    root.attributes("-alpha", 0.97)  # leichte Transparenz
    enable_dark_titlebar(root)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", background=BG_CARD, foreground=TEXT_DIM,
                    font=FONT, padding=(14, 7), borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", BG_ACTIVE)],
              foreground=[("selected", TEXT)])
    style.configure("Vertical.TScrollbar", background=BG_CARD,
                    troughcolor=BG, borderwidth=0, arrowcolor=TEXT_DIM)

    # --- Kopfzeile: Titel + Preset-Buttons -------------------------------
    header = tk.Frame(root, bg=BG)
    header.pack(fill="x", padx=16, pady=(14, 8))
    tk.Label(header, text="Post Installer", bg=BG, fg=TEXT,
             font=FONT_TITLE).pack(side="left")

    presets = tk.Frame(header, bg=BG)
    presets.pack(side="right")
    tk.Label(presets, text="Presets:", bg=BG, fg=TEXT_DIM, font=FONT).pack(side="left", padx=(0, 8))
    for preset_file in sorted(PRESET_DIR.glob("*.json")):
        name = json.loads(preset_file.read_text(encoding="utf-8")).get("name", preset_file.stem)
        build_button(presets, name, lambda p=preset_file: load_preset(p)).pack(side="left", padx=4)

    # --- Tabs -------------------------------------------------------------
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=16, pady=4)
    build_split_tab(notebook, "App Settings", config["apps"], "apps")
    build_split_tab(notebook, "Reg/WinSettings", config["winsettings"], "winsettings", use_toggle=True)
    build_split_tab(notebook, "Uninstalls", config["uninstalls"], "uninstalls")

    # --- Fußzeile: Aktions-Buttons ----------------------------------------
    footer = tk.Frame(root, bg=BG)
    footer.pack(fill="x", padx=16, pady=(8, 14))
    build_button(footer, "Go!", run_go, primary=True).pack(side="right", padx=4)
    build_button(footer, "Speichern", save_selection).pack(side="right", padx=4)
    build_button(footer, "Laden", load_selection).pack(side="right", padx=4)

    root.mainloop()


if __name__ == "__main__":
    main()
