"""About-Fenster im 80s-Demoscene-Stil. 🕹️

Eigenständiges Modul: die GUI braucht nur `about.show_about(parent)`
aufzurufen, alles andere (Fenster, Sternenfeld, Laufschrift, Musik)
passiert hier.

Musik: beim Öffnen wird ein zufälliges Tracker-Modul (XM/MOD/IT/S3M) aus
dem Archiv https://github.com/sxiii/keygen-music geladen, mit libxmplite
zu PCM gerendert und als WAV geloopt abgespielt. Geladene Module landen
im Ordner music_cache/ (gitignored), damit es auch offline funktioniert.

Fallback-Kette, damit das Fenster nie am Sound scheitert:
    1. frisches Zufallsmodul aus dem Netz
    2. zufälliges Modul aus dem lokalen Cache
    3. PC-Speaker-Arpeggio über winsound.Beep (wie 1989)
    4. Stille (Nicht-Windows)
"""

import base64
import io
import json
import math
import random
import threading
import time
import tkinter as tk
import urllib.request
import wave
from pathlib import Path

try:
    import winsound
except ImportError:  # pragma: no cover - winsound gibt es nur auf Windows
    winsound = None

try:
    import libxmplite
except ImportError:
    libxmplite = None

MUSIC_API = "https://api.github.com/repos/sxiii/keygen-music/contents/music"
MODULE_EXTS = (".xm", ".mod", ".it", ".s3m")
CACHE_DIR = Path(__file__).resolve().parent / "music_cache"
MAX_RENDER_SECONDS = 180  # laengere Module werden abgeschnitten und geloopt

# ------------------------------------------------- Fallback-Beep-Musik ----
# Arpeggio-Loop in a-Moll (Am - F - C - G), 16tel-Noten. 0 Hz = Pause.
_N = 90

MELODY = [
    (220, _N), (262, _N), (330, _N), (440, _N), (523, _N), (440, _N), (330, _N), (262, _N),
    (175, _N), (220, _N), (262, _N), (349, _N), (440, _N), (349, _N), (262, _N), (220, _N),
    (262, _N), (330, _N), (392, _N), (523, _N), (659, _N), (523, _N), (392, _N), (330, _N),
    (196, _N), (247, _N), (294, _N), (392, _N), (494, _N), (392, _N), (294, _N), (247, _N),
    (440, _N), (523, _N), (659, _N), (880, _N), (659, _N), (523, _N), (440, _N), (0, _N),
]

CREDITS = [
    ("POST INSTALLER", 18),
    ("", 10),
    ("~ CREDITS ~", 12),
    ("", 10),
    ("Code & Backend", 10),
    ("MAXI", 14),
    ("", 10),
    ("Frontend & Vibe Coding", 10),
    ("PATRICK + CLAUDE", 14),
    ("", 10),
    ("Music", 10),
    ("the keygen scene (via sxiii/keygen-music)", 11),
    ("", 10),
    ("Powered by", 10),
    ("Python + Tkinter + libxmplite", 12),
    ("", 10),
    ("~ GREETINGS FLY OUT TO ~", 12),
    ("", 10),
    ("alle Lehrer, die das hier benoten", 10),
    ("die Demoscene von 1985 bis heute", 10),
    ("alle, die bis hier gelesen haben", 10),
    ("", 10),
    ("NO WAREZ, NUR OPEN SOURCE", 12),
    ("", 10),
    ("...loop...", 8),
]

_open_window = None  # damit der Button das Fenster nicht doppelt öffnet


# --------------------------------------------------------------- Musik ----

def _gh_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "post-installer-about"})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def _download_random_module():
    """Zufälliges Tracker-Modul aus dem GitHub-Archiv holen und cachen."""
    group = random.choice([i for i in _gh_json(MUSIC_API) if i["type"] == "dir"])
    modules = [f for f in _gh_json(group["url"])
               if f["type"] == "file" and f["name"].lower().endswith(MODULE_EXTS)]
    chosen = random.choice(modules)
    # Download über die Contents-API (Base64) — die download_url stolpert
    # über Sonderzeichen in den Dateinamen (Leerzeichen, '#', '+', ...)
    data = base64.b64decode(_gh_json(chosen["url"])["content"])
    CACHE_DIR.mkdir(exist_ok=True)
    (CACHE_DIR / chosen["name"]).write_bytes(data)
    return chosen["name"], data


def _random_cached_module():
    """Offline-Variante: zufälliges bereits geladenes Modul aus dem Cache."""
    cached = [p for p in CACHE_DIR.iterdir()
              if p.suffix.lower() in MODULE_EXTS] if CACHE_DIR.exists() else []
    chosen = random.choice(cached)  # IndexError bei leerem Cache -> Fallback greift
    return chosen.name, chosen.read_bytes()


def _render_wav(module_data):
    """Tracker-Modul mit libxmplite zu einer WAV-Datei rendern."""
    xmp = libxmplite.Xmp()
    xmp.load_mem(module_data)
    xmp.start(44100)
    pcm = io.BytesIO()
    max_bytes = 44100 * 2 * 2 * MAX_RENDER_SECONDS  # stereo, 16 bit
    while pcm.tell() < max_bytes:
        buffer = xmp.play_buffer(16384)
        if xmp.frame_info().loop_count > 0:  # Modul einmal komplett durch
            break
        pcm.write(buffer)
    xmp.release()

    CACHE_DIR.mkdir(exist_ok=True)
    wav_path = CACHE_DIR / "_current.wav"
    with wave.open(str(wav_path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        wav.writeframes(pcm.getvalue())
    return str(wav_path)


def _music_worker(stop_event, now_playing):
    """Läuft im Thread: Tracker-Musik besorgen und abspielen, sonst Beeps."""
    if winsound is None:
        return

    if libxmplite is not None:
        for source in (_download_random_module, _random_cached_module):
            if stop_event.is_set():
                return
            try:
                name, data = source()
                wav_path = _render_wav(data)
                winsound.PlaySound(wav_path, winsound.SND_FILENAME
                                   | winsound.SND_ASYNC | winsound.SND_LOOP)
                now_playing["text"] = f"♫ {Path(name).stem}"
                stop_event.wait()  # spielt im Loop, bis das Fenster schließt
                winsound.PlaySound(None, winsound.SND_PURGE)
                return
            except Exception:
                continue  # naechste Quelle probieren

    # Fallback: PC-Speaker-Arpeggio (blockiert pro Note, deshalb eigener Thread)
    now_playing["text"] = "♫ PC-Speaker-Arpeggio (offline)"
    while not stop_event.is_set():
        for freq, dur in MELODY:
            if stop_event.is_set():
                return
            if freq:
                winsound.Beep(freq, dur)
            else:
                time.sleep(dur / 1000)


# ------------------------------------------------------------- Fenster ----

def show_about(parent):
    """Öffnet das About-Fenster (nur eines gleichzeitig)."""
    global _open_window
    if _open_window is not None and _open_window.winfo_exists():
        _open_window.lift()
        return

    win = tk.Toplevel(parent)
    _open_window = win
    win.title("About — Post Installer")
    win.geometry("540x440")
    win.resizable(False, False)
    win.configure(bg="black")

    canvas = tk.Canvas(win, width=540, height=440, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # --- Sternenfeld (drei Geschwindigkeiten = Parallax-Effekt) ---------
    stars = []
    for _ in range(70):
        depth = random.choice((1, 2, 3))
        star = canvas.create_oval(0, 0, depth, depth, fill="#c0c0ff", outline="")
        canvas.move(star, random.randint(0, 540), random.randint(0, 440))
        stars.append((star, depth))

    # --- Credits als eine Gruppe, die nach oben durchläuft --------------
    y = 460  # startet unterhalb des Fensters
    for text, size in CREDITS:
        canvas.create_text(270, y, text=text, fill="#00ff88", tags="credits",
                           font=("Consolas", size, "bold"), justify="center")
        y += max(size * 2, 20)
    span = y - 460 + 480  # Gesamthöhe der Laufschrift + Fensterhöhe

    # --- Titel mit Farbwechsel + Now-Playing-Zeile -----------------------
    title = canvas.create_text(270, 30, text="* 1 0 0 %  C R A C K E D  B Y  P R A K T I K U M *",
                               fill="#ff00ff", font=("Consolas", 11, "bold"))
    now_playing = {"text": "♫ suche Keygen-Musik…"}
    # schwarzer Balken, damit die Laufschrift nicht durch die Zeile scrollt
    canvas.create_rectangle(0, 410, 540, 440, fill="black", outline="black")
    track_label = canvas.create_text(270, 425, text=now_playing["text"],
                                     fill="#557799", font=("Consolas", 8))

    # --- Musik in eigenem Thread (Download/Rendern blockiert sonst) ------
    stop_event = threading.Event()
    threading.Thread(target=_music_worker, args=(stop_event, now_playing),
                     daemon=True).start()

    tick = [0]
    offset = [0.0]

    def animate():
        if not win.winfo_exists():
            return
        tick[0] += 1
        # Sterne fallen lassen — je "näher" (größer), desto schneller
        for star, depth in stars:
            canvas.move(star, 0, depth * 0.7)
            if canvas.coords(star)[1] > 440:
                canvas.move(star, random.randint(0, 540) - canvas.coords(star)[0], -444)
        # Credits hochschieben, nach einem vollen Durchlauf unten neu einreihen
        canvas.move("credits", 0, -1.2)
        offset[0] += 1.2
        if offset[0] >= span:
            canvas.move("credits", 0, span)
            offset[0] -= span
        # Titel-Farbe pulsieren lassen (Magenta <-> Cyan)
        pulse = max(0, min(255, int(127 + 128 * math.sin(tick[0] / 12))))
        canvas.itemconfigure(title, fill=f"#{pulse:02x}00{255 - pulse:02x}")
        # Now-Playing aktualisieren (der Musik-Thread schreibt den Namen rein)
        canvas.itemconfigure(track_label, text=now_playing["text"])
        win.after(33, animate)  # ~30 FPS

    def close(_event=None):
        global _open_window
        stop_event.set()
        if winsound:
            winsound.PlaySound(None, winsound.SND_PURGE)
        _open_window = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", close)
    win.bind("<Escape>", close)
    animate()
