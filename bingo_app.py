import base64
import html
import json
import random
import re
import secrets
import string
import threading
import time
import urllib.parse
import urllib.request
from functools import partial
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Bingo Online", page_icon="🎯", layout="centered")

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f4eaf8, #e0cbee, #c9aee0, #e9d8f4);
        background-size: 300% 300%;
        animation: drift 20s ease infinite;
    }
    @keyframes drift { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }

    .stApp::before, .stApp::after {
        content: ""; position: fixed; z-index: 0; pointer-events: none;
        width: 46vmax; height: 46vmax; border-radius: 50%; filter: blur(70px); opacity: .55;
    }
    .stApp::before { top: -15vmax; left: -12vmax;
        background: radial-gradient(circle, #d8b4f0 0%, transparent 70%); animation: float1 16s ease-in-out infinite; }
    .stApp::after { bottom: -18vmax; right: -14vmax;
        background: radial-gradient(circle, #b79ad8 0%, transparent 70%); animation: float2 19s ease-in-out infinite; }
    @keyframes float1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(8vmax,6vmax)} }
    @keyframes float2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-7vmax,-6vmax)} }

    [data-testid="stAppViewContainer"] { position: relative; z-index: 1; }
    [data-testid="stHeader"] { background: transparent; }

    [data-testid="stMainBlockContainer"], .block-container {
        background: rgba(255, 255, 255, 0.62);
        border: 1px solid rgba(255, 255, 255, 0.7);
        border-radius: 24px; box-shadow: 0 10px 40px rgba(90, 50, 130, 0.18);
        padding: 2rem 1.5rem 2rem !important; margin-top: 1rem; margin-bottom: 1rem;
    }

    .stApp, .stApp p, .stApp label, .stApp span, .stApp li,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, [data-testid="stMarkdownContainer"] {
        color: #2a1740;
    }
    .stApp [data-testid="stCaptionContainer"], .stApp small { color: #4b3668 !important; }
    .stApp input { color: #2a1740 !important; background: #ffffff !important; }
    .stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"] { background: #ffffff !important; border-radius: 10px; }

    div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0.4rem !important; }
    div[data-testid="stColumn"], div[data-testid="column"] { min-width: 0 !important; }

    /* Invisible helper iframes (music player, drag script, sounds) should not leave blank gaps */
    div[data-testid="stElementContainer"]:has(iframe[height="0"]) {
        position: absolute; width: 0; height: 0; overflow: hidden; margin: 0; padding: 0;
    }

    .stApp button { transition: transform .12s ease, box-shadow .12s ease, background .2s ease; }
    div[data-testid="stColumn"] button, div[data-testid="column"] button {
        padding: 0.25rem 0 !important; min-height: 2.9rem; font-weight: 800; font-size: 1.05rem;
        border-radius: 12px;
    }
    button[data-testid="stBaseButton-secondary"], button[data-testid="baseButton-secondary"] {
        background: #ffffff; border: 2px solid #b79ad0; color: #2a1740;
    }
    button[data-testid="stBaseButton-secondary"] p, button[data-testid="baseButton-secondary"] p { color: #2a1740 !important; }
    button[data-testid="stBaseButton-secondary"]:hover:not(:disabled),
    button[data-testid="baseButton-secondary"]:hover:not(:disabled) {
        background: #f1e4fa; border-color: #7b4bb0; transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(110, 60, 160, .25);
    }
    button:disabled { opacity: 1 !important; cursor: not-allowed; }
    button[data-testid="stBaseButton-secondary"]:disabled,
    button[data-testid="baseButton-secondary"]:disabled { background: #f6eefb; border-color: #cdb6e0; }
    button[data-testid="stBaseButton-secondary"]:disabled p,
    button[data-testid="baseButton-secondary"]:disabled p { color: #4b3668 !important; }

    button[data-testid="stBaseButton-primary"], button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #8a4fc7, #5e2f99); border: 2px solid #4a2480; color: #ffffff;
        box-shadow: 0 4px 12px rgba(94, 47, 153, .35);
    }
    button[data-testid="stBaseButton-primary"] p, button[data-testid="baseButton-primary"] p { color: #ffffff !important; }
    button[data-testid="stBaseButton-primary"]:hover:not(:disabled),
    button[data-testid="baseButton-primary"]:hover:not(:disabled) { transform: translateY(-2px); filter: brightness(1.08); }
    button[data-testid="stBaseButton-primary"]:disabled,
    button[data-testid="baseButton-primary"]:disabled { background: linear-gradient(135deg, #8a4fc7, #5e2f99); }
    div[data-testid="stColumn"] button[data-testid="stBaseButton-primary"]:disabled p { animation: pop .35s ease; }
    @keyframes pop { 0%{transform:scale(.6)} 70%{transform:scale(1.25)} 100%{transform:scale(1)} }

    .title-wrap { text-align: center; margin: 0 0 1.2rem; }
    .title-deco { font-size: 1.3rem; letter-spacing: .5rem; animation: twinkle 2.4s ease-in-out infinite; }
    .title-main { display: flex; justify-content: center; gap: .45rem; font-size: 3rem; font-weight: 900; line-height: 1.15; }
    .stApp .title-main .l { display: inline-block; animation: bounce 2s ease-in-out infinite;
        text-shadow: 0 3px 0 rgba(42, 23, 64, .25), 0 6px 14px rgba(138, 79, 199, .45); }
    .stApp .title-main .l:nth-child(1) { color: #e11d48; animation-delay: 0s; }
    .stApp .title-main .l:nth-child(2) { color: #f2a900; animation-delay: .15s; }
    .stApp .title-main .l:nth-child(3) { color: #8a4fc7; animation-delay: .3s; }
    .stApp .title-main .l:nth-child(4) { color: #2fa89b; animation-delay: .45s; }
    .stApp .title-main .l:nth-child(5) { color: #ff6fb1; animation-delay: .6s; }
    .title-sub { margin-top: .2rem; font-weight: 800; letter-spacing: .08rem; color: #5e2f99; }
    @keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }
    @keyframes twinkle { 0%,100%{opacity:1; transform:scale(1)} 50%{opacity:.55; transform:scale(1.08)} }

    /* Floating round buttons (chat + music) */
    .st-key-chat_toggle, .st-key-music_toggle {
        position: fixed; left: 1.1rem; z-index: 10001; width: auto !important; touch-action: none;
    }
    .st-key-chat_toggle { bottom: 1.1rem; }
    .st-key-music_toggle { bottom: 5.6rem; }
    .st-key-chat_toggle button, .st-key-music_toggle button {
        min-width: 3.6rem; height: 3.6rem; border-radius: 999px !important; padding: 0 .9rem !important;
        box-shadow: 0 6px 18px rgba(60, 20, 100, .35); touch-action: none; cursor: grab;
    }
    .st-key-chat_toggle button p, .st-key-music_toggle button p { font-size: 1.35rem; }

    /* Floating panels (chat + music) */
    .st-key-chat_panel, .st-key-music_panel {
        position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);
        width: min(350px, calc(100vw - 2rem)); z-index: 10000; background: #ffffff;
        border: 1px solid #cdb6e0; border-radius: 18px;
        padding: .8rem .8rem .4rem; box-shadow: 0 12px 36px rgba(60, 20, 100, .35);
    }
    .chat-title { font-weight: 800; color: #5e2f99; margin-bottom: .4rem; }
    .chat-scroll { display: flex; flex-direction: column-reverse; gap: 6px; height: 240px; overflow-y: auto;
        padding: 8px; background: #efe6f7; border-radius: 12px; margin-bottom: .5rem; }
    .bubble { max-width: 78%; padding: 6px 10px; border-radius: 12px; font-size: .95rem;
        overflow-wrap: anywhere; color: #2a1740; }
    .bubble.me { align-self: flex-end; background: #d4b8ef; border-bottom-right-radius: 3px; }
    .bubble.them { align-self: flex-start; background: #ffffff; border-bottom-left-radius: 3px; }
    .bubble .who { display: block; font-size: .7rem; font-weight: 800; color: #6b4a8f; }
    .chat-empty { margin: auto; color: #4b3668; font-size: .9rem; }

    /* Music panel: song profile card + results */
    .st-key-music_panel { max-height: 85vh; overflow-y: auto; }
    .song-card { display: flex; gap: .6rem; background: #efe6f7; border-radius: 12px;
        padding: .5rem; margin-bottom: .6rem; align-items: center; }
    .song-card img { width: 96px; height: 54px; object-fit: cover; border-radius: 8px; flex-shrink: 0; }
    .song-info { min-width: 0; }
    .song-title { font-weight: 800; font-size: .9rem; color: #2a1740; overflow-wrap: anywhere; line-height: 1.2; }
    .song-meta { font-size: .75rem; color: #4b3668; overflow-wrap: anywhere; }

    [data-testid="InputInstructions"] { display: none !important; }
    .st-key-chat_panel [data-testid="stTextInputRootElement"],
    .st-key-chat_panel [data-baseweb="input"],
    .st-key-chat_panel [data-baseweb="base-input"],
    .st-key-chat_panel [data-testid="stTextInputRootElement"]:focus-within,
    .st-key-chat_panel [data-baseweb="input"]:focus-within,
    .st-key-chat_panel input,
    .st-key-chat_panel input:focus,
    .st-key-music_panel [data-testid="stTextInputRootElement"],
    .st-key-music_panel [data-baseweb="input"],
    .st-key-music_panel [data-baseweb="base-input"],
    .st-key-music_panel [data-testid="stTextInputRootElement"]:focus-within,
    .st-key-music_panel [data-baseweb="input"]:focus-within,
    .st-key-music_panel input,
    .st-key-music_panel input:focus {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    @keyframes drawH  { from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); } }
    @keyframes drawV  { from { clip-path: inset(0 0 100% 0); } to { clip-path: inset(0 0 0 0); } }
    @keyframes drawD  { from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); } }
    @keyframes drawD2 { from { clip-path: inset(0 0 0 100%); } to { clip-path: inset(0 0 0 0); } }

    .result { text-align: center; font-size: 1.7rem; font-weight: 900; padding: .9rem 1rem;
        border-radius: 16px; margin: .5rem 0 1rem; }
    .stApp .result { color: #ffffff !important; }
    .result.win { background: linear-gradient(120deg, #f2a900, #ff6fb1, #8a4fc7, #f2a900); background-size: 300% 300%;
        animation: pop .6s ease, shimmer 4s linear infinite, pulse 1.6s ease-in-out .6s infinite; }
    .result.lose { background: #6b5a80; animation: shake .6s ease; }
    .result.draw { background: #9b87b8; animation: pop .5s ease; }
    @keyframes shimmer { 0%{background-position:0% 50%} 100%{background-position:300% 50%} }
    @keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.04)} }
    @keyframes shake { 0%,100%{transform:translateX(0)} 20%{transform:translateX(-10px)} 40%{transform:translateX(9px)}
        60%{transform:translateX(-6px)} 80%{transform:translateX(4px)} }
    .fx { position: fixed; top: -40px; pointer-events: none; z-index: 9999; animation-timing-function: linear; animation-fill-mode: forwards; }
    .confetti { width: 10px; height: 16px; border-radius: 2px; animation-name: fall; }
    @keyframes fall { from { transform: translateY(0) rotate(0deg); opacity: 1; }
        85% { opacity: 1; } to { transform: translateY(115vh) rotate(720deg); opacity: 0; } }
    .dim { position: fixed; inset: 0; background: rgba(40, 20, 60, .22); pointer-events: none; z-index: 9998;
        animation: fadein 1.2s ease both; }
    @keyframes fadein { from { opacity: 0; } to { opacity: 1; } }

    .st-key-win_clip img { border-radius: 16px; max-height: 340px; object-fit: contain;
        box-shadow: 0 8px 24px rgba(94, 47, 153, .25); }
    .st-key-win_clip { margin-bottom: .8rem; animation: fadein 1s ease .4s both; }

    /* Special note shown under the win banner */
    .love-note { text-align: center; font-size: 1.15rem; font-weight: 700; font-style: italic;
        background: linear-gradient(135deg, #ffe4f1, #f0e0ff); border: 1.5px solid #e7b8e0; border-radius: 16px;
        padding: .8rem 1rem; margin: 0 0 1rem; animation: fadein 1.2s ease .8s both; }
    .stApp .love-note { color: #7a2e86 !important; }

    .big-number { font-size: 3.2rem; font-weight: 900; text-align: center; line-height: 1.1;
        color: #5e2f99; text-shadow: 0 3px 14px rgba(138, 79, 199, .45); animation: pop .5s ease; }
    .hdr { text-align: center; font-weight: 900; font-size: 1.2rem; color: #5e2f99; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_store():
    return {"rooms": {}, "lock": threading.RLock()}


STORE = get_store()
LOCK = STORE["lock"]
ROOMS = STORE["rooms"]

ROWS = [[r * 5 + c for c in range(5)] for r in range(5)]
COLS = [[r * 5 + c for r in range(5)] for c in range(5)]
DIAGS = [[0, 6, 12, 18, 24], [4, 8, 12, 16, 20]]
LINES = ROWS + COLS + DIAGS
FREE = 12
MODE_TURN, MODE_CLASSIC = "turn", "classic"
CODE_LEN = 5
NAME_MIN, NAME_MAX = 3, 50
MODE_LABEL = {MODE_TURN: "Turn-based 5×5", MODE_CLASSIC: "Classic caller"}
PHASE_SUB = {
    "waiting": "Waiting for your friend",
    "setup": "Set up your board",
    "playing": "Game on",
    "finished": "Round over",
}
CLIPS_DIR = Path(__file__).parent / "Clips"
# Photos in the Clips folder; one is picked at random when Conqueror wins (missing files are skipped).
# "Pic3.jpeg" is listed too in case "Pic.3.jpeg" was a typo.
WIN_CLIPS = ["win.png", "Pic2.jpeg", "Pic.3.jpeg", "Pic3.jpeg"]
SOUND_DIR = Path(__file__).parent / "sounds"
SOUND_FILES = {"win": "win.mp3", "lose": "lose.mp3", "draw": "draw.mp3"}
TONES = {
    "win": [[523, 0.0], [659, 0.15], [784, 0.3], [1047, 0.45], [1047, 0.7]],
    "lose": [[392, 0.0], [349, 0.25], [294, 0.5], [196, 0.8]],
    "draw": [[440, 0.0], [440, 0.3]],
}

# Special messages: one is picked at random when the winner is named Conqueror
# (any capitalisation). Edit the lines or the name here.
SPECIAL_NAME = "conqueror"
LOVE_NOTES = [
    "You're my favourite player, win or lose. 💜",
    "Just know I'm always going to be your biggest fan, my love. 💕",
    "You'll always be my favourite person to cheer for. ✨",
    "Did the most beautiful girl in the world just win this match? 💖",
    "Okay, my love, you've earned a hug for that one. 🤗",
    "Alright, my love, your reward is unlimited hugs from me.",
    "Alright, miss talented, I'll be needing a hug from you after this.",
    "If I were there right now, I'd pull you into my arms and forget about everything else.",
    "My favourite place would probably be right next to you, with your hand in mine.",
    "I wish I could tuck you into my arms instead of just telling you to sleep well.",
    "Just hoping my favourite person is having a beautiful day, because she makes mine beautiful just by being in it.",
    "There's a kind of beauty in you that goes far beyond what eyes can see, my love. ❤️",
    "You have no idea how many little things about you make my world a more meaningful place.",
]


def find_clip(filename):
    """Find Clips/<filename>. Ignores capital letters (matters on Linux hosts) and treats .jpg and .jpeg as the same."""
    norm = lambda n: n.lower().replace(".jpeg", ".jpg")
    base = Path(__file__).parent
    for folder in [d for d in base.iterdir() if d.is_dir() and d.name.lower() == CLIPS_DIR.name.lower()]:
        for f in folder.iterdir():
            if norm(f.name) == norm(filename):
                return f
    return None


def classic_card():
    cols = [random.sample(range(1 + 15 * c, 16 + 15 * c), 5) for c in range(5)]
    board = [cols[c][r] for r in range(5) for c in range(5)]
    board[FREE] = 0
    return board


def count_lines(marked):
    return sum(all(i in marked for i in line) for line in LINES)


def marked_idx(room, p):
    board = room["boards"][p]
    if board is None:
        return set()
    if room["mode"] == MODE_TURN:
        called = set(room["called"])
        return {i for i, n in enumerate(board) if n in called}
    return room["marks"][p]


def fresh_state(room):
    room["round"] = room.get("round", 0) + 1
    room["called"] = []
    room["last"] = None
    room["winner"] = None
    if "starter" in room:
        room["starter"] = 1 - room["starter"]
    else:
        room["starter"] = random.choice([0, 1])
    room["turn"] = room["starter"]
    room["last_draw"] = time.time()
    room["ready"] = [False, False]
    if room["mode"] == MODE_TURN:
        room["boards"] = [None, None]
        room["marks"] = [set(), set()]
        room["phase"] = "setup" if room["names"][1] else "waiting"
    else:
        room["boards"] = [classic_card(), classic_card() if room["names"][1] else None]
        room["marks"] = [{FREE}, {FREE}]
        room["phase"] = "playing" if room["names"][1] else "waiting"


def create_room(mode, name, opts):
    with LOCK:
        now = time.time()
        for c in [c for c, r in ROOMS.items() if now - r["created"] > 6 * 3600]:
            del ROOMS[c]
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(CODE_LEN))
            if (code not in ROOMS and any(ch.isdigit() for ch in code)
                    and any(ch.isalpha() for ch in code)):
                break
        room = {"code": code, "mode": mode, "names": [name, None], "opts": opts, "created": now,
                "chat": [], "music": None}
        fresh_state(room)
        ROOMS[code] = room
        return code


def join_room(code, name):
    with LOCK:
        room = ROOMS.get(code)
        if not room:
            return None, "Room not found. Check the code."
        names = room["names"]
        for i in (0, 1):
            if names[i] and names[i].lower() == name.lower():
                return i, None
        if names[1] is not None:
            return None, "This room is already full."
        names[1] = name
        if room["mode"] == MODE_TURN:
            room["phase"] = "setup"
        else:
            room["boards"][1] = classic_card()
            room["phase"] = "playing"
            room["last_draw"] = time.time()
        return 1, None


def check_turn_winner(room):
    wins = [count_lines(marked_idx(room, p)) >= 5 for p in (0, 1)]
    if all(wins):
        room["winner"], room["phase"] = "draw", "finished"
    elif wins[0] or wins[1]:
        room["winner"], room["phase"] = (0 if wins[0] else 1), "finished"


def submit_board(code, p, board):
    with LOCK:
        room = ROOMS.get(code)
        if not room or sorted(board) != list(range(1, 26)):
            return
        room["boards"][p] = list(board)
        room["ready"][p] = True
        if all(room["ready"]):
            room["phase"] = "playing"


def call_number(code, p, board, idx):
    with LOCK:
        room = ROOMS.get(code)
        if not room or room["phase"] != "playing" or room["turn"] != p:
            return
        n = board[idx]
        if n in room["called"]:
            return
        room["called"].append(n)
        room["last"] = (n, p)
        check_turn_winner(room)
        if room["phase"] == "playing":
            room["turn"] = 1 - p


def draw_number(room):
    pool = [n for n in range(1, 76) if n not in room["called"]]
    room["last_draw"] = time.time()
    if not pool:
        room["winner"], room["phase"] = "draw", "finished"
        return
    n = random.choice(pool)
    room["called"].append(n)
    room["last"] = (n, None)


def manual_draw(code):
    with LOCK:
        room = ROOMS.get(code)
        if room and room["phase"] == "playing":
            draw_number(room)


def mark_cell(code, p, board, idx):
    with LOCK:
        room = ROOMS.get(code)
        if not room or room["phase"] != "playing" or idx == FREE:
            return
        if board[idx] not in room["called"]:
            return
        marks = room["marks"][p]
        marks.symmetric_difference_update({idx})


def claim_bingo(code, p):
    with LOCK:
        room = ROOMS.get(code)
        if not room or room["phase"] != "playing":
            return
        marked = {i for i in room["marks"][p]
                  if i == FREE or room["boards"][p][i] in room["called"]}
        need_full = room["opts"].get("win") == "full"
        ok = len(marked) == 25 if need_full else count_lines(marked) >= 1
        if ok:
            room["winner"], room["phase"] = p, "finished"
        else:
            st.toast("Not a valid BINGO yet — keep marking! ❌")


def send_message(code, p, text):
    text = (text or "").strip()[:300]
    if not text:
        return
    with LOCK:
        room = ROOMS.get(code)
        if room:
            chat = room.setdefault("chat", [])
            chat.append({"p": p, "text": text})
            del chat[:-200]


def rematch(code):
    with LOCK:
        room = ROOMS.get(code)
        if room:
            fresh_state(room)


# ---------------------------------------------------------------- music

def fmt_time(sec):
    if sec is None:
        return "--:--"
    sec = int(max(0, sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def thumb_url(vid):
    return f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg"


def search_youtube(query, limit=8):
    """Return a list of {id, title, channel, duration, thumb} dicts."""
    results = []
    try:
        from yt_dlp import YoutubeDL
        opts = {"quiet": True, "extract_flat": True, "skip_download": True}
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
        for e in info.get("entries") or []:
            if not e or not e.get("id"):
                continue
            results.append({
                "id": e["id"],
                "title": e.get("title") or query,
                "channel": e.get("channel") or e.get("uploader") or "Unknown artist",
                "duration": e.get("duration"),
                "thumb": thumb_url(e["id"]),
            })
        if results:
            return results
    except Exception:
        pass
    # Fallback: scrape result page, then fetch title/channel through oEmbed
    try:
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en"})
        page = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", "ignore")
        ids = list(dict.fromkeys(re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', page)))[:6]
        for vid in ids:
            title, channel = query, "YouTube"
            try:
                o = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(
                    f"https://www.youtube.com/watch?v={vid}")
                data = json.loads(urllib.request.urlopen(o, timeout=5).read().decode())
                title, channel = data.get("title", title), data.get("author_name", channel)
            except Exception:
                pass
            results.append({"id": vid, "title": title, "channel": channel,
                            "duration": None, "thumb": thumb_url(vid)})
    except Exception:
        pass
    return results


def music_pos(m):
    """Current playback position in seconds, computed from shared state."""
    pos = m.get("pos", 0.0) + ((time.time() - m.get("ts", time.time())) if m.get("playing") else 0)
    if m.get("duration"):
        pos = min(pos, m["duration"])
    return max(0.0, pos)


def do_search():
    query = st.session_state.get("music_query", "").strip()
    if not query:
        st.toast("Type a song name ❌")
        return
    try:
        res = search_youtube(query)
    except Exception as e:
        st.toast(f"Search failed: {e}"[:120])
        res = []
    st.session_state["music_results"] = res
    if not res:
        st.toast("Couldn't find that song ❌")


def pick_song(code, p, item):
    with LOCK:
        room = ROOMS.get(code)
        if room:
            old = room.get("music") or {}
            room["music"] = {
                "id": item["id"], "title": item["title"], "channel": item["channel"],
                "duration": item.get("duration"), "thumb": item["thumb"], "by": p,
                "playing": True, "pos": 0.0, "ts": time.time(),
                "ver": old.get("ver", 0) + 1,
            }
    st.session_state["music_results"] = []


def stop_music(code):
    with LOCK:
        room = ROOMS.get(code)
        if room:
            room["music"] = None


def music_toggle_play(code):
    with LOCK:
        room = ROOMS.get(code)
        m = room and room.get("music")
        if not m:
            return
        pos = music_pos(m)
        if not m["playing"] and m.get("duration") and pos >= m["duration"] - 1:
            pos = 0.0
            m["ver"] += 1          # song had ended: restart from the top
        m["pos"], m["ts"], m["playing"] = pos, time.time(), not m["playing"]


def music_seek(code, delta=None, to=None):
    with LOCK:
        room = ROOMS.get(code)
        m = room and room.get("music")
        if not m:
            return
        pos = to if to is not None else music_pos(m) + delta
        if m.get("duration"):
            pos = min(pos, max(0, m["duration"] - 1))
        m["pos"], m["ts"] = max(0.0, pos), time.time()
        m["ver"] += 1


def toggle_music():
    st.session_state["music_open"] = not st.session_state.get("music_open", False)
    st.session_state["chat_open"] = False


# The player lives in the parent page so controls can drive it without reloading.
PLAYER_JS = """
<script>
const P = window.parent, D = P.document;
const S = __STATE__;
if (!P.__ytState) P.__ytState = {};
if (!P.YT && !D.getElementById('yt-api')) {
  const t = D.createElement('script');
  t.id = 'yt-api';
  t.src = 'https://www.youtube.com/iframe_api';
  D.head.appendChild(t);
}
function ensure() {
  if (P.__yt || !P.YT || !P.YT.Player) return;
  let w = D.getElementById('yt-wrap');
  if (!w) {
    w = D.createElement('div');
    w.id = 'yt-wrap';
    w.style.cssText = 'position:fixed;left:-1000px;top:0;width:300px;height:200px;pointer-events:none;opacity:0;';
    w.innerHTML = '<div id="yt-host"></div>';
    D.body.appendChild(w);
  }
  P.__ytReady = false;
  P.__yt = new P.YT.Player('yt-host', {
    height: '200', width: '300', host: 'https://www.youtube-nocookie.com',
    playerVars: { playsinline: 1, rel: 0, controls: 0 },
    events: { onReady: function () { P.__ytReady = true; } }
  });
}
function apply() {
  ensure();
  const pl = P.__yt;
  if (!pl || !P.__ytReady) return false;
  const st = P.__ytState;
  if (!S.id) {
    if (st.id) { pl.stopVideo(); }
    P.__ytState = {};
    return true;
  }
  if (st.id !== S.id || st.ver !== S.ver) {
    if (S.playing) pl.loadVideoById({ videoId: S.id, startSeconds: S.pos });
    else pl.cueVideoById({ videoId: S.id, startSeconds: S.pos });
  } else if (st.playing !== S.playing) {
    if (S.playing) pl.playVideo(); else pl.pauseVideo();
  }
  pl.setVolume(S.vol);
  P.__ytState = { id: S.id, ver: S.ver, playing: S.playing };
  return true;
}
let tries = 0;
const iv = setInterval(function () {
  if (apply() || ++tries > 40) clearInterval(iv);
}, 500);
</script>
"""

# Runs on the lobby screen so music never keeps playing after leaving a room.
STOP_MUSIC_JS = """
<script>
const P = window.parent;
try { if (P.__yt && P.__yt.stopVideo) P.__yt.stopVideo(); } catch (e) {}
P.__ytState = {};
</script>
"""


def music_widget(code, p, room):
    ss = st.session_state
    music = room.get("music")
    is_open = ss.get("music_open", False)
    ss.setdefault("music_vol", 80)
    vol = ss["music_vol"]

    # Player driver: always rendered so music keeps going when the panel is closed.
    if music:
        state = {"id": music["id"], "ver": music["ver"], "playing": music["playing"],
                 "pos": round(music_pos(music), 1), "vol": vol}
    else:
        state = {"id": None, "ver": 0, "playing": False, "pos": 0, "vol": vol}
    components.html(PLAYER_JS.replace("__STATE__", json.dumps(state)), height=0)

    label = "✖" if is_open else ("🎶" if music else "🎵")
    st.button(label, key="music_toggle", type="primary", on_click=toggle_music)

    if not is_open:
        return

    with st.container(key="music_panel"):
        st.markdown('<div class="chat-title">🎵 Music</div>', unsafe_allow_html=True)

        if music:
            pos = music_pos(music)
            ended = bool(music.get("duration")) and pos >= music["duration"] - 1
            if music["playing"] and ended:
                status = "⏹ Ended"
            elif music["playing"]:
                status = "▶ Playing"
            else:
                status = "⏸ Paused"
            st.markdown(
                f'<div class="song-card">'
                f'<img src="{html.escape(music["thumb"])}" alt="">'
                f'<div class="song-info">'
                f'<div class="song-title">{html.escape(music["title"])}</div>'
                f'<div class="song-meta">{html.escape(music["channel"])}</div>'
                f'<div class="song-meta">{status} · {fmt_time(pos)} / {fmt_time(music.get("duration"))}</div>'
                f'<div class="song-meta">added by {html.escape(room["names"][music["by"]])}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            if music.get("duration"):
                st.progress(min(1.0, pos / music["duration"]))
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.button("⏮", key="m_restart", on_click=music_seek, args=(code,), kwargs={"to": 0.0},
                      use_container_width=True)
            c2.button("⏪", key="m_back", on_click=music_seek, args=(code,), kwargs={"delta": -10},
                      use_container_width=True)
            c3.button("⏸" if music["playing"] else "▶", key="m_play", type="primary",
                      on_click=music_toggle_play, args=(code,), use_container_width=True)
            c4.button("⏩", key="m_fwd", on_click=music_seek, args=(code,), kwargs={"delta": 10},
                      use_container_width=True)
            c5.button("⏹", key="m_stop", on_click=stop_music, args=(code,), use_container_width=True)
            st.slider("🔊 Volume (just for you)", 0, 100, value=ss["music_vol"], key="music_vol_w",
                      on_change=lambda: ss.__setitem__("music_vol", ss["music_vol_w"]))

        with st.form("music_form", clear_on_submit=True, border=False):
            c1, c2 = st.columns([4, 2])
            c1.text_input("Song name", key="music_query", placeholder="Search a song or artist",
                          label_visibility="collapsed")
            c2.form_submit_button("🔍 Search", type="primary", use_container_width=True,
                                  on_click=do_search)

        results = ss.get("music_results") or []
        for i, r in enumerate(results):
            a, b, c = st.columns([2, 5, 2])
            a.markdown(f'<img src="{html.escape(r["thumb"])}" style="width:100%;border-radius:8px">',
                       unsafe_allow_html=True)
            b.markdown(
                f'<div class="song-title">{html.escape(r["title"])}</div>'
                f'<div class="song-meta">{html.escape(r["channel"])} · {fmt_time(r.get("duration"))}</div>',
                unsafe_allow_html=True,
            )
            c.button("▶", key=f"pick_{i}", type="primary", on_click=pick_song,
                     args=(code, p, r), use_container_width=True)
        if not music and not results:
            st.caption("Search a song, pick one from the list. Both of you will hear it.")


# ---------------------------------------------------------------- setup board

def setup_place(key, idx):
    s = st.session_state[key]
    if s["board"][idx] == 0 and s["next"] <= 25:
        s["board"][idx] = s["next"]
        s["next"] += 1


def setup_random(key):
    nums = list(range(1, 26))
    random.shuffle(nums)
    st.session_state[key] = {"board": nums, "next": 26}


def setup_clear(key):
    st.session_state[key] = {"board": [0] * 25, "next": 1}


def setup_undo(key):
    s = st.session_state[key]
    if s["next"] > 1:
        s["next"] -= 1
        s["board"][s["board"].index(s["next"])] = 0


def title_banner(sub):
    letters = "".join(f'<span class="l">{ch}</span>' for ch in "BINGO")
    st.markdown(
        '<div class="title-wrap">'
        '<div class="title-deco">🎉 ✨ 🎯 ✨ 🎉</div>'
        f'<div class="title-main">{letters}</div>'
        f'<div class="title-sub">✦ ━━ {html.escape(sub)} ━━ ✦</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def grid(prefix, labels, marked, enabled, on_click):
    for r in range(5):
        cols = st.columns(5)
        for c in range(5):
            i = r * 5 + c
            with cols[c]:
                st.button(
                    labels[i],
                    key=f"{prefix}_{i}",
                    disabled=not enabled(i),
                    type="primary" if i in marked else "secondary",
                    use_container_width=True,
                    on_click=on_click,
                    args=(i,),
                )


RED = "#e11d48"


def show_lines(prefix, marked):
    rules = []
    kinds = (
        [("row", ln) for ln in ROWS] + [("col", ln) for ln in COLS]
        + [("d1", DIAGS[0]), ("d2", DIAGS[1])]
    )
    glow = ""
    for kind, line in kinds:
        if not all(i in marked for i in line):
            continue
        for pos, i in enumerate(line):
            sel = f".st-key-{prefix}_{i}"
            delay = f"{pos * 0.2:.2f}s"
            rules.append(f"{sel}, {sel} button {{ position: relative; }}")
            if kind == "row":
                rules.append(
                    f'{sel} button::after {{ content: ""; position: absolute; left: -0.2rem; right: -0.2rem; '
                    f"top: 50%; height: 5px; margin-top: -2.5px; background: {RED}; pointer-events: none; z-index: 5; "
                    f"{glow} animation: drawH .2s linear {delay} both; }}"
                )
            elif kind == "col":
                rules.append(
                    f'{sel} button::before {{ content: ""; position: absolute; top: -0.5rem; bottom: -0.5rem; '
                    f"left: 50%; width: 5px; margin-left: -2.5px; background: {RED}; pointer-events: none; z-index: 5; "
                    f"{glow} animation: drawV .2s linear {delay} both; }}"
                )
            elif kind == "d1":
                rules.append(
                    f'{sel}::before {{ content: ""; position: absolute; inset: -0.5rem -0.2rem; pointer-events: none; z-index: 5; '
                    f"background: linear-gradient(to top right, transparent calc(50% - 2.5px), {RED} calc(50% - 2.5px), "
                    f"{RED} calc(50% + 2.5px), transparent calc(50% + 2.5px)); "
                    f"{glow} animation: drawD .2s linear {delay} both; }}"
                )
            else:
                rules.append(
                    f'{sel}::after {{ content: ""; position: absolute; inset: -0.5rem -0.2rem; pointer-events: none; z-index: 5; '
                    f"background: linear-gradient(to top left, transparent calc(50% - 2.5px), {RED} calc(50% - 2.5px), "
                    f"{RED} calc(50% + 2.5px), transparent calc(50% + 2.5px)); "
                    f"{glow} animation: drawD2 .2s linear {delay} both; }}"
                )
    st.markdown("<style>" + " ".join(rules) + "</style>", unsafe_allow_html=True)


def show_result(kind, text, rkey):
    """`text` must already be HTML-safe (escape any player names before passing them in)."""
    rnd = random.Random(rkey)
    parts = [f'<div class="result {kind}">{text}</div>']
    if kind == "win":
        colors = ["#8a4fc7", "#f2a900", "#ff6fb1", "#5ec2b7", "#e11d48", "#ffffff"]
        for _ in range(60):
            parts.append(
                f'<div class="fx confetti" style="left:{rnd.randint(0, 98)}vw; background:{rnd.choice(colors)}; '
                f'animation-duration:{rnd.uniform(2.5, 5):.1f}s; animation-delay:{rnd.uniform(0, 2.5):.1f}s;"></div>'
            )
    elif kind == "lose":
        parts.append('<div class="dim"></div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


@st.cache_data
def load_sound(name):
    return base64.b64encode((SOUND_DIR / name).read_bytes()).decode()


def play_sound(kind):
    name = SOUND_FILES[kind]
    if (SOUND_DIR / name).exists():
        data = load_sound(name)
        components.html(
            f"""
            <script>
            const a = new window.parent.Audio("data:audio/mpeg;base64,{data}");
            a.play();
            </script>
            """,
            height=0,
        )
        return
    components.html(
        """
        <script>
        const P = window.parent;
        const ctx = new (P.AudioContext || P.webkitAudioContext)();
        ctx.resume();
        const notes = %s;
        notes.forEach(function (n) {
          const o = ctx.createOscillator();
          const g = ctx.createGain();
          const t = ctx.currentTime + n[1];
          o.type = 'triangle';
          o.frequency.value = n[0];
          g.gain.setValueAtTime(0.25, t);
          g.gain.exponentialRampToValueAtTime(0.001, t + 0.45);
          o.connect(g);
          g.connect(ctx.destination);
          o.start(t);
          o.stop(t + 0.5);
        });
        </script>
        """ % json.dumps(TONES[kind]),
        height=0,
    )


def submit_chat(code, p):
    send_message(code, p, st.session_state.get("chat_msg", ""))


def toggle_chat():
    st.session_state["chat_open"] = not st.session_state.get("chat_open", False)
    st.session_state["music_open"] = False


# Makes both round buttons (chat + music) draggable, remembering their positions.
DRAG_JS = """
<script>
const P = window.parent;
const D = P.document;
P.__btnPos = P.__btnPos || {};
function place(el, x, y) {
  el.style.setProperty('left', x + 'px', 'important');
  el.style.setProperty('top', y + 'px', 'important');
  el.style.setProperty('right', 'auto', 'important');
  el.style.setProperty('bottom', 'auto', 'important');
}
function setupOne(cls) {
  const el = D.querySelector('.' + cls);
  if (!el) return;
  const b = el.querySelector('button');
  if (!b) return;
  if (P.__btnPos[cls] && !el.__down) place(el, P.__btnPos[cls].x, P.__btnPos[cls].y);
  if (el.__drag) return;
  el.__drag = true;
  let sx = 0, sy = 0, ox = 0, oy = 0, moved = false;
  b.style.touchAction = 'none';
  b.addEventListener('pointerdown', function (e) {
    el.__down = true;
    moved = false;
    sx = e.clientX;
    sy = e.clientY;
    const r = el.getBoundingClientRect();
    ox = r.left;
    oy = r.top;
    b.setPointerCapture(e.pointerId);
  });
  b.addEventListener('pointermove', function (e) {
    if (!el.__down) return;
    const dx = e.clientX - sx;
    const dy = e.clientY - sy;
    if (!moved && Math.hypot(dx, dy) < 6) return;
    moved = true;
    const x = Math.min(Math.max(0, ox + dx), P.innerWidth - el.offsetWidth);
    const y = Math.min(Math.max(0, oy + dy), P.innerHeight - el.offsetHeight);
    P.__btnPos[cls] = { x: x, y: y };
    place(el, x, y);
  });
  b.addEventListener('pointerup', function () { el.__down = false; });
  b.addEventListener('pointercancel', function () { el.__down = false; });
  b.addEventListener('click', function (e) {
    if (moved) {
      e.preventDefault();
      e.stopImmediatePropagation();
      moved = false;
    }
  }, true);
}
function setup() {
  setupOne('st-key-chat_toggle');
  setupOne('st-key-music_toggle');
}
setInterval(setup, 400);
setup();
</script>
"""


def chat_widget(code, p, room):
    ss = st.session_state
    chat, opp = room.get("chat", []), 1 - p
    is_open = ss.get("chat_open", False)
    seen_key, toast_key = f"seen_{code}", f"toasted_{code}"
    if is_open:
        ss[seen_key] = ss[toast_key] = len(chat)
    unread = sum(1 for m in chat[ss.get(seen_key, 0):] if m["p"] == opp)
    if not is_open and len(chat) > ss.get(toast_key, 0):
        new = [m for m in chat[ss.get(toast_key, 0):] if m["p"] == opp]
        if new:
            st.toast(f"💬 {room['names'][opp]}: {new[-1]['text'][:60]}")
        ss[toast_key] = len(chat)

    label = "✖" if is_open else ("💬" + (f" {unread}" if unread else ""))
    st.button(label, key="chat_toggle", type="primary", on_click=toggle_chat)
    components.html(DRAG_JS, height=0)

    if is_open:
        with st.container(key="chat_panel"):
            bubbles = "".join(
                f'<div class="bubble {"me" if m["p"] == p else "them"}">'
                + ('' if m["p"] == p else f'<span class="who">{html.escape(room["names"][m["p"]])}</span>')
                + f'{html.escape(m["text"])}</div>'
                for m in reversed(chat)
            ) or '<div class="chat-empty">No messages yet — say hi 👋</div>'
            st.markdown(
                f'<div class="chat-title">💬 Chat with {html.escape(room["names"][opp])}</div>'
                f'<div class="chat-scroll">{bubbles}</div>',
                unsafe_allow_html=True,
            )
            with st.form("chat_form", clear_on_submit=True, border=False):
                c1, c2 = st.columns([5, 1])
                c1.text_input("Message", key="chat_msg", placeholder="Type a message", max_chars=300,
                              label_visibility="collapsed")
                c2.form_submit_button("➤", type="primary", use_container_width=True,
                                      on_click=submit_chat, args=(code, p))


def leave():
    for k in ("code", "player", "chat_open", "music_open", "music_results"):
        st.session_state.pop(k, None)


def lobby():
    components.html(STOP_MUSIC_JS, height=0)
    title_banner("Play with a friend")
    st.caption("2 players · play from different devices with a room code")

    tab_create, tab_join = st.tabs(["Create room", "Join room"])

    with tab_create:
        name = st.text_input(f"Your name ({NAME_MIN}-{NAME_MAX} characters)", key="c_name", max_chars=NAME_MAX)
        mode = st.radio(
            "Game mode",
            [MODE_TURN, MODE_CLASSIC],
            format_func=lambda m: MODE_LABEL[m],
            captions=[
                "Arrange 1–25 yourself, take turns calling numbers, first to 5 lines wins.",
                "Cards with 1–75, numbers are drawn, mark them and shout BINGO.",
            ],
        )
        opts = {}
        if mode == MODE_CLASSIC:
            opts["win"] = st.radio(
                "Win condition", ["line", "full"],
                format_func=lambda w: "Any one line" if w == "line" else "Full house (all 25)",
                horizontal=True,
            )
            opts["auto"] = st.slider("Auto-draw every N seconds (0 = host draws manually)", 0, 15, 5)
        if st.button("Create room", type="primary", disabled=len(name.strip()) < NAME_MIN):
            code = create_room(mode, name.strip(), opts)
            st.session_state.code, st.session_state.player = code, 0
            st.rerun()

    with tab_join:
        name = st.text_input(f"Your name ({NAME_MIN}-{NAME_MAX} characters)", key="j_name", max_chars=NAME_MAX)
        code = st.text_input("Room code", max_chars=CODE_LEN, key="j_code").strip().upper()
        if st.button("Join room", type="primary", disabled=not (len(name.strip()) >= NAME_MIN and len(code) == CODE_LEN)):
            p, err = join_room(code, name.strip())
            if err:
                st.error(err)
            else:
                st.session_state.code, st.session_state.player = code, p
                st.rerun()


@st.fragment(run_every=2)
def game_view():
    ss = st.session_state
    code, p = ss.get("code"), ss.get("player")
    with LOCK:
        room = ROOMS.get(code)
        if room is None:
            leave()
            st.rerun(scope="app")
            return
        room.setdefault("chat", [])
        room.setdefault("music", None)
        if room["music"] and not {"id", "ver", "pos", "ts", "playing", "thumb", "channel", "by"} <= room["music"].keys():
            room["music"] = None   # leftover from an older version of the app
        if (room["mode"] == MODE_CLASSIC and room["phase"] == "playing"
                and room["opts"].get("auto", 0) > 0
                and time.time() - room["last_draw"] >= room["opts"]["auto"]):
            draw_number(room)
        snap = {k: (v.copy() if isinstance(v, (list, set, dict)) else v) for k, v in room.items()}
        snap["boards"] = [b.copy() if b else None for b in room["boards"]]
        snap["marks"] = [m.copy() for m in room["marks"]]
    room = snap
    opp = 1 - p
    names = room["names"]
    rkey = f"{code}_{room['round']}"

    title_banner(PHASE_SUB.get(room["phase"], "Let's play"))
    st.write(f"**{names[p]}** (you) vs **{names[opp] or '… waiting'}**")
    if names[1]:
        chat_widget(code, p, room)
        music_widget(code, p, room)

    if room["phase"] == "waiting":
        st.info(f"Share the room code **{code}** with your friend and ask them to join.")
        if st.button("Leave room"):
            leave()
            st.rerun(scope="app")
        return

    if room["phase"] == "setup":
        if room["ready"][p]:
            st.success("You're ready! Waiting for your opponent to finish their board…")
            grid(f"mine_{rkey}", [str(n) for n in room["boards"][p]], set(), lambda i: False, lambda i: None)
        else:
            key = f"setup_{rkey}"
            if key not in ss:
                setup_clear(key)
            s = ss[key]
            st.write("**Set up your board.** Tap cells to place "
                     + (f"**{s['next']}**" if s["next"] <= 25 else "numbers")
                     + " (1→25 in order), or randomise.")
            labels = [str(n) if n else "·" for n in s["board"]]
            grid(f"setup_{rkey}", labels, set(), lambda i: s["board"][i] == 0 and s["next"] <= 25,
                 partial(setup_place, key))
            b1, b2, b3 = st.columns(3)
            b1.button("🎲 Random", on_click=setup_random, args=(key,), use_container_width=True)
            b2.button("↩️ Undo", on_click=setup_undo, args=(key,), use_container_width=True)
            b3.button("🧹 Clear", on_click=setup_clear, args=(key,), use_container_width=True)
            st.button("✅ I'm ready", type="primary", disabled=s["next"] <= 25,
                      on_click=submit_board, args=(code, p, s["board"]))
        return

    board = room["boards"][p]
    called = room["called"]
    playing = room["phase"] == "playing"
    marked = marked_idx(room, p)

    if room["phase"] == "finished":
        w = room["winner"]
        kind = "draw" if w == "draw" else ("win" if w == p else "lose")
        if ss.get("sound_played") != rkey:
            ss["sound_played"] = rkey
            m = room.get("music")
            if not (m and m.get("playing")):
                play_sound(kind)
        if w == "draw":
            show_result("draw", "🤝 It's a draw!", rkey)
        elif w == p:
            show_result("win", "🏆 BINGO! You win!", rkey)
            if names[p].strip().lower() == SPECIAL_NAME:
                clips = list(dict.fromkeys(f for f in map(find_clip, WIN_CLIPS) if f))
                if clips:
                    clip = random.Random(f"clip_{rkey}").choice(clips)   # same photo all round, new pick next round
                    with st.container(key="win_clip"):
                        st.image(str(clip), width="stretch")
                # same note on every refresh of this round, a new random one next round
                note = random.Random(f"love_{rkey}").choice(LOVE_NOTES)
                st.markdown(f'<div class="love-note">{html.escape(note)}</div>', unsafe_allow_html=True)
            if ss.get("celebrated") != rkey:
                ss["celebrated"] = rkey
                st.balloons()
        else:
            show_result("lose", f"😞 {html.escape(names[w])} wins this round", rkey)

    if room["mode"] == MODE_TURN:
        my_turn = playing and room["turn"] == p
        if playing:
            st.info("🟢 **Your turn** — tap a number to call it." if my_turn
                    else f"⏳ **{names[opp]}** is choosing a number…")
        if room["last"]:
            n, who = room["last"]
            st.caption(f"Last call: **{n}** by {names[who]}")
        show_lines(f"play_{rkey}", marked)
        grid(f"play_{rkey}", [str(n) for n in board], marked,
             lambda i: my_turn and board[i] not in called,
             partial(call_number, code, p, board))
        if called:
            st.caption("Called so far: " + ", ".join(map(str, called)))

    else:
        if called:
            n = called[-1]
            st.markdown(f"<div class='big-number'>{'BINGO'[(n - 1) // 15]} {n}</div>", unsafe_allow_html=True)
            st.caption("Previous: " + ", ".join(map(str, called[-6:-1][::-1])) if len(called) > 1 else "")
        else:
            st.markdown("<div class='big-number'>—</div>", unsafe_allow_html=True)
        auto = room["opts"].get("auto", 0)
        if playing and auto == 0 and p == 0:
            st.button("🎱 Draw next number", type="primary", on_click=manual_draw, args=(code,))
        elif playing and auto == 0:
            st.caption("The host draws the numbers.")
        elif playing:
            st.caption(f"Numbers are drawn automatically every {auto}s.")
        hdr = st.columns(5)
        for c, ch in enumerate("BINGO"):
            hdr[c].markdown(f"<div class='hdr'>{ch}</div>", unsafe_allow_html=True)
        labels = ["★" if i == FREE else str(board[i]) for i in range(25)]
        show_lines(f"play_{rkey}", marked)
        grid(f"play_{rkey}", labels, marked,
             lambda i: playing and i != FREE and board[i] in called,
             partial(mark_cell, code, p, board))
        goal = "any one line" if room["opts"].get("win") == "line" else "a full house"
        st.caption(f"Goal: {goal}. Tap called numbers to mark them, then claim BINGO.")
        if st.button("📣 BINGO!", type="primary", disabled=not playing, use_container_width=True):
            claim_bingo(code, p)

    f1, f2 = st.columns(2)
    if room["phase"] == "finished" and p == 0:
        f1.button("🔁 Play again", on_click=rematch, args=(code,), use_container_width=True)
    elif room["phase"] == "finished":
        f1.caption("Waiting for the host to start a rematch…")
    if f2.button("🚪 Leave room", use_container_width=True):
        leave()
        st.rerun(scope="app")


if st.session_state.get("code") in ROOMS:
    game_view()
else:
    st.session_state.pop("code", None)
    lobby()