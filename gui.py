"""Frontend für den Post Installer.

Liest config.json (App-Katalog, Windows-Settings, Uninstalls, Icons) und
baut daraus die komplette Oberfläche — nichts ist hartkodiert. Neue Apps
oder Settings kommen also nur in die config.json, nicht hierher.

Das Aussehen der GUI (Theme, Akzentfarbe, Schrift, Transparenz, runde
Ecken, Symbole) wird im Tab "App Settings" eingestellt und in
gui_settings.json gespeichert.

Anbindung ans Backend (backend.py) über drei einfache Funktionen:

    backend.install_apps(entries)    # Liste von dicts aus config.json ("apps")
    backend.apply_settings(entries)  # dito ("winsettings")
    backend.uninstall_apps(entries)  # dito ("uninstalls")

Jeder Eintrag hat mindestens "id" und "name" — die technischen Felder
(winget/choco/commands/appx) stehen in der config.json.
"""

import ctypes
import json
import random
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

try:
    import backend
except ImportError:
    backend = None

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
PRESET_DIR = BASE_DIR / "presets"
SETTINGS_FILE = BASE_DIR / "gui_settings.json"

# ------------------------------------------------------- GUI-Einstellungen ----

DEFAULT_SETTINGS = {
    "theme": "dark",          # "dark" oder "light"
    "accent": "#60cdff",      # Akzentfarbe (Buttons, Schalter, aktive Tabs)
    "font_family": "Segoe UI",
    "font_size": 10,
    "alpha": 0.97,            # Fenster-Transparenz (1.0 = deckend)
    "rounded": True,          # runde Ecken für Buttons und Karten
    "icons": True,            # Emoji-Symbole in Tabs und Sidebar
}
SETTINGS = dict(DEFAULT_SETTINGS)

# Icons für die Tabs (Kategorie-Icons stehen in der config.json)
TAB_ICONS = {"Apps": "🖥️", "Reg/WinSettings": "⚙️", "Uninstalls": "🗑️", "App Settings": "🎨"}

# Bei jedem Start grüßt ein zufälliger Nerd-Witz aus der Fußzeile
NERD_JOKES = [
    "Es gibt 10 Arten von Menschen: die, die Binär verstehen, und die anderen.",
    "99 little bugs in the code… take one down, patch it around… 127 little bugs in the code.",
    "There's no place like 127.0.0.1",
    "Ein SQL-Query geht in eine Bar, sieht zwei Tische und fragt: „Darf ich joinen?“",
    "sudo make me a sandwich.",
    "Das ist kein Bug, das ist ein undokumentiertes Feature.",
    "Läuft bei mir. — jeder Entwickler, kurz vor dem Deployment",
    "Ich würde ja einen UDP-Witz erzählen, aber ich weiß nicht, ob er ankommt.",
    "Never trust an atom. They make up everything — genau wie Programmierer ihre Zeitschätzungen.",
    "Keyboard not found. Press F1 to continue.",
]

# Diese Globals bilden das aktive Theme ab; apply_palette() setzt sie
# passend zu SETTINGS. Widgets lesen sie beim (Neu-)Aufbau der GUI.
BG = BG_CARD = BG_SIDEBAR = BG_HOVER = BG_ACTIVE = ""
ACCENT = TEXT = TEXT_DIM = TOGGLE_OFF = ""
FONT = FONT_SMALL = FONT_TITLE = None


def apply_palette():
    """Setzt die Farb-/Font-Globals passend zu SETTINGS."""
    global BG, BG_CARD, BG_SIDEBAR, BG_HOVER, BG_ACTIVE
    global ACCENT, TEXT, TEXT_DIM, TOGGLE_OFF, FONT, FONT_SMALL, FONT_TITLE

    if SETTINGS["theme"] == "dark":
        BG, BG_CARD, BG_SIDEBAR = "#202020", "#2b2b2b", "#191919"
        BG_HOVER, BG_ACTIVE = "#303030", "#1f3a56"
        TEXT, TEXT_DIM, TOGGLE_OFF = "#f0f0f0", "#9d9d9d", "#4d4d4d"
    else:
        BG, BG_CARD, BG_SIDEBAR = "#f3f3f3", "#ffffff", "#e9e9e9"
        BG_HOVER, BG_ACTIVE = "#dedede", "#cce4f7"
        TEXT, TEXT_DIM, TOGGLE_OFF = "#1a1a1a", "#5f5f5f", "#b0b0b0"

    ACCENT = SETTINGS["accent"]
    family, size = SETTINGS["font_family"], int(SETTINGS["font_size"])
    FONT = (family, size)
    FONT_SMALL = (family, max(7, size - 2))
    FONT_TITLE = (family, size + 6, "bold")


def icon_text(icon, text):
    """Text optional mit Emoji-Symbol davor (je nach Einstellung)."""
    if SETTINGS["icons"] and icon:
        return f"{icon}  {text}"
    return text


def load_gui_settings():
    global SETTINGS
    SETTINGS = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            SETTINGS.update(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        pass  # dann eben Defaults
    apply_palette()


def save_gui_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(SETTINGS, f, indent=2)


def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def apply_window_style(root):
    """Transparenz + (auf Windows 11) Titelleisten-Farbe setzen."""
    root.configure(bg=BG)
    root.attributes("-alpha", float(SETTINGS["alpha"]))
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        value = ctypes.c_int(1 if SETTINGS["theme"] == "dark" else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), 4)
    except Exception:
        pass  # auf älteren Windows-Versionen einfach Standard lassen


# Auswahl-Zustand der gesamten GUI (überlebt einen Theme-Neuaufbau):
#   VARS[id]    -> tk.BooleanVar (Checkbox/Schalter an oder aus)
#   ENTRIES[id] -> ("apps"|"winsettings"|"uninstalls", eintrag-dict)
VARS = {}
ENTRIES = {}


# ------------------------------------------------------------- Widgets ----

def round_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    """Abgerundetes Rechteck als geglättetes Polygon zeichnen."""
    radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    points = [x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
              x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
              x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class Toggle(tk.Canvas):
    """Kleiner Ein/Aus-Schalter im Windows-11-Stil (Canvas-basiert)."""

    def __init__(self, parent, variable, bg=None):
        super().__init__(parent, width=44, height=22, bg=bg or BG_CARD,
                         highlightthickness=0, cursor="hand2")
        self.variable = variable
        self.bind("<Button-1>", lambda _e: self.variable.set(not self.variable.get()))
        self._trace = variable.trace_add("write", lambda *_: self._draw())
        self.bind("<Destroy>", lambda _e: self.variable.trace_remove("write", self._trace))
        self._draw()

    def _draw(self):
        self.delete("all")
        on = self.variable.get()
        track = ACCENT if on else TOGGLE_OFF
        # Track: zwei Kreise + Rechteck ergeben eine abgerundete Pille
        self.create_oval(1, 1, 21, 21, fill=track, outline=track)
        self.create_oval(23, 1, 43, 21, fill=track, outline=track)
        self.create_rectangle(11, 1, 33, 21, fill=track, outline=track)
        # Knopf
        x = 26 if on else 4
        knob = "#101010" if on else "#fafafa"
        self.create_oval(x, 4, x + 14, 18, fill=knob, outline="#808080")


class RoundedButton(tk.Canvas):
    """Button als abgerundete Pille (Tkinter kann das nicht nativ)."""

    def __init__(self, parent, text, command, primary=False, outer_bg=None):
        font = tkfont.Font(family=SETTINGS["font_family"], size=int(SETTINGS["font_size"]))
        self.w = font.measure(text) + 36
        self.h = 34
        super().__init__(parent, width=self.w, height=self.h, bg=outer_bg or BG,
                         highlightthickness=0, cursor="hand2", bd=0)
        self.text, self.font, self.command = text, font, command
        self.fill = ACCENT if primary else BG_CARD
        self.hover_fill = ACCENT if primary else BG_HOVER
        self.fg = "#101010" if primary else TEXT
        self.bind("<Button-1>", lambda _e: self.command())
        self.bind("<Enter>", lambda _e: self._draw(hover=True))
        self.bind("<Leave>", lambda _e: self._draw(hover=False))
        self._draw()

    def _draw(self, hover=False):
        self.delete("all")
        fill = self.hover_fill if hover else self.fill
        round_rect(self, 1, 1, self.w - 2, self.h - 2, 14, fill=fill, outline=fill)
        self.create_text(self.w // 2, self.h // 2, text=self.text, fill=self.fg, font=self.font)


class RoundedCard(tk.Canvas):
    """Karte mit runden Ecken; Inhalt kommt in .inner (ein normaler Frame).

    Der innere Frame ist seitlich um den Radius eingerückt, damit seine
    (eckigen) Ränder die gezeichneten Rundungen nicht überdecken.
    """

    def __init__(self, parent, fill=None, outer_bg=None, radius=12):
        super().__init__(parent, bg=outer_bg or BG, highlightthickness=0, bd=0)
        self.fill = fill or BG_CARD
        self.radius = radius
        self.inner = tk.Frame(self, bg=self.fill)
        self._win = self.create_window(radius, 2, window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",
                        lambda _e: self.configure(height=self.inner.winfo_reqheight() + 4))
        self.bind("<Configure>", self._redraw)

    def _redraw(self, _event=None):
        self.delete("bgrect")
        w, h = self.winfo_width(), self.winfo_height()
        shape = round_rect(self, 0, 0, w - 1, h - 1, self.radius,
                           fill=self.fill, outline=self.fill, tags="bgrect")
        self.tag_lower(shape)
        self.itemconfigure(self._win, width=max(w - 2 * self.radius, 10))


def build_button(parent, text, command, primary=False, outer_bg=None):
    """Button-Fabrik: rund oder klassisch flach, je nach Einstellung."""
    if SETTINGS["rounded"]:
        return RoundedButton(parent, text, command, primary=primary, outer_bg=outer_bg)
    return tk.Button(parent, text=text, command=command, font=FONT,
                     bg=ACCENT if primary else BG_CARD,
                     fg="#101010" if primary else TEXT,
                     activebackground=ACCENT if primary else BG_HOVER,
                     activeforeground="#101010" if primary else TEXT,
                     relief="flat", padx=18, pady=6, cursor="hand2", bd=0)


def make_card(parent, pady=3, padx=2):
    """Karten-Fabrik: gibt den Frame zurück, in den der Inhalt kommt."""
    if SETTINGS["rounded"]:
        card = RoundedCard(parent)
        card.pack(fill="x", pady=pady, padx=padx)
        return card.inner
    frame = tk.Frame(parent, bg=BG_CARD)
    frame.pack(fill="x", pady=pady, padx=padx)
    return frame


def scrollable_frame(parent, bg=None):
    """Vertikal scrollbarer Bereich; gibt den inneren Frame zurück."""
    bg = bg or BG
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
    row = make_card(parent)
    var = get_var(entry["id"], kind, entry)

    if use_toggle:
        tk.Label(row, text=entry["name"], bg=BG_CARD, fg=TEXT, font=FONT,
                 anchor="w").pack(side="left", fill="x", expand=True, padx=12, pady=9)
        Toggle(row, var).pack(side="right", padx=12, pady=6)
    else:
        check = tk.Checkbutton(row, text=entry["name"], variable=var,
                               bg=BG_CARD, fg=TEXT, font=FONT, anchor="w",
                               activebackground=BG_CARD, activeforeground=TEXT,
                               selectcolor=BG_SIDEBAR, highlightthickness=0, bd=0)
        check.pack(side="left", fill="x", expand=True, padx=8, pady=6)


def build_split_tab(notebook, title, sections, kind, icons, use_toggle=False):
    """Ein Tab mit Steam-artiger Sidebar links und Content rechts."""
    tab = tk.Frame(notebook, bg=BG)
    notebook.add(tab, text=f"  {icon_text(TAB_ICONS.get(title), title)}  ")

    sidebar = tk.Frame(tab, bg=BG_SIDEBAR, width=200)
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
        tk.Label(inner, text=icon_text(icons.get(category), category), bg=BG, fg=TEXT,
                 font=FONT_TITLE, anchor="w").pack(fill="x", pady=(0, 10))
        for entry in sections[category]:
            build_entry_row(inner, entry, kind, use_toggle)

    def make_label(category):
        lbl = tk.Label(sidebar, text=icon_text(icons.get(category), category),
                       bg=BG_SIDEBAR, fg=TEXT_DIM,
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


# ------------------------------------------- Tab: App Settings (Aussehen) ----

ACCENT_CHOICES = ["#60cdff", "#7a7fff", "#ff8c60", "#5fd68b", "#ff6fa5", "#e8c35a"]
PREFERRED_FONTS = ["Segoe UI", "Calibri", "Arial", "Verdana", "Consolas", "Georgia",
                   "JetBrainsMono NF", "JetBrainsMono Nerd Font", "JetBrains Mono"]


def available_fonts():
    """Nur Schriften anbieten, die auf diesem System wirklich installiert sind."""
    installed = set(tkfont.families())
    found = [f for f in PREFERRED_FONTS if f in installed]
    return found or ["Segoe UI"]


def build_appsettings_tab(notebook, root, config):
    """Tab, in dem man das Aussehen der GUI selbst einstellt."""
    tab = tk.Frame(notebook, bg=BG)
    notebook.add(tab, text=f"  {icon_text(TAB_ICONS.get('App Settings'), 'App Settings')}  ")
    inner = scrollable_frame(tab)

    tk.Label(inner, text="Aussehen", bg=BG, fg=TEXT, font=FONT_TITLE,
             anchor="w").pack(fill="x", padx=8, pady=(12, 10))

    theme_var = tk.StringVar(value=SETTINGS["theme"])
    accent_var = tk.StringVar(value=SETTINGS["accent"])
    family_var = tk.StringVar(value=SETTINGS["font_family"])
    size_var = tk.IntVar(value=int(SETTINGS["font_size"]))
    alpha_var = tk.DoubleVar(value=float(SETTINGS["alpha"]))
    rounded_var = tk.BooleanVar(value=bool(SETTINGS["rounded"]))
    icons_var = tk.BooleanVar(value=bool(SETTINGS["icons"]))

    def card(title):
        frame = make_card(inner, pady=4, padx=8)
        tk.Label(frame, text=title, bg=BG_CARD, fg=TEXT, font=FONT, width=16,
                 anchor="w").pack(side="left", padx=12, pady=10)
        return frame

    # --- Theme ---
    row = card("Theme")
    for label, value in (("Dark", "dark"), ("Light", "light")):
        tk.Radiobutton(row, text=label, value=value, variable=theme_var,
                       bg=BG_CARD, fg=TEXT, font=FONT, selectcolor=BG_SIDEBAR,
                       activebackground=BG_CARD, activeforeground=TEXT,
                       highlightthickness=0).pack(side="left", padx=6)

    # --- Akzentfarbe ---
    row = card("Akzentfarbe")
    preview = tk.Label(row, text="  aktuell  ", bg=accent_var.get(), fg="#101010", font=FONT_SMALL)
    preview.pack(side="right", padx=12)

    def set_accent(color):
        accent_var.set(color)
        preview.configure(bg=color)

    for color in ACCENT_CHOICES:
        tk.Button(row, width=2, bg=color, relief="flat", cursor="hand2", bd=0,
                  activebackground=color,
                  command=lambda c=color: set_accent(c)).pack(side="left", padx=3)
    tk.Button(row, text="Eigene…", bg=BG_HOVER, fg=TEXT, relief="flat", bd=0,
              font=FONT_SMALL, cursor="hand2", padx=8,
              command=lambda: (lambda c: c[1] and set_accent(c[1]))(
                  colorchooser.askcolor(accent_var.get(), title="Akzentfarbe"))
              ).pack(side="left", padx=8)

    # --- Schriftart / Größe ---
    row = card("Schriftart")
    combo = ttk.Combobox(row, textvariable=family_var, values=available_fonts(), width=18, font=FONT_SMALL)
    combo.pack(side="left", padx=6)
    tk.Label(row, text="Größe:", bg=BG_CARD, fg=TEXT_DIM, font=FONT).pack(side="left", padx=(16, 4))
    tk.Spinbox(row, from_=8, to=14, textvariable=size_var, width=4, font=FONT,
               bg=BG_HOVER, fg=TEXT, buttonbackground=BG_HOVER, relief="flat",
               insertbackground=TEXT).pack(side="left")

    # --- Transparenz ---
    row = card("Transparenz")
    tk.Scale(row, from_=0.85, to=1.0, resolution=0.01, orient="horizontal",
             variable=alpha_var, bg=BG_CARD, fg=TEXT, font=FONT_SMALL,
             troughcolor=BG_SIDEBAR, highlightthickness=0, length=220,
             activebackground=ACCENT).pack(side="left", padx=6, pady=4)

    # --- Runde Ecken / Symbole ---
    row = card("Runde Ecken")
    Toggle(row, rounded_var).pack(side="left", padx=6, pady=6)
    row = card("Symbole")
    Toggle(row, icons_var).pack(side="left", padx=6, pady=6)
    tk.Label(row, text="Emoji-Symbole in Tabs und Kategorien", bg=BG_CARD,
             fg=TEXT_DIM, font=FONT_SMALL).pack(side="left", padx=8)

    # --- Buttons ---
    actions = tk.Frame(inner, bg=BG)
    actions.pack(fill="x", padx=8, pady=12)

    def apply_and_save():
        SETTINGS.update(theme=theme_var.get(), accent=accent_var.get(),
                        font_family=family_var.get(), font_size=int(size_var.get()),
                        alpha=round(float(alpha_var.get()), 2),
                        rounded=rounded_var.get(), icons=icons_var.get())
        save_gui_settings()
        apply_palette()
        rebuild_ui(root, config, tab_index=notebook.index(tab))

    def reset():
        SETTINGS.update(DEFAULT_SETTINGS)
        save_gui_settings()
        apply_palette()
        rebuild_ui(root, config, tab_index=notebook.index(tab))

    build_button(actions, "Übernehmen & Speichern", apply_and_save, primary=True).pack(side="left")
    build_button(actions, "Zurücksetzen", reset).pack(side="left", padx=8)


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

def build_ui(root, config, tab_index=0):
    """Baut den kompletten Fensterinhalt auf (wird bei Theme-Wechsel erneut aufgerufen)."""
    apply_window_style(root)
    icons = config.get("icons", {})

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
    style.configure("TCombobox", fieldbackground=BG_HOVER, background=BG_HOVER,
                    foreground=TEXT, arrowcolor=TEXT)

    # --- Kopfzeile: Titel + Preset-Buttons -------------------------------
    header = tk.Frame(root, bg=BG)
    header.pack(fill="x", padx=16, pady=(14, 8))
    tk.Label(header, text=icon_text("🚀", "Post Installer"), bg=BG, fg=TEXT,
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
    build_split_tab(notebook, "Apps", config["apps"], "apps", icons)
    build_split_tab(notebook, "Reg/WinSettings", config["winsettings"], "winsettings",
                    icons, use_toggle=True)
    build_split_tab(notebook, "Uninstalls", config["uninstalls"], "uninstalls", icons)
    build_appsettings_tab(notebook, root, config)
    notebook.select(tab_index)

    # --- Fußzeile: Aktions-Buttons ----------------------------------------
    footer = tk.Frame(root, bg=BG)
    footer.pack(fill="x", padx=16, pady=(8, 14))
    build_button(footer, icon_text("▶", "Go!"), run_go, primary=True).pack(side="right", padx=4)
    build_button(footer, icon_text("💾", "Speichern"), save_selection).pack(side="right", padx=4)
    build_button(footer, icon_text("📂", "Laden"), load_selection).pack(side="right", padx=4)
    # Zuletzt gepackt, damit die Buttons ihren Platz sicher haben — der Witz
    # bekommt nur den Rest und wird notfalls abgeschnitten, nicht die Buttons.
    tk.Label(footer, text=icon_text("🤓", random.choice(NERD_JOKES)), bg=BG, fg=TEXT_DIM,
             font=FONT_SMALL, anchor="w").pack(side="left", fill="x", expand=True)


def rebuild_ui(root, config, tab_index=0):
    """Fensterinhalt verwerfen und mit dem aktuellen Theme neu aufbauen.

    Die Häkchen bleiben erhalten, weil die BooleanVars in VARS am
    Tk-Interpreter hängen, nicht an den zerstörten Widgets.
    """
    for child in root.winfo_children():
        child.destroy()
    build_ui(root, config, tab_index)


def main():
    load_gui_settings()
    config = load_config()

    root = tk.Tk()
    root.title("Post Installer")
    root.geometry("900x640")
    root.minsize(720, 520)
    build_ui(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
