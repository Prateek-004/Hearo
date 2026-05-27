#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  ██╗  ██╗███████╗ █████╗ ██████╗  ██████╗
  ██║  ██║██╔════╝██╔══██╗██╔══██╗██╔═══██╗
  ███████║█████╗  ███████║██████╔╝██║   ██║
  ██╔══██║██╔══╝  ██╔══██║██╔══██╗██║   ██║
  ██║  ██║███████╗██║  ██║██║  ██║╚██████╔╝
  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝
  Hearo v1.0 — Smart Offline Music Player
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pygame
import os, sys, json, random, threading, time, math, hashlib, colorsys
from pathlib import Path
from io import BytesIO
from typing import Optional, List, Dict

# ══════════════════════════════════════════════════════
#  Optional Libraries
# ══════════════════════════════════════════════════════
MUTAGEN_OK = PIL_OK = NUMPY_OK = False

try:
    from mutagen import File as MFile
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, APIC
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    MUTAGEN_OK = True
except ImportError:
    pass

try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_OK = True
except ImportError:
    pass

try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    pass

# ══════════════════════════════════════════════════════
#  Constants
# ══════════════════════════════════════════════════════
APP_NAME = "Hearo"
APP_VER  = "1.0.0"
EXTS     = {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".wma", ".aac"}

DATA_DIR = Path.home() / ".hearo"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LIB_F    = DATA_DIR / "library.json"
PLS_F    = DATA_DIR / "playlists.json"

# Colour palette
BG       = "#0B0B0B"
BG2      = "#111111"
SURF     = "#181818"
SURF2    = "#202020"
SURF3    = "#2A2A2A"
BORD     = "#383838"
HOV      = "#282828"
SEL      = "#1B3A28"
ACC      = "#1DB954"
ACC_H    = "#22D55E"
ACC_D    = "#166534"
TXP      = "#FFFFFF"
TXS      = "#AAAAAA"
TXT      = "#606060"
RED      = "#E91429"
PUR      = "#A855F7"
PUR_H    = "#C084FC"
PUR_BG   = "#180A2C"

FF = "Segoe UI"

def fnt(size: int, bold: bool = False) -> tuple:
    return (FF, size, "bold" if bold else "normal")

# ══════════════════════════════════════════════════════
#  Utilities
# ══════════════════════════════════════════════════════
def fmt_dur(sec) -> str:
    if not sec or sec < 0:
        return "0:00"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def trunc(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n-1] + "…"

def hash_color(s: str) -> str:
    h = int(hashlib.md5(s.encode()).hexdigest()[:8], 16)
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360.0, 0.55, 0.85)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

# ══════════════════════════════════════════════════════
#  SongMeta — holds all metadata for one track
# ══════════════════════════════════════════════════════
class SongMeta:
    def __init__(self, path: str, _skip: bool = False):
        self.path        = path
        p                = Path(path)
        self.filename    = p.stem
        self.ext         = p.suffix.lower()
        self.title       = self.filename
        self.artist      = "Unknown Artist"
        self.album       = "Unknown Album"
        self.genre       = ""
        self.year        = ""
        self.track       = 0
        self.duration    = 0.0
        self.bitrate     = 0
        self.art_data: Optional[bytes] = None
        self.liked       = False
        self.play_count  = 0
        self.last_played = 0.0
        self.added_time  = time.time()
        if not _skip and MUTAGEN_OK:
            self._extract()

    def _extract(self):
        try:
            audio = MFile(self.path, easy=True)
            if audio is None:
                return
            def g(k, d=""):
                v = audio.get(k)
                return str(v[0]) if v else d
            self.title  = g("title")  or self.filename
            self.artist = g("artist") or "Unknown Artist"
            self.album  = g("album")  or "Unknown Album"
            self.genre  = g("genre")  or ""
            self.year   = g("date")   or ""
            try:
                tn = g("tracknumber")
                self.track = int(tn.split("/")[0]) if tn else 0
            except:
                pass
            if hasattr(audio, "info"):
                self.duration = float(getattr(audio.info, "length", 0) or 0)
                self.bitrate  = int(getattr(audio.info, "bitrate", 0) or 0)
            self._art()
        except:
            pass

    def _art(self):
        try:
            if self.ext == ".mp3":
                t = ID3(self.path)
                for k in t:
                    if k.startswith("APIC"):
                        self.art_data = t[k].data
                        return
            elif self.ext == ".flac":
                f = FLAC(self.path)
                if f.pictures:
                    self.art_data = f.pictures[0].data
            elif self.ext in (".m4a", ".mp4", ".aac"):
                f = MP4(self.path)
                if "covr" in f:
                    self.art_data = bytes(f["covr"][0])
        except:
            pass

    def load_art(self):
        if self.art_data is None and MUTAGEN_OK:
            self._art()
        return self.art_data

    def to_dict(self) -> dict:
        return dict(path=self.path, title=self.title, artist=self.artist,
                    album=self.album, genre=self.genre, year=self.year,
                    track=self.track, duration=self.duration, bitrate=self.bitrate,
                    liked=self.liked, play_count=self.play_count,
                    last_played=self.last_played, added_time=self.added_time)

    @classmethod
    def from_dict(cls, d: dict):
        o = cls(d.get("path", ""), _skip=True)
        for k in ("title","artist","album","genre","year","track","duration",
                  "bitrate","liked","play_count","last_played","added_time"):
            if k in d:
                setattr(o, k, d[k])
        return o

# ══════════════════════════════════════════════════════
#  Library — persists & manages all songs + playlists
# ══════════════════════════════════════════════════════
class Library:
    def __init__(self):
        self.songs:     List[SongMeta]           = []
        self.playlists: Dict[str, List[str]]     = {}
        self._load()

    def _load(self):
        if LIB_F.exists():
            try:
                seen = set()
                for d in json.loads(LIB_F.read_text(encoding="utf-8")):
                    p = d.get("path", "")
                    if p and p not in seen and Path(p).exists():
                        self.songs.append(SongMeta.from_dict(d))
                        seen.add(p)
            except:
                pass
        if PLS_F.exists():
            try:
                self.playlists = json.loads(PLS_F.read_text(encoding="utf-8"))
            except:
                pass

    def save(self):
        try:
            LIB_F.write_text(
                json.dumps([s.to_dict() for s in self.songs], indent=2, ensure_ascii=False),
                encoding="utf-8")
        except:
            pass
        try:
            PLS_F.write_text(
                json.dumps(self.playlists, indent=2, ensure_ascii=False),
                encoding="utf-8")
        except:
            pass

    def add_files(self, paths) -> int:
        ex = {s.path for s in self.songs}
        n  = 0
        for p in paths:
            if p not in ex and Path(p).suffix.lower() in EXTS:
                self.songs.append(SongMeta(p))
                ex.add(p)
                n += 1
        if n:
            self.save()
        return n

    def add_folder(self, folder: str) -> int:
        files = []
        for root, _, fnames in os.walk(folder):
            for fn in fnames:
                if Path(fn).suffix.lower() in EXTS:
                    files.append(os.path.join(root, fn))
        return self.add_files(files)

    def remove(self, path: str):
        self.songs = [s for s in self.songs if s.path != path]
        for pl in self.playlists.values():
            while path in pl:
                pl.remove(path)
        self.save()

    def get(self, path: str) -> Optional[SongMeta]:
        for s in self.songs:
            if s.path == path:
                return s
        return None

    def liked(self) -> List[SongMeta]:
        return [s for s in self.songs if s.liked]

    def pl_songs(self, name: str) -> List[SongMeta]:
        bp = {s.path: s for s in self.songs}
        return [bp[p] for p in self.playlists.get(name, []) if p in bp]

    def search(self, q: str) -> List[SongMeta]:
        q = q.lower()
        return [s for s in self.songs
                if q in s.title.lower() or q in s.artist.lower()
                or q in s.album.lower()]

# ══════════════════════════════════════════════════════
#  AI Recommender — cosine-similarity on audio features
# ══════════════════════════════════════════════════════
_GENRES = ["pop","rock","hip hop","rap","r&b","soul","jazz","classical",
           "electronic","dance","country","folk","metal","punk","blues",
           "reggae","latin","indie","alternative","ambient","trap","lofi"]

def _genre_id(genre: str) -> int:
    g = genre.lower()
    for i, name in enumerate(_GENRES):
        if name in g:
            return i
    return int(hashlib.md5(g.encode()).hexdigest()[:2], 16) % 10 + 12

def _artist_fp(artist: str) -> list:
    h = hashlib.md5(artist.lower().encode()).hexdigest()
    return [int(h[i*2:(i+1)*2], 16) / 255.0 for i in range(5)]

def _song_vec(s: SongMeta) -> list:
    gi  = _genre_id(s.genre) / 22.0
    afp = _artist_fp(s.artist)
    alb = int(hashlib.md5(s.album.lower().encode()).hexdigest()[:4], 16) / 65535.0
    dur = min(6, int(s.duration / 60)) / 6.0
    bit = min(7, int(s.bitrate / 48000)) / 7.0
    try:
        yr  = int(str(s.year)[:4])
        dec = max(0.0, min(1.0, (yr - 1950) / 80.0))
    except:
        dec = 0.5
    return ([gi * 2.0] + [a * 4.0 for a in afp] + [alb, dur, bit * 0.5, dec * 1.5])

def _cosine(a: list, b: list) -> float:
    if NUMPY_OK:
        av, bv = np.array(a, float), np.array(b, float)
        d = np.linalg.norm(av) * np.linalg.norm(bv)
        return float(np.dot(av, bv) / d) if d else 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x*x for x in a))
    nb  = math.sqrt(sum(x*x for x in b))
    return dot / (na * nb) if na * nb else 0.0

class Recommender:
    def __init__(self, lib: Library):
        self.lib = lib
        self._vc: Dict[str, list] = {}

    def _v(self, s: SongMeta) -> list:
        if s.path not in self._vc:
            self._vc[s.path] = _song_vec(s)
        return self._vc[s.path]

    def similar(self, song: SongMeta, n: int = 25, excl=None) -> List[SongMeta]:
        ex  = set(excl or [])
        ex.add(song.path)
        ref = self._v(song)
        ranked = sorted(
            [(s, _cosine(ref, self._v(s)))
             for s in self.lib.songs
             if s.path not in ex and Path(s.path).exists()],
            key=lambda x: -x[1])
        return [s for s, _ in ranked[:n]]

    def ai_queue(self, current: SongMeta, size: int = 40) -> List[SongMeta]:
        pool = self.similar(current, n=min(60, max(0, len(self.lib.songs)-1)))
        if not pool:
            return list(self.lib.songs)
        cut  = max(3, len(pool) // 3)
        top  = pool[:cut]
        rest = pool[cut:]
        random.shuffle(rest)
        return ([current] + top + rest)[:size]

    def top_picks(self, n: int = 8) -> List[SongMeta]:
        avail  = [s for s in self.lib.songs if Path(s.path).exists()]
        played = [s for s in avail if s.play_count > 0]
        if not avail:
            return []
        if not played:
            return random.sample(avail, min(n, len(avail)))
        seeds = sorted(played, key=lambda s: s.play_count, reverse=True)[:2]
        seen  = {s.path for s in seeds}
        recs: List[SongMeta] = []
        for seed in seeds:
            for s in self.similar(seed, n=6, excl=list(seen)):
                seen.add(s.path)
                recs.append(s)
        if len(recs) < n:
            extra = [s for s in avail if s.path not in seen]
            random.shuffle(extra)
            recs.extend(extra[:n - len(recs)])
        random.shuffle(recs)
        return recs[:n]

# ══════════════════════════════════════════════════════
#  Player — pygame mixer wrapper with position tracking
# ══════════════════════════════════════════════════════
class Player:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 4096)
        pygame.mixer.init()
        self.current: Optional[SongMeta] = None
        self._vol    = 0.7
        self._paused = False
        self._loaded = False
        self._pos    = 0.0
        self._t0     = 0.0
        pygame.mixer.music.set_volume(self._vol)

    @property
    def volume(self) -> float:
        return self._vol

    @volume.setter
    def volume(self, v: float):
        self._vol = max(0.0, min(1.0, v))
        pygame.mixer.music.set_volume(self._vol)

    def load(self, song: SongMeta) -> bool:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(song.path)
            self.current = song
            self._paused = False
            self._loaded = True
            self._pos    = 0.0
            self._t0     = 0.0
            return True
        except Exception as e:
            messagebox.showerror("Playback Error",
                f"Cannot play:\n{Path(song.path).name}\n\n{e}")
            self._loaded = False
            return False

    def play(self):
        if not self._loaded:
            return
        try:
            if self._pos > 0:
                pygame.mixer.music.play(start=self._pos)
            else:
                pygame.mixer.music.play()
        except Exception:
            try:
                pygame.mixer.music.play()
            except:
                pass
        self._t0     = time.time() - self._pos
        self._paused = False

    def pause(self):
        if self.playing:
            self._pos = self.pos
            pygame.mixer.music.pause()
            self._paused = True

    def resume(self):
        if self._paused and self._loaded:
            self._t0 = time.time() - self._pos
            pygame.mixer.music.unpause()
            self._paused = False

    def stop(self):
        pygame.mixer.music.stop()
        self._paused = False
        self._loaded = False
        self._pos    = 0.0
        self.current = None

    def seek(self, sec: float):
        self._pos = max(0.0, sec)
        if not self._loaded:
            return
        try:
            pygame.mixer.music.play(start=self._pos)
            self._t0 = time.time() - self._pos
            if self._paused:
                pygame.mixer.music.pause()
        except:
            pass

    @property
    def playing(self) -> bool:
        return pygame.mixer.music.get_busy() and not self._paused

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def pos(self) -> float:
        if not self._loaded:
            return 0.0
        if self._paused:
            return self._pos
        if self._t0 == 0.0:
            return 0.0
        return time.time() - self._t0

    @property
    def ended(self) -> bool:
        return (self._loaded and not self._paused
                and not pygame.mixer.music.get_busy())

# ══════════════════════════════════════════════════════
#  Tooltip
# ══════════════════════════════════════════════════════
class Tooltip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text   = text
        self._tip   = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event):
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self._tip, text=self.text,
                 bg=SURF3, fg=TXP, font=fnt(9),
                 padx=8, pady=4, relief="flat").pack()

    def _hide(self, _event):
        if self._tip:
            self._tip.destroy()
            self._tip = None

# ══════════════════════════════════════════════════════
#  HearoApp — main UI + controller
# ══════════════════════════════════════════════════════
class HearoApp:
    def __init__(self):
        self.lib    = Library()
        self.player = Player()
        self.rec    = Recommender(self.lib)

        # Playback state
        self.queue: List[SongMeta] = []
        self.qi         = -1
        self.shuffle    = False
        self.ai_shuffle = False
        self.repeat     = 0       # 0=off  1=all  2=one

        # UI state
        self._view        = "library"
        self._sort_rev    = False
        self._seek_active = False
        self._muted       = False
        self._prev_vol    = 0.7
        self._prog_pct    = 0.0
        self._hover_prog  = False
        self._displayed:  List[SongMeta] = []
        self._art_cache:  Dict[str, object] = {}

        # Build window
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("1280x800")
        self.root.minsize(960, 650)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        try:
            self.root.iconbitmap("")
        except:
            pass

        self._apply_styles()
        self._build_ui()
        self._refresh_list()
        self._update_np()
        self._bind_keys()
        self._tick()
        self.root.mainloop()

    # ── Styles ─────────────────────────────────────────────────────────────
    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Hearo.Treeview",
            background=SURF, foreground=TXS,
            fieldbackground=SURF, borderwidth=0,
            rowheight=44, font=fnt(10))
        s.configure("Hearo.Treeview.Heading",
            background=SURF2, foreground=TXT,
            borderwidth=0, font=fnt(9, True), padding=(8, 6))
        s.map("Hearo.Treeview",
            background=[("selected", SEL)],
            foreground=[("selected", TXP)])
        s.configure("Hearo.Vertical.TScrollbar",
            background=SURF3, troughcolor=SURF,
            arrowcolor=TXT, borderwidth=0, width=7)
        s.map("Hearo.Vertical.TScrollbar",
            background=[("active", BORD)])

    # ── UI build ────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_topbar()
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)
        self._build_sidebar(body)
        self._build_main(body)
        self._build_player()

    # ── Top bar ─────────────────────────────────────────────────────────────
    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=BG2, height=66)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # Logo
        tk.Label(bar, text="♪ HEARO", bg=BG2, fg=ACC,
                 font=(FF, 22, "bold"), padx=22).pack(side="left", fill="y")

        # Buttons right
        btn_area = tk.Frame(bar, bg=BG2)
        btn_area.pack(side="right", padx=16, fill="y")
        self._mkbtn(btn_area, "+ Add Folder", self.add_folder, SURF3, TXS
                    ).pack(side="right", padx=4, pady=16)
        self._mkbtn(btn_area, "+ Add Songs", self.add_songs, ACC, "#000", bold=True
                    ).pack(side="right", padx=4, pady=16)

        # Search box (centered)
        sf = tk.Frame(bar, bg=SURF2)
        sf.place(relx=0.42, rely=0.5, anchor="center", width=390, height=38)
        tk.Label(sf, text="⌕", bg=SURF2, fg=TXT, font=fnt(15)).pack(side="left", padx=10)
        self._search_sv = tk.StringVar()
        self._search_ent = tk.Entry(
            sf, textvariable=self._search_sv,
            bg=SURF2, fg=TXP, insertbackground=TXP,
            font=fnt(10), bd=0, highlightthickness=0, relief="flat")
        self._search_ent.pack(side="left", fill="both", expand=True, padx=4, pady=7)
        self._ph = "Search songs, artists, albums…"
        self._search_ent.insert(0, self._ph)
        self._search_ent.configure(fg=TXT)
        self._search_sv.trace_add("write", lambda *_: self._on_search())
        self._search_ent.bind("<FocusIn>",  self._search_in)
        self._search_ent.bind("<FocusOut>", self._search_out)
        self._search_ent.bind("<Escape>",
            lambda e: (self._search_sv.set(""),
                       self._search_ent.event_generate("<FocusOut>")))

    def _mkbtn(self, parent, text, cmd, bg, fg, bold=False):
        hbg = ACC_H if bg == ACC else HOV
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=fg, font=fnt(9, bold),
                      bd=0, padx=12, pady=6, cursor="hand2",
                      activebackground=hbg, activeforeground=fg, relief="flat")
        b.bind("<Enter>", lambda e, b=b: b.configure(bg=hbg))
        b.bind("<Leave>", lambda e, b=b: b.configure(bg=bg))
        return b

    # ── Sidebar ─────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=BG2, width=234)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        tk.Frame(sb, bg=BORD, height=1).pack(fill="x")

        self._nav_btns: Dict[str, tk.Button] = {}
        for label, view in [("🎵  Your Library", "library"),
                              ("❤  Liked Songs",  "liked")]:
            b = tk.Button(sb, text=label, anchor="w",
                          bg=BG2, fg=TXS, font=fnt(11),
                          bd=0, padx=20, pady=12, cursor="hand2",
                          activebackground=HOV, activeforeground=TXP, relief="flat")
            b.configure(command=lambda v=view: self._set_view(v))
            b.bind("<Enter>", lambda e, b=b, v=view:
                   b.configure(bg=HOV, fg=TXP) if self._view != v else None)
            b.bind("<Leave>", lambda e, b=b, v=view:
                   b.configure(bg=SEL if self._view == v else BG2,
                               fg=TXP if self._view == v else TXS))
            b.pack(fill="x")
            self._nav_btns[view] = b
        self._nav_btns["library"].configure(bg=SEL, fg=TXP)

        tk.Frame(sb, bg=BORD, height=1).pack(fill="x", pady=8)

        # Playlists header
        ph = tk.Frame(sb, bg=BG2)
        ph.pack(fill="x", padx=16, pady=(0, 4))
        tk.Label(ph, text="PLAYLISTS", bg=BG2, fg=TXT, font=fnt(9, True)).pack(side="left")
        self._mkbtn(ph, "+", lambda: self.new_playlist(), SURF3, TXS
                    ).pack(side="right")

        self._pl_frame = tk.Frame(sb, bg=BG2)
        self._pl_frame.pack(fill="both", expand=True)
        self._refresh_playlists()

    # ── Main content ────────────────────────────────────────────────────────
    def _build_main(self, parent):
        mf = tk.Frame(parent, bg=BG)
        mf.pack(side="left", fill="both", expand=True)

        # Header row
        header = tk.Frame(mf, bg=BG, padx=24, pady=14)
        header.pack(fill="x")
        self._view_title = tk.Label(header, text="Your Library",
                                     bg=BG, fg=TXP, font=fnt(21, True))
        self._view_title.pack(side="left")

        # Sort controls
        sf2 = tk.Frame(header, bg=BG)
        sf2.pack(side="right")
        tk.Label(sf2, text="Sort:", bg=BG, fg=TXT, font=fnt(9)).pack(side="left")
        self._sort_sv = tk.StringVar(value="title")
        for lbl, key in [("Title","title"),("Artist","artist"),
                          ("Album","album"),("Duration","duration"),
                          ("Added","added_time")]:
            tk.Radiobutton(sf2, text=lbl, variable=self._sort_sv, value=key,
                           command=self._on_sort,
                           bg=BG, fg=TXS, selectcolor=BG,
                           activebackground=BG, activeforeground=ACC,
                           font=fnt(9), cursor="hand2", bd=0
                           ).pack(side="left", padx=2)
        tk.Button(sf2, text="⇅", command=self._toggle_rev,
                  bg=SURF2, fg=TXS, font=fnt(11), bd=0,
                  padx=6, pady=1, cursor="hand2", relief="flat",
                  activebackground=SURF3, activeforeground=TXP
                  ).pack(side="left", padx=4)

        # Song list
        tree_f = tk.Frame(mf, bg=SURF)
        tree_f.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        vsb = ttk.Scrollbar(tree_f, orient="vertical",
                             style="Hearo.Vertical.TScrollbar")
        self.tree = ttk.Treeview(
            tree_f, style="Hearo.Treeview",
            columns=("n","title","artist","album","dur","liked"),
            show="headings", selectmode="browse",
            yscrollcommand=vsb.set)

        self.tree.heading("n",      text="#",       anchor="center")
        self.tree.heading("title",  text="Title",   anchor="w")
        self.tree.heading("artist", text="Artist",  anchor="w")
        self.tree.heading("album",  text="Album",   anchor="w")
        self.tree.heading("dur",    text="Time",    anchor="center")
        self.tree.heading("liked",  text="♥",       anchor="center")

        self.tree.column("n",      width=42,  minwidth=42,  anchor="center")
        self.tree.column("title",  width=290, minwidth=130, anchor="w")
        self.tree.column("artist", width=195, minwidth=100, anchor="w")
        self.tree.column("album",  width=195, minwidth=100, anchor="w")
        self.tree.column("dur",    width=58,  minwidth=50,  anchor="center")
        self.tree.column("liked",  width=42,  minwidth=42,  anchor="center")

        self.tree.tag_configure("even", background=SURF)
        self.tree.tag_configure("odd",  background="#1c1c1c")
        self.tree.tag_configure("play", background=SEL, foreground=ACC_H)

        vsb.configure(command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Double-1>",        self._dbl_click)
        self.tree.bind("<Return>",          self._dbl_click)
        self.tree.bind("<ButtonRelease-1>", self._single_click)
        self.tree.bind("<Button-3>",        self._right_click)
        self.root.bind("<Delete>",          lambda e: self._del_sel())

        # AI Recommendations
        self._build_rec_panel(mf)

    def _build_rec_panel(self, parent):
        self._rec_outer = tk.Frame(parent, bg=PUR_BG, pady=8)
        self._rec_outer.pack(fill="x", padx=12, pady=(0, 12))

        rh = tk.Frame(self._rec_outer, bg=PUR_BG, padx=14)
        rh.pack(fill="x")
        tk.Label(rh, text="✦  AI Picks For You",
                 bg=PUR_BG, fg=PUR_H, font=fnt(11, True)).pack(side="left")
        tk.Label(rh, text="  —  based on your listening history",
                 bg=PUR_BG, fg=TXT, font=fnt(9)).pack(side="left")
        self._mkbtn(rh, "↺ Refresh", self._load_recs, PUR_BG, PUR
                    ).pack(side="right")

        self._rec_cards = tk.Frame(self._rec_outer, bg=PUR_BG)
        self._rec_cards.pack(fill="x", padx=14, pady=(8, 2))
        self._load_recs()

    # ── Player bar ──────────────────────────────────────────────────────────
    def _build_player(self):
        bar = tk.Frame(self.root, bg=SURF2, height=94)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Frame(bar, bg=BORD, height=1).pack(fill="x", side="top")

        inner = tk.Frame(bar, bg=SURF2)
        inner.pack(fill="both", expand=True, padx=18, pady=6)

        # ── Now Playing ────────────────────────────────────────────────
        npl = tk.Frame(inner, bg=SURF2, width=290)
        npl.pack(side="left", fill="y")
        npl.pack_propagate(False)

        self._art_lbl = tk.Label(npl, bg=SURF3, width=60, height=60,
                                  text="♪", fg=TXT, font=fnt(20))
        self._art_lbl.pack(side="left", padx=(0, 12), pady=2)

        npi = tk.Frame(npl, bg=SURF2)
        npi.pack(side="left", fill="y", pady=8)
        self._np_title  = tk.Label(npi, text="No song playing",
                                    bg=SURF2, fg=TXP, font=fnt(11, True), anchor="w")
        self._np_title.pack(anchor="w")
        self._np_artist = tk.Label(npi, text="", bg=SURF2, fg=TXS,
                                    font=fnt(9), anchor="w")
        self._np_artist.pack(anchor="w", pady=(1, 0))
        self._np_like = tk.Button(npi, text="♡",
                                   command=self._toggle_like_cur,
                                   bg=SURF2, fg=TXT, font=fnt(12),
                                   bd=0, cursor="hand2", relief="flat",
                                   activebackground=SURF2, activeforeground=RED)
        self._np_like.pack(anchor="w", pady=(2, 0))

        # ── Transport controls ─────────────────────────────────────────
        ctrl = tk.Frame(inner, bg=SURF2)
        ctrl.pack(side="left", fill="both", expand=True, padx=10)

        brow = tk.Frame(ctrl, bg=SURF2)
        brow.pack(pady=(6, 2))

        def cbtn(par, ch, cmd, color=TXS, size=16, tip=""):
            b = tk.Button(par, text=ch, command=cmd,
                          bg=SURF2, fg=color, font=fnt(size),
                          bd=0, cursor="hand2", relief="flat",
                          activebackground=SURF2, activeforeground=TXP,
                          padx=7, pady=0)
            b.bind("<Enter>", lambda e, b=b: b.configure(fg=TXP))
            b.bind("<Leave>", lambda e, b=b, c=color: b.configure(fg=c))
            if tip:
                Tooltip(b, tip)
            return b

        self._btn_prev = cbtn(brow, "⏮", self.prev_song,  tip="Previous  (←)")
        self._btn_prev.pack(side="left", padx=4)

        self._btn_play = cbtn(brow, "▶", self.toggle_play, TXP, 20, "Play / Pause  (Space)")
        self._btn_play.pack(side="left", padx=4)

        self._btn_next = cbtn(brow, "⏭", self.next_song,  tip="Next  (→)")
        self._btn_next.pack(side="left", padx=4)

        tk.Frame(brow, bg=BORD, width=1, height=22).pack(side="left", padx=12)

        self._btn_shuf = cbtn(brow, "⇌",  self.toggle_shuffle,   tip="Shuffle  (S)")
        self._btn_shuf.pack(side="left", padx=3)

        # AI Shuffle button — accent purple
        self._btn_ai = tk.Button(
            brow, text="AI ⇌",
            command=self.toggle_ai_shuffle,
            bg=PUR_BG, fg=PUR, font=fnt(9, True),
            bd=0, cursor="hand2", relief="flat",
            padx=10, pady=4,
            activebackground=PUR_BG, activeforeground=PUR_H)
        self._btn_ai.pack(side="left", padx=4)
        Tooltip(self._btn_ai, "AI Shuffle — queue similar songs automatically")

        self._btn_rep = cbtn(brow, "↺", self.toggle_repeat, tip="Repeat  (R)")
        self._btn_rep.pack(side="left", padx=3)

        # Progress row
        prow = tk.Frame(ctrl, bg=SURF2)
        prow.pack(fill="x", padx=8, pady=(0, 4))

        self._pos_lbl = tk.Label(prow, text="0:00", bg=SURF2, fg=TXT,
                                  font=fnt(9), width=5)
        self._pos_lbl.pack(side="left")

        self._prog_cv = tk.Canvas(prow, bg=SURF3, height=4,
                                   cursor="hand2", highlightthickness=0)
        self._prog_cv.pack(side="left", fill="x", expand=True, padx=8)
        self._draw_prog()

        self._dur_lbl = tk.Label(prow, text="0:00", bg=SURF2, fg=TXT,
                                  font=fnt(9), width=5)
        self._dur_lbl.pack(side="left")

        self._prog_cv.bind("<ButtonPress-1>",   self._seek_press)
        self._prog_cv.bind("<B1-Motion>",       self._seek_move)
        self._prog_cv.bind("<ButtonRelease-1>", self._seek_release)
        self._prog_cv.bind("<Enter>", lambda e: self._prog_hover(True))
        self._prog_cv.bind("<Leave>", lambda e: self._prog_hover(False))

        # ── Volume ─────────────────────────────────────────────────────
        vf = tk.Frame(inner, bg=SURF2, width=210)
        vf.pack(side="right", fill="y")
        vf.pack_propagate(False)

        vrow = tk.Frame(vf, bg=SURF2)
        vrow.pack(expand=True)

        self._btn_mute = tk.Button(vrow, text="🔊", command=self.toggle_mute,
                                    bg=SURF2, fg=TXS, font=fnt(11),
                                    bd=0, cursor="hand2", relief="flat",
                                    activebackground=SURF2, activeforeground=TXP)
        self._btn_mute.pack(side="left", padx=(0, 8))
        Tooltip(self._btn_mute, "Mute  (M)")

        self._vol_cv = tk.Canvas(vrow, bg=SURF3, width=90, height=4,
                                  cursor="hand2", highlightthickness=0)
        self._vol_cv.pack(side="left")
        self._draw_vol()
        self._vol_cv.bind("<ButtonPress-1>",   self._vol_set)
        self._vol_cv.bind("<B1-Motion>",       self._vol_set)

        self._vol_lbl = tk.Label(vrow, text=f"{int(self.player.volume*100)}%",
                                  bg=SURF2, fg=TXT, font=fnt(9), width=4)
        self._vol_lbl.pack(side="left", padx=(8, 0))

    # ══════════════════════════════════════════════════
    #  Playback
    # ══════════════════════════════════════════════════
    def _build_queue(self, start: Optional[SongMeta] = None):
        songs = list(self._songs_for_view())
        if not songs:
            return
        if self.ai_shuffle and start:
            self.queue = self.rec.ai_queue(start)
            try:
                self.qi = next(i for i, s in enumerate(self.queue)
                               if s.path == start.path)
            except StopIteration:
                self.qi = 0
        elif self.shuffle:
            self.queue = list(songs)
            if start and start in self.queue:
                self.queue.remove(start)
            random.shuffle(self.queue)
            if start:
                self.queue.insert(0, start)
            self.qi = 0
        else:
            self.queue = list(songs)
            if start:
                try:
                    self.qi = next(i for i, s in enumerate(self.queue)
                                   if s.path == start.path)
                except StopIteration:
                    self.qi = 0
            else:
                self.qi = 0

    def play_song(self, song: SongMeta, rebuild: bool = True):
        if rebuild:
            self._build_queue(song)
        if not self.player.load(song):
            return
        self.player.play()
        song.play_count += 1
        song.last_played = time.time()
        self.lib.save()
        self._update_np()
        self._refresh_list()
        self._scroll_to_current()

    def toggle_play(self):
        if self.player.playing:
            self.player.pause()
            self._btn_play.configure(text="▶")
        elif self.player.paused:
            self.player.resume()
            self._btn_play.configure(text="⏸")
        elif self.queue and 0 <= self.qi < len(self.queue):
            s = self.queue[self.qi]
            if not self.player.loaded:
                self.player.load(s)
            self.player.play()
            self._btn_play.configure(text="⏸")
        elif self.lib.songs:
            self.play_song(self.lib.songs[0])

    def next_song(self):
        if not self.queue:
            return
        if self.repeat == 2:
            self.play_song(self.queue[self.qi], rebuild=False)
            return
        self.qi += 1
        if self.qi >= len(self.queue):
            if self.repeat == 1:
                self.qi = 0
            else:
                self.qi = len(self.queue) - 1
                self.player.stop()
                self._update_np()
                return
        self.play_song(self.queue[self.qi], rebuild=False)

    def prev_song(self):
        if not self.queue:
            return
        if self.player.pos > 3.0:
            self.player.seek(0)
            return
        self.qi = max(0, self.qi - 1)
        self.play_song(self.queue[self.qi], rebuild=False)

    def toggle_shuffle(self):
        if self.ai_shuffle:
            self.ai_shuffle = False
            self._btn_ai.configure(bg=PUR_BG, fg=PUR)
        self.shuffle = not self.shuffle
        self._btn_shuf.configure(fg=ACC if self.shuffle else TXS)
        if self.shuffle and self.player.current:
            self._build_queue(self.player.current)

    def toggle_ai_shuffle(self):
        if self.shuffle:
            self.shuffle = False
            self._btn_shuf.configure(fg=TXS)
        self.ai_shuffle = not self.ai_shuffle
        if self.ai_shuffle:
            self._btn_ai.configure(bg=PUR, fg="#000")
            if self.player.current:
                self._build_queue(self.player.current)
            messagebox.showinfo(
                "AI Shuffle Activated",
                "🤖  AI Shuffle is now ON!\n\n"
                "Hearo analyses the current track and queues up\n"
                "similar songs based on genre, artist style, tempo\n"
                "and audio features — all offline, no internet needed.",
                parent=self.root)
        else:
            self._btn_ai.configure(bg=PUR_BG, fg=PUR)

    def toggle_repeat(self):
        self.repeat = (self.repeat + 1) % 3
        self._btn_rep.configure(
            text=["↺", "🔁", "🔂"][self.repeat],
            fg=[TXS, ACC, ACC][self.repeat])
        tips = ["Repeat: Off", "Repeat: All", "Repeat: One"]
        Tooltip(self._btn_rep, tips[self.repeat])

    def toggle_mute(self):
        if self._muted:
            self.player.volume = self._prev_vol
            self._muted = False
        else:
            self._prev_vol = self.player.volume
            self.player.volume = 0.0
            self._muted = True
        v = self.player.volume
        self._btn_mute.configure(
            text="🔇" if v == 0 else ("🔉" if v < 0.5 else "🔊"))
        self._vol_lbl.configure(text=f"{int(v*100)}%")
        self._draw_vol()

    def _toggle_like_cur(self):
        if self.player.current:
            self.player.current.liked = not self.player.current.liked
            self.lib.save()
            self._update_np_like()
            self._refresh_list()

    # ══════════════════════════════════════════════════
    #  UI Updates
    # ══════════════════════════════════════════════════
    def _update_np(self):
        s = self.player.current
        if s:
            self._np_title.configure( text=trunc(s.title,  30))
            self._np_artist.configure(text=trunc(s.artist, 32))
            self.root.title(f"{s.title}  —  {s.artist}  |  {APP_NAME}")
            self._update_np_like()
            self._load_art(s)
            self._btn_play.configure(text="⏸")
        else:
            self._np_title.configure( text="No song playing")
            self._np_artist.configure(text="")
            self._art_lbl.configure(image="", text="♪", bg=SURF3, fg=TXT)
            self.root.title(APP_NAME)
            self._btn_play.configure(text="▶")

    def _update_np_like(self):
        if self.player.current:
            lk = self.player.current.liked
            self._np_like.configure(text="❤" if lk else "♡",
                                    fg=RED if lk else TXT)

    def _load_art(self, song: SongMeta):
        if not PIL_OK:
            col = hash_color(song.artist)
            self._art_lbl.configure(
                image="", text=song.title[:1].upper(),
                bg=col, fg="#000", font=fnt(22, True))
            return

        path = song.path
        if path in self._art_cache:
            self._art_lbl.configure(
                image=self._art_cache[path], text="", bg=SURF3)
            return

        def _thread():
            try:
                data = song.load_art()
                if data:
                    img = Image.open(BytesIO(data)).resize((60, 60), Image.LANCZOS)
                else:
                    col_str = hash_color(song.artist)
                    col_rgb = tuple(int(col_str[i:i+2], 16) for i in (1, 3, 5))
                    img = Image.new("RGB", (60, 60), col_rgb)
                    dr  = ImageDraw.Draw(img)
                    dr.text((18, 15), song.title[:1].upper(), fill=(0, 0, 0))
                ph = ImageTk.PhotoImage(img)
                self._art_cache[path] = ph
                def _upd():
                    if self.player.current and self.player.current.path == path:
                        self._art_lbl.configure(image=ph, text="", bg=SURF3)
                self.root.after(0, _upd)
            except:
                pass
        threading.Thread(target=_thread, daemon=True).start()

    def _refresh_list(self):
        key  = self._sort_sv.get() if hasattr(self, "_sort_sv") else "title"
        songs = list(self._songs_for_view())

        def sv(s):
            v = getattr(s, key, "")
            return v.lower() if isinstance(v, str) else float(v or 0)

        songs.sort(key=sv, reverse=self._sort_rev)
        self._displayed = songs

        cur_path = self.player.current.path if self.player.current else None
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, s in enumerate(songs):
            lk  = "❤" if s.liked else "♡"
            tag = "play" if s.path == cur_path else ("even" if i%2==0 else "odd")
            self.tree.insert("", "end",
                             values=(i+1, trunc(s.title, 55),
                                     trunc(s.artist, 38), trunc(s.album, 38),
                                     fmt_dur(s.duration), lk),
                             tags=(tag,))
        self._update_view_title()

        if not songs:
            self._show_empty()

    def _show_empty(self):
        """Show a welcome hint when library is empty."""
        items = self.tree.get_children()
        if not items:
            self.tree.insert("", "end",
                             values=("", "  ← Click \"+ Add Songs\" or \"+ Add Folder\" to begin!",
                                     "", "", "", ""),
                             tags=("even",))

    def _scroll_to_current(self):
        if not self.player.current:
            return
        cur = self.player.current.path
        for item in self.tree.get_children():
            try:
                idx = int(self.tree.item(item, "values")[0]) - 1
                if 0 <= idx < len(self._displayed) and self._displayed[idx].path == cur:
                    self.tree.see(item)
                    self.tree.selection_set(item)
                    return
            except:
                pass

    def _refresh_playlists(self):
        for w in self._pl_frame.winfo_children():
            w.destroy()
        for name in self.lib.playlists:
            b = tk.Button(
                self._pl_frame, text=f"♫  {name}", anchor="w",
                bg=BG2, fg=TXS, font=fnt(10),
                bd=0, padx=20, pady=9, cursor="hand2", relief="flat",
                activebackground=HOV, activeforeground=TXP)
            b.configure(command=lambda n=name: self._set_view(f"playlist:{n}"))
            b.bind("<Enter>", lambda e, b=b, n=name:
                   b.configure(bg=HOV, fg=TXP)
                   if self._view != f"playlist:{n}" else None)
            b.bind("<Leave>", lambda e, b=b, n=name:
                   b.configure(bg=SEL if self._view == f"playlist:{n}" else BG2,
                               fg=TXP if self._view == f"playlist:{n}" else TXS))
            b.bind("<Button-3>", lambda e, n=name: self._pl_ctx(e, n))
            b.pack(fill="x")

    def _load_recs(self):
        for w in self._rec_cards.winfo_children():
            w.destroy()
        tk.Label(self._rec_cards, text="Analysing your library…",
                 bg=PUR_BG, fg=TXT, font=fnt(9)).pack(anchor="w")

        def _work():
            picks = self.rec.top_picks(9)
            def _show():
                for w in self._rec_cards.winfo_children():
                    w.destroy()
                if not picks:
                    tk.Label(self._rec_cards,
                             text="Add songs and start listening — AI picks will appear here!",
                             bg=PUR_BG, fg=TXT, font=fnt(9)).pack(anchor="w")
                    return
                for song in picks:
                    self._rec_card(song)
            self.root.after(0, _show)
        threading.Thread(target=_work, daemon=True).start()

    def _rec_card(self, song: SongMeta):
        col   = hash_color(song.artist)
        frame = tk.Frame(self._rec_cards, bg=SURF2, cursor="hand2")
        frame.pack(side="left", padx=4, pady=2, ipadx=6, ipady=6)

        art = tk.Label(frame, text=song.title[:1].upper(),
                       bg=col, fg="#000", font=fnt(16, True), width=5, height=2)
        art.pack()
        tk.Label(frame, text=trunc(song.title, 15),
                 bg=SURF2, fg=TXP, font=fnt(8, True)).pack(anchor="w", pady=(3,0))
        tk.Label(frame, text=trunc(song.artist, 15),
                 bg=SURF2, fg=TXS, font=fnt(7)).pack(anchor="w")
        pb = tk.Button(frame, text="▶ Play",
                       command=lambda s=song: self.play_song(s),
                       bg=SURF3, fg=ACC, font=fnt(7, True),
                       bd=0, cursor="hand2", relief="flat", padx=6, pady=2,
                       activebackground=SEL, activeforeground=ACC_H)
        pb.pack(pady=(4, 0))

        for w in (frame, art):
            w.bind("<Enter>", lambda e, f=frame: f.configure(bg=SURF3))
            w.bind("<Leave>", lambda e, f=frame: f.configure(bg=SURF2))

    # ══════════════════════════════════════════════════
    #  Event handlers
    # ══════════════════════════════════════════════════
    def _dbl_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        try:
            idx = int(self.tree.item(sel[0], "values")[0]) - 1
            if 0 <= idx < len(self._displayed):
                self.play_song(self._displayed[idx])
        except:
            pass

    def _single_click(self, event):
        col = self.tree.identify_column(event.x)
        if col == "#6":   # ♥ column
            sel = self.tree.selection()
            if not sel:
                return
            try:
                idx = int(self.tree.item(sel[0], "values")[0]) - 1
                if 0 <= idx < len(self._displayed):
                    s = self._displayed[idx]
                    s.liked = not s.liked
                    self.lib.save()
                    if self.player.current and self.player.current.path == s.path:
                        self._update_np_like()
                    self._refresh_list()
            except:
                pass

    def _right_click(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        self.tree.selection_set(row)
        try:
            idx = int(self.tree.item(row, "values")[0]) - 1
        except:
            return
        if not (0 <= idx < len(self._displayed)):
            return
        song = self._displayed[idx]

        m = tk.Menu(self.root, tearoff=0, bg=SURF3, fg=TXP,
                    activebackground=SEL, activeforeground=TXP,
                    font=fnt(10))
        m.add_command(label="▶  Play Now",
                      command=lambda: self.play_song(song))
        m.add_command(label="⏭  Play Next",
                      command=lambda: self._insert_next(song))
        m.add_separator()
        m.add_command(label="❤  Toggle Like",
                      command=lambda: self._toggle_like(song))
        m.add_command(label="✦  Find Similar (AI)",
                      command=lambda: self._similar_win(song))

        pl_sub = tk.Menu(m, tearoff=0, bg=SURF3, fg=TXP,
                         activebackground=SEL, font=fnt(10))
        for name in self.lib.playlists:
            pl_sub.add_command(label=name,
                               command=lambda n=name, s=song: self._add_to_pl(s, n))
        pl_sub.add_separator()
        pl_sub.add_command(label="+ New Playlist",
                           command=lambda s=song: self.new_playlist(seed=s))
        m.add_cascade(label="➕  Add to Playlist", menu=pl_sub)
        m.add_separator()
        m.add_command(label="🗑  Remove from Library",
                      command=lambda: self._remove_song(song))
        m.tk_popup(event.x_root, event.y_root)

    def _on_search(self):
        q = self._search_sv.get().strip()
        if q and q != self._ph:
            results = self.lib.search(q)
            self._displayed = results
            cur = self.player.current.path if self.player.current else None
            for item in self.tree.get_children():
                self.tree.delete(item)
            for i, s in enumerate(results):
                tag = "play" if s.path == cur else ("even" if i%2==0 else "odd")
                self.tree.insert("", "end",
                    values=(i+1, trunc(s.title,55), trunc(s.artist,38),
                            trunc(s.album,38), fmt_dur(s.duration),
                            "❤" if s.liked else "♡"),
                    tags=(tag,))
            self._view_title.configure(
                text=f"Search results for \"{q}\"  —  {len(results)} found")
        else:
            self._refresh_list()

    def _search_in(self, event):
        if self._search_ent.get() == self._ph:
            self._search_ent.delete(0, "end")
            self._search_ent.configure(fg=TXP)

    def _search_out(self, event):
        if not self._search_sv.get():
            self._search_ent.configure(fg=TXT)
            self._search_ent.insert(0, self._ph)
            self._refresh_list()

    def _on_sort(self):
        self._refresh_list()

    def _toggle_rev(self):
        self._sort_rev = not self._sort_rev
        self._refresh_list()

    def _set_view(self, view: str):
        self._view = view
        for v, b in self._nav_btns.items():
            b.configure(bg=SEL if v == view else BG2,
                        fg=TXP if v == view else TXS)
        self._refresh_list()

    def _update_view_title(self):
        v = self._view
        if v == "library":
            self._view_title.configure(
                text=f"Your Library  ·  {len(self.lib.songs)} songs")
        elif v == "liked":
            self._view_title.configure(
                text=f"Liked Songs  ·  {len(self.lib.liked())}")
        elif v.startswith("playlist:"):
            name = v[9:]
            self._view_title.configure(
                text=f"♫  {name}  ·  {len(self.lib.pl_songs(name))} songs")

    def _songs_for_view(self) -> List[SongMeta]:
        v = self._view
        if v == "liked":
            return self.lib.liked()
        if v.startswith("playlist:"):
            return self.lib.pl_songs(v[9:])
        return self.lib.songs

    # ══════════════════════════════════════════════════
    #  Actions
    # ══════════════════════════════════════════════════
    def add_songs(self):
        paths = filedialog.askopenfilenames(
            title="Add Songs to Hearo",
            filetypes=[
                ("Audio Files", " ".join(f"*{e}" for e in sorted(EXTS))),
                ("MP3",  "*.mp3"), ("FLAC", "*.flac"), ("WAV",  "*.wav"),
                ("OGG",  "*.ogg"), ("M4A",  "*.m4a"),  ("All",  "*.*"),
            ])
        if paths:
            n = self.lib.add_files(list(paths))
            self._refresh_list()
            self._load_recs()
            messagebox.showinfo(APP_NAME, f"✓  Added {n} song(s) to your library.",
                                parent=self.root)

    def add_folder(self):
        folder = filedialog.askdirectory(title="Select Music Folder")
        if folder:
            n = self.lib.add_folder(folder)
            self._refresh_list()
            self._load_recs()
            messagebox.showinfo(APP_NAME,
                f"✓  Scanned folder — added {n} new song(s).", parent=self.root)

    def new_playlist(self, seed: Optional[SongMeta] = None):
        name = simpledialog.askstring("New Playlist", "Playlist name:",
                                       parent=self.root)
        if name and name.strip():
            name = name.strip()
            self.lib.playlists.setdefault(name, [])
            if seed and seed.path not in self.lib.playlists[name]:
                self.lib.playlists[name].append(seed.path)
            self.lib.save()
            self._refresh_playlists()

    def _add_to_pl(self, song: SongMeta, name: str):
        pl = self.lib.playlists.setdefault(name, [])
        if song.path not in pl:
            pl.append(song.path)
            self.lib.save()

    def _toggle_like(self, song: SongMeta):
        song.liked = not song.liked
        self.lib.save()
        self._refresh_list()
        if self.player.current and self.player.current.path == song.path:
            self._update_np_like()

    def _remove_song(self, song: SongMeta):
        if messagebox.askyesno("Remove Song",
                f'Remove "{trunc(song.title, 50)}" from library?',
                parent=self.root):
            if self.player.current and self.player.current.path == song.path:
                self.player.stop()
                self._update_np()
            self.lib.remove(song.path)
            self.queue = [s for s in self.queue if s.path != song.path]
            self._refresh_list()

    def _del_sel(self):
        sel = self.tree.selection()
        if not sel:
            return
        try:
            idx = int(self.tree.item(sel[0], "values")[0]) - 1
            if 0 <= idx < len(self._displayed):
                self._remove_song(self._displayed[idx])
        except:
            pass

    def _insert_next(self, song: SongMeta):
        if not self.queue:
            self.queue = [song]
            self.qi = 0
            return
        pos = min(self.qi + 1, len(self.queue))
        self.queue.insert(pos, song)

    def _similar_win(self, song: SongMeta):
        similar = self.rec.similar(song, n=15)
        win = tk.Toplevel(self.root)
        win.title(f"Similar to: {song.title}")
        win.configure(bg=BG2)
        win.geometry("560x440")
        win.grab_set()

        tk.Label(win, text=f"Songs similar to:  {trunc(song.title, 45)}",
                 bg=BG2, fg=PUR_H, font=fnt(12, True), pady=12
                 ).pack(fill="x", padx=18)
        tk.Label(win,
                 text="Ranked by AI similarity score (genre, artist, tempo, decade)",
                 bg=BG2, fg=TXT, font=fnt(9)).pack(anchor="w", padx=18)

        tree = ttk.Treeview(win, style="Hearo.Treeview",
                             columns=("title","artist","match"), show="headings")
        tree.heading("title",  text="Title");  tree.column("title",  width=200, anchor="w")
        tree.heading("artist", text="Artist"); tree.column("artist", width=155, anchor="w")
        tree.heading("match",  text="Match");  tree.column("match",  width=70,  anchor="center")

        ref = _song_vec(song)
        for i, s in enumerate(similar):
            pct = f"{_cosine(ref, _song_vec(s))*100:.0f}%"
            bg  = SURF if i%2==0 else "#1c1c1c"
            tree.insert("", "end",
                        values=(trunc(s.title,45), trunc(s.artist,32), pct),
                        tags=(f"r{i}",))
            tree.tag_configure(f"r{i}", background=bg)

        def _play_sel(e):
            sel2 = tree.selection()
            if sel2:
                idx2 = tree.index(sel2[0])
                if 0 <= idx2 < len(similar):
                    self.play_song(similar[idx2])
                    win.destroy()
        tree.bind("<Double-1>", _play_sel)
        tree.pack(fill="both", expand=True, padx=16, pady=8)

        bf = tk.Frame(win, bg=BG2)
        bf.pack(pady=6)
        self._mkbtn(bf, "▶  Play AI Queue from this song",
                    lambda: (self.play_song(song), self.toggle_ai_shuffle(), win.destroy()),
                    PUR, "#000", bold=True).pack(side="left", padx=6)
        self._mkbtn(bf, "Close", win.destroy, SURF3, TXS).pack(side="left", padx=6)

    def _pl_ctx(self, event, name: str):
        m = tk.Menu(self.root, tearoff=0, bg=SURF3, fg=TXP,
                    activebackground=SEL, font=fnt(10))
        m.add_command(label=f'Open "{name}"',
                      command=lambda: self._set_view(f"playlist:{name}"))
        m.add_separator()
        m.add_command(label="Delete Playlist",
                      command=lambda: self._del_pl(name))
        m.tk_popup(event.x_root, event.y_root)

    def _del_pl(self, name: str):
        if messagebox.askyesno("Delete Playlist",
                f'Delete playlist "{name}"?', parent=self.root):
            del self.lib.playlists[name]
            self.lib.save()
            self._refresh_playlists()
            if self._view == f"playlist:{name}":
                self._set_view("library")

    # ══════════════════════════════════════════════════
    #  Progress & Volume
    # ══════════════════════════════════════════════════
    def _draw_prog(self):
        cv = self._prog_cv
        cv.delete("all")
        w = cv.winfo_width() or 400
        h = cv.winfo_height() or 4
        th = 5 if (self._hover_prog or self._seek_active) else 3
        y0 = h // 2 - th // 2
        cv.create_rectangle(0, y0, w, y0 + th, fill=SURF3, outline="")
        px = int(w * self._prog_pct)
        if px > 0:
            cv.create_rectangle(0, y0, px, y0 + th, fill=ACC, outline="")
        if self._hover_prog or self._seek_active:
            cy = h // 2
            cv.create_oval(px-6, cy-6, px+6, cy+6, fill=TXP, outline="")

    def _draw_vol(self):
        cv = self._vol_cv
        cv.delete("all")
        w  = cv.winfo_width() or 90
        h  = cv.winfo_height() or 4
        y0 = h // 2 - 2
        cv.create_rectangle(0, y0, w, y0+4, fill=SURF3, outline="")
        px = int(w * self.player.volume)
        if px > 0:
            cv.create_rectangle(0, y0, px, y0+4, fill=TXS, outline="")
        cy = h // 2
        cv.create_oval(px-5, cy-5, px+5, cy+5, fill=TXP, outline="")

    def _prog_hover(self, on: bool):
        self._hover_prog = on
        self._draw_prog()

    def _seek_press(self, e):
        self._seek_active = True
        self._apply_seek(e.x)

    def _seek_move(self, e):
        if self._seek_active:
            self._apply_seek(e.x)

    def _seek_release(self, e):
        self._seek_active = False
        self._apply_seek(e.x, commit=True)
        self._draw_prog()

    def _apply_seek(self, x: int, commit: bool = False):
        w   = self._prog_cv.winfo_width() or 1
        pct = max(0.0, min(1.0, x / w))
        self._prog_pct = pct
        if commit and self.player.current:
            dur = self.player.current.duration
            if dur > 0:
                self.player.seek(pct * dur)
        self._draw_prog()

    def _vol_set(self, e):
        w = self._vol_cv.winfo_width() or 1
        v = max(0.0, min(1.0, e.x / w))
        self.player.volume = v
        self._muted = (v == 0)
        icon = "🔇" if v == 0 else ("🔉" if v < 0.5 else "🔊")
        self._btn_mute.configure(text=icon)
        self._vol_lbl.configure(text=f"{int(v*100)}%")
        self._draw_vol()

    # ══════════════════════════════════════════════════
    #  Keyboard bindings
    # ══════════════════════════════════════════════════
    def _bind_keys(self):
        r = self.root
        def not_in_search(fn):
            def wrapped(e):
                if r.focus_get() is not self._search_ent:
                    fn(e)
            return wrapped

        r.bind("<space>",  not_in_search(lambda e: self.toggle_play()))
        r.bind("<Right>",  not_in_search(lambda e: self._skip(5)))
        r.bind("<Left>",   not_in_search(lambda e: self._skip(-5)))
        r.bind("<Up>",     not_in_search(lambda e: self._vol_adj(0.05)))
        r.bind("<Down>",   not_in_search(lambda e: self._vol_adj(-0.05)))
        r.bind("n",        not_in_search(lambda e: self.next_song()))
        r.bind("p",        not_in_search(lambda e: self.prev_song()))
        r.bind("m",        not_in_search(lambda e: self.toggle_mute()))
        r.bind("s",        not_in_search(lambda e: self.toggle_shuffle()))
        r.bind("r",        not_in_search(lambda e: self.toggle_repeat()))

    def _skip(self, sec: float):
        if self.player.current:
            new = max(0.0, min(self.player.pos + sec,
                               self.player.current.duration))
            self.player.seek(new)

    def _vol_adj(self, delta: float):
        self.player.volume = self.player.volume + delta
        v = self.player.volume
        self._vol_lbl.configure(text=f"{int(v*100)}%")
        self._draw_vol()

    # ══════════════════════════════════════════════════
    #  Main tick loop
    # ══════════════════════════════════════════════════
    def _tick(self):
        try:
            if self.player.ended:
                self.next_song()
            elif self.player.playing or self.player.paused:
                pos = self.player.pos
                cur = self.player.current
                if cur:
                    dur = cur.duration or 1.0
                    if not self._seek_active:
                        self._prog_pct = min(1.0, max(0.0, pos / dur))
                        self._draw_prog()
                    self._pos_lbl.configure(text=fmt_dur(pos))
                    self._dur_lbl.configure(text=fmt_dur(dur))
            self._btn_play.configure(
                text="⏸" if self.player.playing else "▶")
        except Exception:
            pass
        self.root.after(400, self._tick)

    # ══════════════════════════════════════════════════
    #  Quit
    # ══════════════════════════════════════════════════
    def _quit(self):
        try:
            self.lib.save()
        except:
            pass
        try:
            self.player.stop()
            pygame.mixer.quit()
        except:
            pass
        self.root.destroy()

# ══════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════
def main():
    try:
        pygame.init()
    except Exception:
        pass
    HearoApp()

if __name__ == "__main__":
    main()
