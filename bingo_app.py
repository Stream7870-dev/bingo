"""
Online 2-player Bingo with Streamlit
------------------------------------
Two modes:
  1. Turn-based 5x5  - each player arranges 1-25 on their own board, players take
                       turns calling a number, first to complete 5 lines wins.
  2. Classic caller  - B-I-N-G-O cards (1-75), numbers are drawn one by one,
                       players mark called numbers and claim BINGO.

Players join the same room with a 4-letter room code from different devices.
Game state lives on the server (shared by every browser session) and each
client polls it every 2 seconds.

Run:   pip install "streamlit>=1.37"
       streamlit run bingo_app.py
Online: deploy (Streamlit Community Cloud, Render, a VPS...) or share your
        machine with a tunnel (e.g. `cloudflared tunnel --url http://localhost:8501`).
"""

import random
import string
import threading
import time
from functools import partial

import streamlit as st

st.set_page_config(page_title="Bingo Online", page_icon="🎯", layout="centered")

# Keep the 5x5 grid as a grid even on phones (Streamlit stacks columns by default).
st.markdown(
    """
    <style>
    /* ---------- Soft mauve animated background ---------- */
    .stApp {
        background: linear-gradient(135deg, #f4eaf8, #e0cbee, #c9aee0, #e9d8f4);
        background-size: 300% 300%;
        animation: drift 20s ease infinite;
    }
    @keyframes drift { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }

    /* floating glow orbs */
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

    /* frosted glass panel */
    [data-testid="stMainBlockContainer"], .block-container {
        background: rgba(255, 255, 255, 0.50);
        backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.7);
        border-radius: 24px; box-shadow: 0 10px 40px rgba(90, 50, 130, 0.18);
        padding: 2rem 1.5rem 2rem !important; margin-top: 1rem; margin-bottom: 1rem;
    }

    /* ---------- Clear, dark text ---------- */
    .stApp, .stApp p, .stApp label, .stApp span, .stApp li,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, [data-testid="stMarkdownContainer"] {
        color: #2a1740;
    }
    .stApp [data-testid="stCaptionContainer"], .stApp small { color: #4b3668 !important; }
    .stApp input { color: #2a1740 !important; background: #ffffff !important; }
    .stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"] { background: #ffffff !important; border-radius: 10px; }

    /* ---------- Keep the grid a grid, even on phones ---------- */
    div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0.4rem !important; }
    div[data-testid="stColumn"], div[data-testid="column"] { min-width: 0 !important; }

    /* ---------- Buttons / bingo cells ---------- */
    .stApp button { transition: transform .12s ease, box-shadow .12s ease, background .2s ease; }
    div[data-testid="stColumn"] button, div[data-testid="column"] button {
        padding: 0.25rem 0 !important; min-height: 2.9rem; font-weight: 800; font-size: 1.05rem;
        border-radius: 12px;
    }
    /* normal / uncalled cells */
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

    /* crossed / marked cells and main action buttons */
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

    /* red "line complete" animations */
    @keyframes drawH  { from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); } }
    @keyframes drawV  { from { clip-path: inset(0 0 100% 0); } to { clip-path: inset(0 0 0 0); } }
    @keyframes drawD  { from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); } }
    @keyframes drawD2 { from { clip-path: inset(0 0 0 100%); } to { clip-path: inset(0 0 0 0); } }

    /* ---------- win / lose effects ---------- */
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
    .raindrop { font-size: 1.3rem; opacity: .75; animation-name: fall; }
    @keyframes fall { from { transform: translateY(0) rotate(0deg); opacity: 1; }
        85% { opacity: 1; } to { transform: translateY(115vh) rotate(720deg); opacity: 0; } }
    .dim { position: fixed; inset: 0; background: rgba(40, 20, 60, .22); pointer-events: none; z-index: 9998;
        animation: fadein 1.2s ease both; }
    @keyframes fadein { from { opacity: 0; } to { opacity: 1; } }

    /* big called number and BINGO letters */
    .big-number { font-size: 3.2rem; font-weight: 900; text-align: center; line-height: 1.1;
        color: #5e2f99; text-shadow: 0 3px 14px rgba(138, 79, 199, .45); animation: pop .5s ease; }
    .hdr { text-align: center; font-weight: 900; font-size: 1.2rem; color: #5e2f99; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Shared server-side store (one per server process, shared by all sessions)
# --------------------------------------------------------------------------
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
FREE = 12  # centre cell index in classic mode
MODE_TURN, MODE_CLASSIC = "turn", "classic"
NAME_MIN, NAME_MAX = 3, 50  # allowed name length (letters, digits, anything)
MODE_LABEL = {MODE_TURN: "Turn-based 5×5", MODE_CLASSIC: "Classic caller"}


# --------------------------------------------------------------------------
# Game logic
# --------------------------------------------------------------------------
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
    """(Re)initialise everything about a round except the players and settings."""
    room["round"] = room.get("round", 0) + 1
    room["called"] = []
    room["last"] = None  # (number, player)
    room["winner"] = None  # 0, 1 or "draw"
    room["turn"] = random.choice([0, 1])
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
        while True:
            code = "".join(random.choices(string.ascii_uppercase, k=4))
            if code not in ROOMS:
                break
        room = {"code": code, "mode": mode, "names": [name, None], "opts": opts, "created": now}
        fresh_state(room)
        ROOMS[code] = room
        return code


def join_room(code, name):
    """Returns (player_index, error)."""
    with LOCK:
        room = ROOMS.get(code)
        if not room:
            return None, "Room not found. Check the code."
        names = room["names"]
        for i in (0, 1):  # reconnect with the same name
            if names[i] and names[i].lower() == name.lower():
                return i, None
        if names[1] is not None:
            return None, "This room is already full."
        names[1] = name
        # start the game for the second player
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
    """Caller draw (classic). Must be called with LOCK held."""
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
        marks.symmetric_difference_update({idx})  # toggle


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


def rematch(code):
    with LOCK:
        room = ROOMS.get(code)
        if room:
            fresh_state(room)


# ---- board setup helpers (turn mode, per-client until "Ready") ------------
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


# --------------------------------------------------------------------------
# UI helpers
# --------------------------------------------------------------------------
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
    """Inject CSS that draws an animated red line over every completed row,
    column or diagonal of the grid whose buttons use keys `{prefix}_{i}`."""
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
            elif kind == "d1":  # top-left -> bottom-right
                rules.append(
                    f'{sel}::before {{ content: ""; position: absolute; inset: -0.5rem -0.2rem; pointer-events: none; z-index: 5; '
                    f"background: linear-gradient(to top right, transparent calc(50% - 2.5px), {RED} calc(50% - 2.5px), "
                    f"{RED} calc(50% + 2.5px), transparent calc(50% + 2.5px)); "
                    f"{glow} animation: drawD .2s linear {delay} both; }}"
                )
            else:  # d2: top-right -> bottom-left
                rules.append(
                    f'{sel}::after {{ content: ""; position: absolute; inset: -0.5rem -0.2rem; pointer-events: none; z-index: 5; '
                    f"background: linear-gradient(to top left, transparent calc(50% - 2.5px), {RED} calc(50% - 2.5px), "
                    f"{RED} calc(50% + 2.5px), transparent calc(50% + 2.5px)); "
                    f"{glow} animation: drawD2 .2s linear {delay} both; }}"
                )
    # always render the element so the page layout stays stable between refreshes
    st.markdown("<style>/* lines */ " + " ".join(rules) + "</style>", unsafe_allow_html=True)


def show_result(kind, text, rkey):
    """Big animated banner plus a full-screen effect (confetti for a win, rain for a loss)."""
    rnd = random.Random(rkey)  # same pieces on every refresh, so the effect plays only once
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
        for _ in range(35):
            parts.append(
                f'<div class="fx raindrop" style="left:{rnd.randint(0, 98)}vw; '
                f'animation-duration:{rnd.uniform(2, 4):.1f}s; animation-delay:{rnd.uniform(0, 2.5):.1f}s;">💧</div>'
            )
    st.markdown("".join(parts), unsafe_allow_html=True)


def leave():
    for k in ("code", "player"):
        st.session_state.pop(k, None)


# --------------------------------------------------------------------------
# Lobby
# --------------------------------------------------------------------------
def lobby():
    st.title("🎯 Bingo Online")
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
        code = st.text_input("Room code", max_chars=4, key="j_code").strip().upper()
        if st.button("Join room", type="primary", disabled=not (len(name.strip()) >= NAME_MIN and len(code) == 4)):
            p, err = join_room(code, name.strip())
            if err:
                st.error(err)
            else:
                st.session_state.code, st.session_state.player = code, p
                st.rerun()


# --------------------------------------------------------------------------
# Game screen (a fragment: refreshes itself every 2 s without a full rerun)
# --------------------------------------------------------------------------
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
        # server-side auto draw, driven by whichever client polls first
        if (room["mode"] == MODE_CLASSIC and room["phase"] == "playing"
                and room["opts"].get("auto", 0) > 0
                and time.time() - room["last_draw"] >= room["opts"]["auto"]):
            draw_number(room)
        snap = {k: (v.copy() if isinstance(v, (list, set)) else v) for k, v in room.items()}
        snap["boards"] = [b.copy() if b else None for b in room["boards"]]
        snap["marks"] = [m.copy() for m in room["marks"]]
    room = snap
    opp = 1 - p
    names = room["names"]
    rkey = f"{code}_{room['round']}"

    st.markdown(f"### 🎯 Room `{code}` · {MODE_LABEL[room['mode']]}")
    st.write(f"**{names[p]}** (you) vs **{names[opp] or '… waiting'}**")

    # ---- waiting -----------------------------------------------------------
    if room["phase"] == "waiting":
        st.info(f"Share the room code **{code}** with your friend and ask them to join.")
        if st.button("Leave room"):
            leave()
            st.rerun(scope="app")
        return

    # ---- turn mode: board setup -------------------------------------------
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

    # ---- finished banner ---------------------------------------------------
    if room["phase"] == "finished":
        w = room["winner"]
        if w == "draw":
            show_result("draw", "🤝 It's a draw!", rkey)
        elif w == p:
            show_result("win", "🏆 BINGO! You win!", rkey)
            if ss.get("celebrated") != rkey:
                ss["celebrated"] = rkey
                st.balloons()
        else:
            show_result("lose", f"😞 {names[w]} wins this round", rkey)

    # ---- TURN MODE ---------------------------------------------------------
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

    # ---- CLASSIC MODE ------------------------------------------------------
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

    # ---- footer ------------------------------------------------------------
    f1, f2 = st.columns(2)
    if room["phase"] == "finished" and p == 0:
        f1.button("🔁 Play again", on_click=rematch, args=(code,), use_container_width=True)
    elif room["phase"] == "finished":
        f1.caption("Waiting for the host to start a rematch…")
    if f2.button("🚪 Leave room", use_container_width=True):
        leave()
        st.rerun(scope="app")


# --------------------------------------------------------------------------
if st.session_state.get("code") in ROOMS:
    game_view()
else:
    st.session_state.pop("code", None)
    lobby()