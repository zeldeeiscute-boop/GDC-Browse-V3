"""CDG Browse v2 - fully custom-drawn, aesthetic browser (single file).
Install:  pip3 install PyQt6 PyQt6-WebEngine
Run:      python3 cdg_browse.py
Every button, tab, slider, switch and panel is custom painted (no stock UI).
"""
import sys
import json
import math
import time
import re
import os
import uuid
import base64
import hashlib
import hmac
import secrets
import threading
import urllib.request
from pathlib import Path
from urllib.parse import quote, urlparse, parse_qs, urlencode
from http.server import BaseHTTPRequestHandler, HTTPServer
from html import escape


# ------------------------------------------------------------------ CDG Chat (built-in server + web app)
# Run on this computer automatically from the browser, or host it for everyone:
#     python3 cdg_browse.py --chat-server [--port 8765]
CHAT_PORT = 8765
CHAT_HTML = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CDG Chat</title>
<style>
*{box-sizing:border-box}html,body{height:100%;margin:0}
body{background:#0a0814;color:#efeaff;font:14px/1.45 -apple-system,"Segoe UI",Roboto,sans-serif;display:flex;overflow:hidden}
#side{width:220px;flex:none;background:#120d2b;border-right:1px solid rgba(239,234,255,.12);display:flex;flex-direction:column;padding:14px;gap:8px;overflow:auto}
h1{font-size:17px;margin:0 0 6px;color:#b46bff}h2{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#9d93c7;margin:12px 0 2px;font-weight:600}
.room{padding:8px 11px;border-radius:12px;cursor:pointer;color:#cfc7f0;border:1px solid transparent}
.room:hover{background:rgba(239,234,255,.08)}.room.on{background:rgba(180,107,255,.22);border-color:rgba(180,107,255,.55);color:#fff}
.on-u{font-size:13px;color:#cfc7f0;padding:2px 11px}.on-u:before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:#5dffb0;margin-right:8px}
#main{flex:1;display:flex;flex-direction:column;min-width:0}
#top{padding:14px 20px;border-bottom:1px solid rgba(239,234,255,.12);display:flex;align-items:center;gap:12px}
#title{font-weight:600;font-size:16px}#status{font-size:12px;color:#ffb36b}
#log{flex:1;overflow:auto;padding:16px 20px;display:flex;flex-direction:column;gap:6px}
.m{max-width:75%;padding:8px 13px;border-radius:16px;background:rgba(239,234,255,.09);align-self:flex-start;word-wrap:break-word;overflow-wrap:anywhere;white-space:pre-wrap}
.m.me{align-self:flex-end;background:linear-gradient(135deg,#b46bff,#7f5bff);color:#fff}
.who{font-size:11px;color:#9d93c7;margin-bottom:1px}.me .who{color:#e6d5ff}
#bar{display:flex;gap:10px;padding:14px 20px;border-top:1px solid rgba(239,234,255,.12)}
input{background:rgba(239,234,255,.08);border:1px solid rgba(239,234,255,.18);color:#efeaff;border-radius:999px;padding:10px 16px;font:inherit;outline:none}
input:focus{border-color:#b46bff}#msg{flex:1}
button{background:#b46bff;color:#1a0a33;border:0;border-radius:999px;padding:10px 20px;font:inherit;font-weight:600;cursor:pointer}button:hover{filter:brightness(1.1)}
#nr{width:100%;padding:7px 12px;font-size:13px}
#nouser{margin:auto;color:#9d93c7;text-align:center;padding:30px}
@media(max-width:640px){#side{display:none}}
</style></head><body>
<div id="side"><h1>CDG Chat</h1><h2>Rooms</h2><div id="rooms"></div><input id="nr" placeholder="New room, then Enter" maxlength="24"><h2>Online</h2><div id="online"></div></div>
<div id="main"><div id="top"><div id="title"># general</div><div id="status"></div></div><div id="log"></div>
<div id="bar"><input id="msg" placeholder="Message" maxlength="1000" autocomplete="off"><button id="send">Send</button></div></div>
<script>
var S=sessionStorage,Hh=new URLSearchParams(location.hash.slice(1));
var U=Hh.get('u')||S.getItem('u'),K=Hh.get('k')||S.getItem('k');
if(Hh.get('u')&&Hh.get('k')){S.setItem('u',U);S.setItem('k',K);history.replaceState(null,'',location.pathname);}
var room='general',after=0,timer=null,$=function(i){return document.getElementById(i)};
if(!U||!K){document.body.innerHTML='<div id="nouser">Open CDG Chat from the CDG Browse start page while signed in to your CDG account.</div>';}
else{
function api(p,body){var o={headers:{'X-CDG-User':U,'X-CDG-Key':K}};
 if(body){o.method='POST';o.headers['Content-Type']='application/json';o.body=JSON.stringify(body);}
 return fetch(p,o).then(function(r){return r.json().then(function(j){if(!r.ok)throw new Error(j.error||'Error');return j;});});}
function setStatus(t){$('status').textContent=t;}
function addMsgs(ms){var log=$('log'),stick=log.scrollHeight-log.scrollTop-log.clientHeight<80;
 ms.forEach(function(m){after=Math.max(after,m.id);var d=document.createElement('div');d.className='m'+(m.user===U?' me':'');
  var w=document.createElement('div');w.className='who';w.textContent=m.user+' · '+new Date(m.ts*1000).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
  var t=document.createElement('div');t.textContent=m.text;d.appendChild(w);d.appendChild(t);log.appendChild(d);});
 if(stick||ms.length&&after===ms[ms.length-1].id&&log.children.length===ms.length)log.scrollTop=log.scrollHeight;}
function drawRooms(rs){var el=$('rooms');el.textContent='';rs.forEach(function(r){var d=document.createElement('div');
 d.className='room'+(r===room?' on':'');d.textContent='# '+r;d.onclick=function(){go(r);};el.appendChild(d);});}
function drawOnline(us){var el=$('online');el.textContent='';us.forEach(function(u){var d=document.createElement('div');d.className='on-u';d.textContent=u;el.appendChild(d);});}
function poll(){var r=room;
 api('/api/poll?room='+encodeURIComponent(r)+'&after='+after).then(function(j){
  if(r!==room)return;setStatus('');addMsgs(j.msgs);drawRooms(j.rooms);drawOnline(j.online);
 }).catch(function(e){setStatus(e.message==='Failed to fetch'?'Reconnecting...':e.message);})
 .then(function(){clearTimeout(timer);timer=setTimeout(poll,1200);});}
function go(r){clearTimeout(timer);room=r;after=0;$('log').textContent='';$('title').textContent='# '+r;poll();}
function send(){var t=$('msg').value.trim();if(!t)return;$('msg').value='';
 api('/api/send',{room:room,text:t}).then(function(){clearTimeout(timer);poll();}).catch(function(e){setStatus(e.message);});}
$('send').onclick=send;$('msg').onkeydown=function(e){if(e.key==='Enter')send();};
$('nr').onkeydown=function(e){if(e.key!=='Enter')return;var n=$('nr').value.trim().toLowerCase().replace(/\s+/g,'-');if(!n)return;$('nr').value='';
 api('/api/room',{name:n}).then(function(j){go(j.room);}).catch(function(er){setStatus(er.message);});};
poll();
}
</script></body></html>"""


def run_chat_server(host="127.0.0.1", port=CHAT_PORT):
    """Tiny multi-user chat server (standard library only). Users are identified by a name plus a
    secret key that their browser derives from their CDG account; the first claim of a name wins."""
    from http.server import ThreadingHTTPServer
    base = Path.home() / ".cdg_browse"
    base.mkdir(parents=True, exist_ok=True)
    store = base / "chat_server.json"
    lock = threading.Lock()
    st = {"rooms": {"general": []}, "users": {}, "next": 1}
    try:
        d = json.loads(store.read_text())
        if isinstance(d.get("rooms"), dict) and isinstance(d.get("users"), dict):
            st = d
            st.setdefault("next", 1)
            st["rooms"].setdefault("general", [])
    except Exception:
        pass
    seen, last_send = {}, {}
    NAME_RE = re.compile(r"^[A-Za-z0-9_]{2,20}$")
    ROOM_RE = re.compile(r"^[a-z0-9_-]{2,24}$")
    local = host in ("127.0.0.1", "localhost")

    def persist():
        try:
            tmp = store.with_suffix(".tmp")
            tmp.write_text(json.dumps(st))
            os.replace(tmp, store)
            os.chmod(store, 0o600)
        except Exception:
            pass

    class H(BaseHTTPRequestHandler):
        server_version = "CDGChat"

        def log_message(self, *a):
            pass

        def _out(self, code, body, ctype="application/json"):
            b = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(b)

        def _err(self, code, msg):
            self._out(code, {"error": msg})

        def _host_ok(self):
            return (not local) or self.headers.get("Host", "").split(":")[0] in ("127.0.0.1", "localhost")

        def _auth(self):
            u, k = self.headers.get("X-CDG-User", ""), self.headers.get("X-CDG-Key", "")
            if not NAME_RE.match(u) or not re.fullmatch(r"[0-9a-f]{64}", k):
                return None
            hk, low = hashlib.sha256(k.encode()).hexdigest(), u.lower()
            with lock:
                cur = st["users"].get(low)
                if cur is None:
                    if len(st["users"]) >= 5000:
                        return None
                    st["users"][low] = {"h": hk, "n": u}
                    persist()
                    cur = st["users"][low]
                elif not hmac.compare_digest(cur["h"], hk):
                    return None
                seen[low] = (cur["n"], time.time())
                return cur["n"]

        def do_GET(self):
            if not self._host_ok():
                return self._err(403, "Bad host")
            u = urlparse(self.path)
            if u.path in ("/", "/index.html"):
                return self._out(200, CHAT_HTML.encode(), "text/html")
            if u.path != "/api/poll":
                return self._err(404, "Not found")
            me = self._auth()
            if not me:
                return self._err(403, "That name is taken by another account, or your key is invalid")
            q = parse_qs(u.query)
            room = (q.get("room", ["general"])[0] or "general")
            try:
                after = max(0, int(q.get("after", ["0"])[0]))
            except ValueError:
                after = 0
            with lock:
                if room not in st["rooms"]:
                    return self._err(404, "No such room")
                ms = [m for m in st["rooms"][room] if m["id"] > after]
                if after == 0:
                    ms = ms[-100:]
                now = time.time()
                online = sorted(n for n, t in seen.values() if now - t < 20)
                return self._out(200, {"msgs": ms, "rooms": sorted(st["rooms"]), "online": online})

        def do_POST(self):
            if not self._host_ok():
                return self._err(403, "Bad host")
            me = self._auth()
            if not me:
                return self._err(403, "That name is taken by another account, or your key is invalid")
            try:
                n = int(self.headers.get("Content-Length", "0"))
                if n > 4096:
                    return self._err(413, "Too big")
                body = json.loads(self.rfile.read(n) or b"{}")
                if not isinstance(body, dict):
                    raise ValueError
            except Exception:
                return self._err(400, "Bad request")
            path = urlparse(self.path).path
            with lock:
                if path == "/api/send":
                    room, text = str(body.get("room", "")), str(body.get("text", "")).strip()[:1000]
                    if room not in st["rooms"] or not text:
                        return self._err(400, "Nothing to send")
                    now = time.time()
                    if now - last_send.get(me, 0) < 0.4:
                        return self._err(429, "Slow down")
                    last_send[me] = now
                    st["rooms"][room].append({"id": st["next"], "user": me, "text": text, "ts": int(now)})
                    st["next"] += 1
                    st["rooms"][room] = st["rooms"][room][-500:]
                    persist()
                    return self._out(200, {"ok": True})
                if path == "/api/room":
                    name = str(body.get("name", "")).strip().lower()
                    if not ROOM_RE.match(name):
                        return self._err(400, "Room names are 2-24 letters, numbers, - or _")
                    if name not in st["rooms"]:
                        if len(st["rooms"]) >= 50:
                            return self._err(400, "Too many rooms")
                        st["rooms"][name] = []
                        persist()
                    return self._out(200, {"room": name})
            return self._err(404, "Not found")

    try:
        srv = ThreadingHTTPServer((host, port), H)
    except OSError as e:
        print("CDG Chat: couldn't start on port %d (%s). Is it already running?" % (port, e))
        return
    srv.daemon_threads = True
    if not local:
        import socket
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "your-ip"
        print("CDG Chat server running on port %d." % port)
        print("Friends on your network: set Chat server to http://%s:%d in CDG Browse > Settings." % (ip, port))
        print("For the internet, put this behind HTTPS (e.g. a reverse proxy) so keys are encrypted.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if "--chat-server" in sys.argv:
    _a = sys.argv
    try:
        _p = int(_a[_a.index("--port") + 1]) if "--port" in _a else CHAT_PORT
    except (ValueError, IndexError):
        _p = CHAT_PORT
    run_chat_server("127.0.0.1" if "--local" in _a else "0.0.0.0", _p)
    sys.exit(0)


from PyQt6.QtCore import Qt, QUrl, QTimer, QRectF, QPointF, pyqtSignal, QVariantAnimation, QEvent, QEasingCurve, QPropertyAnimation, QSize, QUrlQuery, QRect, QPoint
from PyQt6.QtGui import (QColor, QPainter, QPen, QBrush, QFont, QFontMetrics, QLinearGradient,
                         QRadialGradient, QPolygonF, QKeySequence, QShortcut, QCursor, QPainterPath, QPixmap, QDesktopServices)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QStackedWidget, QScrollArea, QFrame, QLabel,
                             QLineEdit, QPlainTextEdit, QSizePolicy, QGraphicsOpacityEffect)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (QWebEngineProfile, QWebEnginePage, QWebEngineContextMenuRequest,
                                   QWebEngineSettings, QWebEngineDownloadRequest, QWebEngineUrlRequestInterceptor,
                                   QWebEngineUrlRequestInfo, QWebEngineScript)

DIR = Path.home() / ".cdg_browse"
SAVE = DIR / "save_v2.json"

THEMES = {
    "Neon Night": {"bg": "#0a0814", "bg2": "#1d1048", "text": "#efeaff", "accent": "#b46bff"},
    "Sakura": {"bg": "#1a0e16", "bg2": "#41183a", "text": "#ffe8f2", "accent": "#ff7eb6"},
    "Ocean Depths": {"bg": "#06121b", "bg2": "#0b3a5c", "text": "#dff6ff", "accent": "#3ccfff"},
    "Sunset": {"bg": "#1c0e0e", "bg2": "#52201f", "text": "#fff0e0", "accent": "#ff8a3c"},
    "Aurora": {"bg": "#06150e", "bg2": "#0d4a3c", "text": "#e3fff1", "accent": "#5dffb0"},
    "Frost": {"bg": "#eef2fb", "bg2": "#d3ddff", "text": "#1c2233", "accent": "#5b7cff"},
    "Graphite": {"bg": "#0d0d10", "bg2": "#2a2a31", "text": "#f2f2f4", "accent": "#d0d0d8"},
    "Lavender": {"bg": "#f6f1ff", "bg2": "#e0d2ff", "text": "#2a1f45", "accent": "#9a6bff"},
}

SHOP = {
    "theme_sakura": {"name": "Sakura Theme", "desc": "Soft pink blossom vibes.", "price": 50, "kind": "theme", "value": "Sakura"},
    "theme_ocean": {"name": "Ocean Depths Theme", "desc": "Deep blue calm.", "price": 50, "kind": "theme", "value": "Ocean Depths"},
    "theme_frost": {"name": "Frost Theme", "desc": "Crisp, bright light mode.", "price": 40, "kind": "theme", "value": "Frost"},
    "theme_sunset": {"name": "Sunset Theme", "desc": "Warm orange glow.", "price": 75, "kind": "theme", "value": "Sunset"},
    "theme_aurora": {"name": "Aurora Theme", "desc": "Northern lights green.", "price": 100, "kind": "theme", "value": "Aurora"},
    "theme_graphite": {"name": "Graphite Theme", "desc": "Neutral, distraction-free dark.", "price": 60, "kind": "theme", "value": "Graphite"},
    "theme_lavender": {"name": "Lavender Theme", "desc": "Soft purple light mode.", "price": 60, "kind": "theme", "value": "Lavender"},
    "accent_picker": {"name": "Custom Accent Color", "desc": "Pick any accent color with swatches and a rainbow slider.", "price": 40, "kind": "feature"},
    "pill_buttons": {"name": "Pill Buttons", "desc": "Ultra-round buttons and panels.", "price": 60, "kind": "feature"},
    "gradient_bar": {"name": "Gradient Toolbar", "desc": "A glowing gradient across your toolbar.", "price": 80, "kind": "feature"},
    "orbs": {"name": "Floating Orbs", "desc": "Soft glowing orbs drift behind the whole browser.", "price": 90, "kind": "feature"},
    "rainbow_accent": {"name": "Rainbow Accent", "desc": "Your accent color slowly cycles through every hue.", "price": 150, "kind": "feature"},
}

ACH = {
    "first_steps": {"name": "First Steps", "desc": "Visit your first page", "coins": 10},
    "explorer": {"name": "Explorer", "desc": "Visit 10 pages", "coins": 25},
    "marathon": {"name": "Web Marathon", "desc": "Visit 50 pages", "coins": 60},
    "stylist": {"name": "Stylist", "desc": "Change your theme or accent", "coins": 10},
    "cookie": {"name": "Cookie Monster", "desc": "Open the Cookie Jar", "coins": 10},
    "shopper": {"name": "Big Spender", "desc": "Buy something in the CDG Shop", "coins": 15},
    "multitask": {"name": "Multitasker", "desc": "Have 5 tabs open", "coins": 20},
    "builder": {"name": "Builder", "desc": "Customize your browser layout", "coins": 15},
    "spacer": {"name": "Space Cadet", "desc": "Create a second Space", "coins": 15},
}

ENGINES = {
    "DuckDuckGo": ("https://duckduckgo.com/", "q"),
    "Google": ("https://www.google.com/search", "q"),
    "Bing": ("https://www.bing.com/search", "q"),
    "Brave": ("https://search.brave.com/search", "q"),
}

SWATCHES = ["#b46bff", "#ff7eb6", "#3ccfff", "#ff8a3c", "#5dffb0", "#ffd166", "#ff5d5d"]

DEFAULT_ORDER = ["back", "forward", "reload", "home", "address", "coins", "account", "adblock", "shop", "build", "settings"]
LOCKED = ("address", "build", "settings")
ITEM_NAMES = {"back": "Back", "forward": "Forward", "reload": "Reload", "home": "Home", "address": "Address bar",
              "coins": "Coin counter", "account": "Account button", "adblock": "Ad blocker button", "shop": "Shop button", "build": "Build button", "settings": "Settings button"}
TEMPLATES = {
    "Classic": dict(toolbar="top", tabpos="top", density="cozy", hidden=[], order=DEFAULT_ORDER),
    "Minimal": dict(toolbar="top", tabpos="top", density="compact", hidden=["home", "shop", "coins"], order=DEFAULT_ORDER),
    "Bottom Bar": dict(toolbar="bottom", tabpos="top", density="cozy", hidden=[], order=DEFAULT_ORDER),
    "Sidebar": dict(toolbar="top", tabpos="side", density="cozy", hidden=[], order=DEFAULT_ORDER),
    "Focus": dict(toolbar="bottom", tabpos="side", density="compact", hidden=["home", "shop", "coins", "forward"], order=DEFAULT_ORDER),
    "Power": dict(toolbar="top", tabpos="side", density="roomy", hidden=[],
                  order=["address", "back", "forward", "reload", "home", "coins", "account", "adblock", "shop", "build", "settings"]),
}

TILES = [("YouTube", "https://www.youtube.com", "#ff6b6b"), ("Wikipedia", "https://www.wikipedia.org", "#b8c0d4"),
         ("GitHub", "https://github.com", "#a29bfe"), ("Reddit", "https://www.reddit.com", "#ff9f43"),
         ("Spotify", "https://open.spotify.com", "#55efc4"), ("Maps", "https://maps.google.com", "#74d7ff"),
         ("CDG Chat", "https://cdg.start/chat", "#b46bff")]
DEFAULT_TILES = [{"name": n, "url": u, "color": c} for n, u, c in TILES]
SOCIAL_TILES = [("Instagram", "https://www.instagram.com", "#e1306c"), ("TikTok", "https://www.tiktok.com", "#25f4ee"),
                ("X", "https://x.com", "#cfd6e4"), ("Facebook", "https://www.facebook.com", "#4c8bf5"),
                ("Reddit", "https://www.reddit.com", "#ff6a3d"), ("Snapchat", "https://www.snapchat.com", "#fffc00"),
                ("Discord", "https://discord.com/app", "#7c8cff"), ("Pinterest", "https://www.pinterest.com", "#e60023"),
                ("Twitch", "https://www.twitch.tv", "#9146ff"), ("Threads", "https://www.threads.net", "#b9b9c9"),
                ("WhatsApp", "https://web.whatsapp.com", "#25d366"), ("LinkedIn", "https://www.linkedin.com", "#3b8fd9"),
                ("Bluesky", "https://bsky.app", "#3b9cff")]
SOCIAL_HOSTS = ("instagram.com", "tiktok.com", "facebook.com", "snapchat.com", "twitch.tv", "threads.net", "x.com", "twitter.com")
CODEC_JS = r"""(function(){var v=document.createElement('video'),a=document.createElement('audio');return JSON.stringify({h264:v.canPlayType('video/mp4; codecs="avc1.42E01E"'),aac:a.canPlayType('audio/mp4; codecs="mp4a.40.2"'),vp9:v.canPlayType('video/webm; codecs="vp9"'),opus:a.canPlayType('audio/webm; codecs="opus"')})})()"""

DEFAULTS = {
    "coins": 0, "owned": [], "unlocked": [], "visits": 0,
    "theme": "Neon Night", "accent": "", "radius": 14, "win_radius": 22,
    "pill": False, "gradient": False, "orbs": False, "rainbow": False,
    "achievements_on": True, "home": "start", "engine": "DuckDuckGo",
    "spaces": [{"name": "Home", "theme": "Neon Night"}], "space": 0,
    "toolbar": "top", "tabpos": "top", "density": "cozy", "template": "Classic",
    "tb_order": list(DEFAULT_ORDER), "tb_hidden": [],
    "tiles": [dict(t) for t in DEFAULT_TILES],
    "history": [], "searches": [],
    "adblock": True, "adblock_allow": [], "blocked": 0, "chat_tile": False, "chat_url": "",
}

D = {}
P = {}
RAINBOW_H = 0.0
AL_C = Qt.AlignmentFlag.AlignCenter.value
AL_L = (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter).value
AL_R = (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter).value
IS_MAC = sys.platform == "darwin"
MOD = "\u2318" if IS_MAC else "Ctrl+"
_MENU = None
CHAT_PROC = None


# ------------------------------------------------------------------ accounts, history, suggestions
ACCTS = DIR / "accounts.json"
SESSION = DIR / "session.json"
OAUTH = DIR / "oauth.json"
CUR = None  # signed-in account: {"id", "name", "provider"} or None for guest
GOOGLE_DOMAINS = {"gmail.com", "googlemail.com"}
PROVIDER_NAMES = {"google": "Signed in with Google", "github": "Signed in with GitHub",
                  "username": "CDG username account", "email": "Email account"}


def safe_id(x):
    return re.sub(r"[^A-Za-z0-9_-]", "", str(x))[:60] or "x"


def data_path():
    return SAVE if not CUR else DIR / f"acct_{safe_id(CUR['id'])}.json"


def load_session():
    global CUR
    CUR = None
    try:
        d = json.loads(SESSION.read_text())
        if isinstance(d, dict) and d.get("id") and d.get("name"):
            CUR = {"id": safe_id(d["id"]), "name": str(d["name"])[:60], "provider": d.get("provider", "username")}
    except Exception:
        pass


def write_session():
    try:
        SESSION.write_text(json.dumps(CUR or {}))
    except Exception:
        pass


def users_load():
    try:
        u = json.loads(ACCTS.read_text()).get("users", {})
        return u if isinstance(u, dict) else {}
    except Exception:
        return {}


def users_save(users):
    try:
        ACCTS.write_text(json.dumps({"users": users}))
        os.chmod(ACCTS, 0o600)
    except Exception:
        pass


def pw_hash(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, 200_000).hex()


def oauth_cfg():
    cfg = {}
    try:
        cfg = json.loads(OAUTH.read_text())
    except Exception:
        pass
    return {"google_id": os.environ.get("CDG_GOOGLE_CLIENT_ID") or cfg.get("google_client_id", ""),
            "google_secret": os.environ.get("CDG_GOOGLE_CLIENT_SECRET") or cfg.get("google_client_secret", ""),
            "github_id": os.environ.get("CDG_GITHUB_CLIENT_ID") or cfg.get("github_client_id", "")}


def _http_json(url, data=None, headers=None, timeout=20):
    body = urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers={"Accept": "application/json", "User-Agent": "CDG-Browse",
                                                          **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def github_flow(win, cfg, run):
    """GitHub device flow: show a code, the user approves it in their browser, we poll."""
    def ev(kind, **kw):
        win.oauthEvent.emit(kind, dict(kw, run=run))
    try:
        d = _http_json("https://github.com/login/device/code", {"client_id": cfg["github_id"], "scope": "read:user"})
        if "user_code" not in d:
            raise RuntimeError(d.get("error_description") or d.get("error") or "GitHub refused the request")
        ev("code", code=d["user_code"], url=d["verification_uri"])
        interval, deadline = int(d.get("interval", 5)), time.time() + int(d.get("expires_in", 600))
        while time.time() < deadline and win._oauth_run == run:
            time.sleep(interval)
            if win._oauth_run != run:
                return
            t = _http_json("https://github.com/login/oauth/access_token",
                           {"client_id": cfg["github_id"], "device_code": d["device_code"],
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"})
            if t.get("access_token"):
                u = _http_json("https://api.github.com/user", headers={"Authorization": "Bearer " + t["access_token"]})
                ev("done", id="github_" + str(u["id"]), name=u.get("name") or u.get("login") or "GitHub user",
                   provider="github")
                return
            err = t.get("error")
            if err == "slow_down":
                interval += 5
            elif err and err != "authorization_pending":
                raise RuntimeError(t.get("error_description") or err)
        if win._oauth_run == run:
            ev("error", msg="GitHub sign-in timed out.")
    except Exception as ex:
        ev("error", msg=f"GitHub sign-in failed: {ex}")


def google_flow(win, cfg, run):
    """Google loopback + PKCE flow in the system browser (Google blocks embedded browsers)."""
    def ev(kind, **kw):
        win.oauthEvent.emit(kind, dict(kw, run=run))
    srv = None
    try:
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        state = secrets.token_urlsafe(16)
        got = {}

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
                if "code" in q or "error" in q:
                    got.update(q)
                body = (b"<html><body style='font-family:sans-serif;text-align:center;margin-top:18vh'>"
                        b"<h2>You're signed in to CDG Browse</h2><p>You can close this tab.</p></body></html>")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass
        srv = HTTPServer(("127.0.0.1", 0), H)
        srv.timeout = 1
        redirect = f"http://127.0.0.1:{srv.server_address[1]}"
        ev("open", url="https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
            "client_id": cfg["google_id"], "redirect_uri": redirect, "response_type": "code",
            "scope": "openid profile", "state": state, "code_challenge": challenge, "code_challenge_method": "S256"}))
        deadline = time.time() + 300
        while not got and time.time() < deadline and win._oauth_run == run:
            srv.handle_request()
        if win._oauth_run != run:
            return
        if not got:
            raise RuntimeError("timed out")
        if got.get("state") != state or "code" not in got:
            raise RuntimeError(got.get("error") or "sign-in was interrupted")
        form = {"code": got["code"], "client_id": cfg["google_id"], "redirect_uri": redirect,
                "grant_type": "authorization_code", "code_verifier": verifier}
        if cfg["google_secret"]:
            form["client_secret"] = cfg["google_secret"]
        tok = _http_json("https://oauth2.googleapis.com/token", form)
        info = _http_json("https://openidconnect.googleapis.com/v1/userinfo",
                          headers={"Authorization": "Bearer " + tok["access_token"]})
        ev("done", id="google_" + str(info["sub"]), name=info.get("name") or "Google user", provider="google")
    except Exception as ex:
        ev("error", msg=f"Google sign-in failed: {ex}")
    finally:
        if srv is not None:
            srv.server_close()


def search_query(url):
    """If url is a results page of a known engine, return the query text."""
    p = urlparse(url)
    for action, param in ENGINES.values():
        a = urlparse(action)
        if p.hostname == a.hostname and p.path.rstrip("/") == a.path.rstrip("/"):
            v = parse_qs(p.query).get(param)
            if v and v[0].strip():
                return v[0].strip()[:120]
    return None


def record_visit(url, title):
    now = time.time()
    q = search_query(url)
    if q:
        for s in D["searches"]:
            if s["q"].lower() == q.lower():
                s["t"], s["n"] = now, s.get("n", 1) + 1
                break
        else:
            D["searches"].append({"q": q, "t": now, "n": 1})
        D["searches"] = sorted(D["searches"], key=lambda s: -s.get("t", 0))[:150]
        return
    key = url.split("#")[0]
    for h in D["history"]:
        if h["url"] == key:
            h["t"], h["n"] = now, h.get("n", 1) + 1
            if title:
                h["title"] = title
            break
    else:
        D["history"].append({"url": key, "title": title or "", "host": urlparse(url).hostname or "", "t": now, "n": 1})
    D["history"] = sorted(D["history"], key=lambda h: -h.get("t", 0))[:400]


def _words(s):
    return re.findall(r"[a-z0-9]+", s.lower())


def suggestions(text):
    """Recent sites / recent searches / recommended searches, all from your own history."""
    q = text.strip().lower()
    out = {"sites": [], "searches": [], "rec": []}
    if not q:
        return out
    best = {}
    for h in D["history"]:
        host = (h.get("host") or "").lower()
        bare = host[4:] if host.startswith("www.") else host
        title = (h.get("title") or "").lower()
        if bare.startswith(q):
            sc = 3
        elif title.startswith(q) or any(w.startswith(q) for w in _words(title)):
            sc = 2
        elif len(q) >= 3 and (q in bare or q in title):
            sc = 1
        else:
            continue
        key = (sc, h.get("n", 1), h.get("t", 0))
        if bare not in best or key > best[bare][0]:
            best[bare] = (key, h)
    out["sites"] = [h for _, h in sorted(best.values(), key=lambda x: x[0], reverse=True)[:4]]
    ss = []
    for s in D["searches"]:
        ql = s["q"].lower()
        sc = 2 if ql.startswith(q) else 1 if (len(q) >= 3 and q in ql) else 0
        if sc and ql != q:
            ss.append((sc, s.get("t", 0), s["q"]))
    ss.sort(key=lambda x: (x[0], x[1]), reverse=True)
    out["searches"] = [x[2] for x in ss[:3]]
    shown = {x.lower() for x in out["searches"]} | {q}
    cand = {}

    def add(t, w):
        t = " ".join(t.split())
        tl = t.lower()
        if not (2 <= len(tl) <= 48) or tl in shown:
            return
        if tl.startswith(q):
            w += 100
        elif any(x.startswith(q) for x in _words(tl)):
            w += 10
        else:
            return
        cand[tl] = cand.get(tl, 0) + w
    for s in D["searches"]:
        add(s["q"], 3 + s.get("n", 1))
    for h in D["history"]:
        n = h.get("n", 1)
        host = (h.get("host") or "").lower()
        bare = host[4:] if host.startswith("www.") else host
        parts = bare.split(".")
        add(parts[-2] if len(parts) >= 2 else bare, 2 + n)
        title = h.get("title") or ""
        for seg in re.split(r"\s[-|\u2013\u2014:\u00b7]\s", title):
            if seg and len(seg) <= 40:
                add(seg, 1 + n / 2)
        for w in _words(title):
            if len(w) >= 3:
                add(w, 0.5)
    out["rec"] = [k for k, _ in sorted(cand.items(), key=lambda kv: -kv[1])[:5]]
    return out


# ------------------------------------------------------------------ ad blocker
BUILTIN_AD_DOMAINS = frozenset("""
doubleclick.net googlesyndication.com googleadservices.com googletagservices.com adservice.google.com 2mdn.net
adnxs.com adsrvr.org adform.net advertising.com amazon-adsystem.com openx.net rubiconproject.com pubmatic.com
casalemedia.com criteo.com criteo.net taboola.com outbrain.com revcontent.com mgid.com smartadserver.com
adcolony.com moatads.com doubleverify.com adsafeprotected.com scorecardresearch.com quantserve.com quantcount.com
exelator.com bluekai.com krxd.net demdex.net everesttech.net agkn.com rlcdn.com bidswitch.net 33across.com
sharethrough.com indexww.com contextweb.com lijit.com sovrn.com yieldmo.com teads.tv media.net zedo.com
tribalfusion.com adtechus.com serving-sys.com mathtag.com mookie1.com nexac.com tapad.com liadm.com adroll.com
perfectaudience.com adblade.com adsymptotic.com adform.com ads.yahoo.com analytics.yahoo.com
ads.twitter.com static.ads-twitter.com ads-api.twitter.com analytics.twitter.com ads.linkedin.com ads.pinterest.com
an.facebook.com google-analytics.com hotjar.com fullstory.com mouseflow.com crazyegg.com chartbeat.com
popads.net popcash.net propellerads.com juicyads.com exoclick.com trafficjunky.net adsterra.com clickadu.com
hilltopads.net onclickads.net ad-maven.com admaven.com richpush.co trafficfactory.biz adspyglass.com
adkernel.com appnexus.com yieldlab.net improvedigital.com gumgum.com triplelift.com 1rx.io spotxchat.com
spotx.tv springserve.com connatix.com undertone.com conversantmedia.com adition.com emxdgt.com
ml314.com bounceexchange.com bouncex.net cdn.taboola.com trc.taboola.com pixel.quantserve.com
""".split())

# domains that must never be blocked outright, even if a downloaded list contains them
NEVER_BLOCK = frozenset("""
google.com gstatic.com googleapis.com googleusercontent.com youtube.com ytimg.com googlevideo.com github.com
githubusercontent.com cloudflare.com jsdelivr.net unpkg.com facebook.com fbcdn.net instagram.com cdninstagram.com
tiktok.com tiktokcdn.com twitter.com twimg.com x.com reddit.com redd.it redditstatic.com redditmedia.com
discord.com discordapp.com discord.gg twitch.tv ttvnw.net snapchat.com pinterest.com pinimg.com linkedin.com
licdn.com whatsapp.com whatsapp.net microsoft.com live.com amazon.com apple.com wikipedia.org wikimedia.org
duckduckgo.com bing.com
""".split())

AD_LIST_URLS = ("https://easylist.to/easylist/easylist.txt", "https://easylist.to/easylist/easyprivacy.txt",
                "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=0&mimetype=plaintext")

# hides leftover ad boxes the network blocker can't remove (empty ad frames, placeholders)
AD_JS = r"""(function(){var A=__ALLOW__,h=location.hostname.replace(/^www\./,'');
if(A.some(function(a){return h===a||h.endsWith('.'+a)}))return;
var css='ins.adsbygoogle,.adsbygoogle,div[id^="google_ads_iframe"],iframe[id^="google_ads_iframe"],div[id^="div-gpt-ad"],'
+'iframe[src*="doubleclick.net"],iframe[src*="googlesyndication.com"],iframe[src*="adnxs.com"],[id^="taboola-"],'
+'[class*="taboola-"],.OUTBRAIN,[data-ad-slot],[data-google-query-id],.ad-banner,.ad-slot,.advert,.advertisement,'
+'.adsbox,.ad-container,#ad-banner,#adBanner{display:none!important}';
var t=setInterval(function(){if(document.documentElement){clearInterval(t);var s=document.createElement('style');
s.textContent=css;(document.head||document.documentElement).appendChild(s)}},5)})();"""

_DOM_RULE = re.compile(r"^\|\|([a-z0-9][a-z0-9.-]*\.[a-z]{2,})\^(?:\$(?:third-party|3p))?$")
_HOSTS_RULE = re.compile(r"^(?:127\.0\.0\.1|0\.0\.0\.0)\s+([a-z0-9][a-z0-9.-]*\.[a-z]{2,})\s*$")


def parse_filter_list(text):
    """Keep only whole-domain rules (EasyList '||domain^' and hosts-file lines)."""
    out = set()
    for line in text.splitlines():
        line = line.strip().lower()
        if not line or line[0] in "!#[@":
            continue
        m = _DOM_RULE.match(line) or _HOSTS_RULE.match(line)
        if m and m.group(1) != "localhost":
            out.add(m.group(1))
    return out


def download_lists(win):
    doms, ok = set(), 0
    for url in AD_LIST_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CDG-Browse"})
            with urllib.request.urlopen(req, timeout=30) as r:
                doms |= parse_filter_list(r.read().decode("utf-8", "replace"))
            ok += 1
        except Exception:
            pass
    win.adlistEvent.emit({"domains": sorted(doms)[:150000], "ok": ok})


class AdBlocker(QWebEngineUrlRequestInterceptor):
    """Blocks requests to known ad/tracker domains (runs on Chromium's network thread)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled, self.allow, self.n = True, frozenset(), 0
        self.domains = BUILTIN_AD_DOMAINS

    def load_saved(self):
        try:
            extra = set((DIR / "adblock_domains.txt").read_text().split()) - NEVER_BLOCK
            self.domains = frozenset(BUILTIN_AD_DOMAINS | extra)
        except Exception:
            pass

    def match(self, host):
        parts = host.split(".")
        d = self.domains
        for i in range(len(parts) - 1):
            if ".".join(parts[i:]) in d:
                return True
        return False

    def interceptRequest(self, info):
        if not self.enabled:
            return
        try:
            host = info.requestUrl().host().lower()
            if not host or info.resourceType() == QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame:
                return
            fp = info.firstPartyUrl().host().lower()
            fp = fp[4:] if fp.startswith("www.") else fp
            if fp:
                if self.allow and any(fp == a or fp.endswith("." + a) for a in self.allow):
                    return
                if host == fp or host.endswith("." + fp) or fp.endswith("." + host):
                    return  # same site: leave first-party requests alone
            if self.match(host):
                info.block(True)
                self.n += 1
        except Exception:
            pass


# ------------------------------------------------------------------ helpers
def load_data():
    D.clear()
    D.update(json.loads(json.dumps(DEFAULTS)))
    try:
        D.update(json.loads(data_path().read_text()))
    except Exception:
        pass
    if D["theme"] not in THEMES:
        D["theme"] = "Neon Night"
    if not D["spaces"]:
        D["spaces"] = [{"name": "Home", "theme": D["theme"]}]
    D["space"] = max(0, min(int(D["space"]), len(D["spaces"]) - 1))
    D["spaces"][D["space"]]["theme"] = D["theme"]
    for sp in D["spaces"]:
        if sp.get("theme") not in THEMES:
            sp["theme"] = "Neon Night"
    D["tb_order"] = [k for k in D["tb_order"] if k in DEFAULT_ORDER] + [k for k in DEFAULT_ORDER if k not in D["tb_order"]]
    D["tiles"] = [t for t in D["tiles"] if isinstance(t, dict) and t.get("url")] if isinstance(D["tiles"], list) else [dict(t) for t in DEFAULT_TILES]
    if not D.get("chat_tile"):
        D["chat_tile"] = True
        if not any(t["url"].startswith("https://cdg.start/chat") for t in D["tiles"]):
            D["tiles"].append({"name": "CDG Chat", "url": "https://cdg.start/chat", "color": "#b46bff"})
    for k in ("history", "searches", "adblock_allow"):
        if not isinstance(D.get(k), list):
            D[k] = []
    try:
        D["win_radius"] = max(0, min(40, int(D["win_radius"])))
    except Exception:
        D["win_radius"] = 22
    if D["toolbar"] not in ("top", "bottom"): D["toolbar"] = "top"
    if D["tabpos"] not in ("top", "side"): D["tabpos"] = "top"
    if D["density"] not in ("compact", "cozy", "roomy"): D["density"] = "cozy"


def save():
    try:
        data_path().write_text(json.dumps(D))
    except Exception:
        pass


def mix(a, b, t):
    return QColor(int(a.red() + (b.red() - a.red()) * t), int(a.green() + (b.green() - a.green()) * t),
                  int(a.blue() + (b.blue() - a.blue()) * t))


def alpha(c, a):
    x = QColor(c)
    x.setAlpha(max(0, min(255, int(a))))
    return x


def grad(x1, y1, x2, y2, c1, c2):
    g = QLinearGradient(x1, y1, x2, y2)
    g.setColorAt(0, c1)
    g.setColorAt(1, c2)
    return g


def F(px, weight=QFont.Weight.Medium):
    f = QFont()
    f.setPixelSize(px)
    f.setWeight(weight)
    return f


def rgba(c, a):
    return f"rgba({c.red()},{c.green()},{c.blue()},{int(a)})"


def refresh_pal():
    th = THEMES[D["theme"]]
    bg, bg2, text = QColor(th["bg"]), QColor(th["bg2"]), QColor(th["text"])
    acc = QColor(D["accent"]) if D["accent"] else QColor(th["accent"])
    if D["rainbow"] and "rainbow_accent" in D["owned"]:
        acc = QColor.fromHsv(int(RAINBOW_H) % 360, 190, 255)
    h = max(acc.hue(), 0)
    acc2 = QColor.fromHsv((h + 45) % 360, min(acc.saturation(), 210), 255)
    P.update({
        "bg": bg, "bg2": bg2, "text": text, "acc": acc, "acc2": acc2,
        "muted": mix(text, bg, 0.45),
        "onacc": QColor("#0b0916") if acc.lightnessF() > 0.55 else QColor("#ffffff"),
        "dark": bg.lightnessF() < 0.5,
    })


def corner(h):
    return h / 2 if D["pill"] else min(float(D["radius"]), h / 2)


def qss():
    t, acc, R = P["text"], P["acc"], D["radius"]
    cardbg = rgba(QColor("#ffffff"), 16) if P["dark"] else rgba(QColor("#ffffff"), 170)
    return f"""
    QLabel {{ color: {t.name()}; background: transparent; font-size: 13px; }}
    QLabel#h1 {{ font-size: 30px; font-weight: 700; color: {t.name()}; }}
    QLabel#h2 {{ font-size: 17px; font-weight: 700; color: {acc.name()}; }}
    QLabel#h3 {{ font-size: 15px; font-weight: 700; }}
    QLabel#muted {{ color: {P['muted'].name()}; font-size: 12px; }}
    QFrame#card {{ background: {cardbg}; border: 1px solid {rgba(t, 38)}; border-radius: {R + 6}px; }}
    QLineEdit#bare {{ background: transparent; border: none; color: {t.name()}; font-size: 14px;
        selection-background-color: {acc.name()}; selection-color: {P['onacc'].name()}; placeholder-text-color: {P['muted'].name()}; }}
    QLineEdit#input {{ background: {rgba(t, 16)}; border: 1px solid {rgba(t, 45)}; border-radius: {R}px; padding: 9px 14px;
        color: {t.name()}; font-size: 14px; selection-background-color: {acc.name()}; placeholder-text-color: {P['muted'].name()}; }}
    QLineEdit#input:focus {{ border: 2px solid {acc.name()}; }}
    QPlainTextEdit {{ background: {rgba(t, 12)}; border: 1px solid {rgba(t, 40)}; border-radius: {R}px; color: {t.name()};
        padding: 8px; font-family: Menlo, Consolas, monospace; font-size: 12px; }}
    QScrollArea {{ background: transparent; border: none; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {rgba(t, 80)}; border-radius: 4px; min-height: 30px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    """


# ------------------------------------------------------------------ icons
def draw_icon(p, kind, rect, col):
    cx, cy = rect.width() / 2, rect.height() / 2
    u = rect.width() * 0.17
    p.setPen(QPen(col, 1.9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    pts = lambda *a: QPolygonF([QPointF(x, y) for x, y in a])
    if kind == "back":
        p.drawPolyline(pts((cx + .6 * u, cy - 1.6 * u), (cx - .9 * u, cy), (cx + .6 * u, cy + 1.6 * u)))
    elif kind == "forward":
        p.drawPolyline(pts((cx - .6 * u, cy - 1.6 * u), (cx + .9 * u, cy), (cx - .6 * u, cy + 1.6 * u)))
    elif kind == "reload":
        r = 1.55 * u
        p.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r), 90 * 16, 280 * 16)  # open circle, gap at top-right
        # clockwise arrowhead at the top end of the arc, pointing right into the gap
        px, py, w = cx, cy - r, .75 * u
        p.setBrush(col)
        p.drawPolygon(pts((px + .8 * u, py), (px - .5 * u, py - w), (px - .5 * u, py + w)))
        p.setBrush(Qt.BrushStyle.NoBrush)
    elif kind == "home":
        p.drawPolyline(pts((cx - 1.9 * u, cy - .1 * u), (cx, cy - 1.8 * u), (cx + 1.9 * u, cy - .1 * u)))
        p.drawPolyline(pts((cx - 1.3 * u, cy - .3 * u), (cx - 1.3 * u, cy + 1.6 * u),
                           (cx + 1.3 * u, cy + 1.6 * u), (cx + 1.3 * u, cy - .3 * u)))
    elif kind == "settings":
        p.drawLine(QPointF(cx - 1.8 * u, cy - u), QPointF(cx + 1.8 * u, cy - u))
        p.drawLine(QPointF(cx - 1.8 * u, cy + u), QPointF(cx + 1.8 * u, cy + u))
        p.setBrush(P["bg"])
        p.drawEllipse(QPointF(cx - .6 * u, cy - u), .65 * u, .65 * u)
        p.drawEllipse(QPointF(cx + .7 * u, cy + u), .65 * u, .65 * u)
    elif kind == "shop":
        p.drawRoundedRect(QRectF(cx - 1.6 * u, cy - .6 * u, 3.2 * u, 2.4 * u), .5 * u, .5 * u)
        p.drawArc(QRectF(cx - .85 * u, cy - 1.8 * u, 1.7 * u, 2.0 * u), 0, 180 * 16)
    elif kind == "build":
        p.drawRoundedRect(QRectF(cx - 1.7 * u, cy - 1.7 * u, 3.4 * u, 3.4 * u), .5 * u, .5 * u)
        p.drawLine(QPointF(cx - .3 * u, cy - 1.7 * u), QPointF(cx - .3 * u, cy + 1.7 * u))
        p.drawLine(QPointF(cx - .3 * u, cy + .2 * u), QPointF(cx + 1.7 * u, cy + .2 * u))
    elif kind == "plus":
        p.drawLine(QPointF(cx - 1.2 * u, cy), QPointF(cx + 1.2 * u, cy))
        p.drawLine(QPointF(cx, cy - 1.2 * u), QPointF(cx, cy + 1.2 * u))
    elif kind == "close":
        p.drawLine(QPointF(cx - u, cy - u), QPointF(cx + u, cy + u))
        p.drawLine(QPointF(cx + u, cy - u), QPointF(cx - u, cy + u))


# ------------------------------------------------------------------ custom widgets
class Hover(QWidget):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.h = 0.0
        self.pr = 0.0
        self._an = QVariantAnimation(self)
        self._an.setDuration(180)
        self._an.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._an.valueChanged.connect(self._hv)
        self._pa = QVariantAnimation(self)
        self._pa.valueChanged.connect(self._pv)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _pv(self, v):
        self.pr = float(v)
        self.update()

    def _press_anim(self, down):
        # squish on press, springy overshoot on release
        self._pa.stop()
        self._pa.setStartValue(float(self.pr))
        self._pa.setEndValue(1.0 if down else 0.0)
        self._pa.setDuration(90 if down else 380)
        self._pa.setEasingCurve(QEasingCurve.Type.OutCubic if down else QEasingCurve.Type.OutBack)
        self._pa.start()

    def _mk(self):
        """Painter with antialiasing and the press-squish scale applied."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if abs(self.pr) > 0.001:
            w, h = max(1, self.width()), max(1, self.height())
            pr = max(-0.4, min(1.0, self.pr))
            p.translate(w / 2, h / 2)
            p.scale(1 - 6 * pr / w, 1 - 6 * pr / h)
            p.translate(-w / 2, -h / 2)
        return p

    def _hv(self, v):
        self.h = float(v)
        self.update()

    def _go(self, t):
        self._an.stop()
        self._an.setStartValue(float(self.h))
        self._an.setEndValue(float(t))
        self._an.start()

    def enterEvent(self, e):
        self._go(1.0)

    def leaveEvent(self, e):
        self._go(0.0)
        if self.pr > 0:
            self._press_anim(False)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.RightButton:
            e.ignore()
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self._press_anim(True)
        e.accept()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._press_anim(False)
            if self.rect().contains(e.position().toPoint()):
                self.activate(e)

    def activate(self, e):
        self.clicked.emit()


class IconButton(Hover):
    def __init__(self, kind, size=36):
        super().__init__()
        self.kind = kind
        self.setFixedSize(size, size)

    def paintEvent(self, e):
        p = self._mk()
        if self.h > 0:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(alpha(P["text"], 30 * self.h))
            p.drawEllipse(QRectF(self.rect()).adjusted(2, 2, -2, -2))
        draw_icon(p, self.kind, self.rect(), mix(P["muted"], P["text"], self.h))


class Dot(Hover):
    def __init__(self, color):
        super().__init__()
        self.color = QColor(color)
        self.setFixedSize(16, 16)

    def paintEvent(self, e):
        p = self._mk()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(mix(self.color, QColor("#ffffff"), .25 * self.h))
        p.drawEllipse(QRectF(self.rect()).adjusted(2, 2, -2, -2))


class PillButton(Hover):
    def __init__(self, text, primary=False, height=34):
        super().__init__()
        self.text, self.primary, self.off = text, primary, False
        self.setFixedHeight(height)
        self._fit()

    def _fit(self):
        self.setFixedWidth(QFontMetrics(F(13, QFont.Weight.DemiBold)).horizontalAdvance(self.text) + 34)

    def set_text(self, t):
        self.text = t
        self._fit()
        self.update()

    def set_off(self, off):
        self.off = off
        self.setCursor(Qt.CursorShape.ArrowCursor if off else Qt.CursorShape.PointingHandCursor)
        self.update()

    def activate(self, e):
        if not self.off:
            self.clicked.emit()

    def paintEvent(self, e):
        p = self._mk()
        r = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        rr = corner(r.height()) if not D["pill"] else r.height() / 2
        if self.off:
            p.setOpacity(.45)
        if self.primary:
            w = QColor("#ffffff")
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad(0, 0, r.width(), 0, mix(P["acc"], w, .18 * self.h), mix(P["acc2"], w, .18 * self.h))))
            tc = P["onacc"]
        else:
            p.setPen(QPen(alpha(P["text"], 45 + 70 * self.h), 1))
            p.setBrush(alpha(P["text"], 14 + 22 * self.h))
            tc = P["text"]
        p.drawRoundedRect(r, rr, rr)
        p.setPen(tc)
        p.setFont(F(13, QFont.Weight.DemiBold))
        p.drawText(r, AL_C, self.text)


class Chip(Hover):
    def __init__(self, text, selected=False, dot=None, locked=False):
        super().__init__()
        self.text, self.sel, self.dot, self.locked = text, selected, dot, locked
        self.setFixedHeight(32)
        self.setFixedWidth(QFontMetrics(F(13)).horizontalAdvance(text) + 32 + (16 if dot else 0))

    def set_text(self, text, dot=None):
        self.text, self.dot = text, dot
        self.setFixedWidth(QFontMetrics(F(13)).horizontalAdvance(text) + 32 + (16 if dot else 0))
        self.update()

    def paintEvent(self, e):
        p = self._mk()
        r = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        rr = r.height() / 2
        if self.locked:
            p.setOpacity(.55)
        if self.sel:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad(0, 0, r.width(), 0, P["acc"], P["acc2"])))
            tc = P["onacc"]
        else:
            p.setPen(QPen(alpha(P["text"], 40 + 60 * self.h), 1))
            p.setBrush(alpha(P["text"], 10 + 18 * self.h))
            tc = P["text"]
        p.drawRoundedRect(r, rr, rr)
        x = 16
        if self.dot:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self.dot)
            p.drawEllipse(QPointF(18, r.height() / 2), 5, 5)
            x = 32
        p.setPen(tc)
        p.setFont(F(13))
        p.drawText(QRectF(x, 0, r.width() - x, r.height()), AL_L, self.text)


class Swatch(Hover):
    def __init__(self, color, selected):
        super().__init__()
        self.color, self.sel = QColor(color), selected
        self.setFixedSize(30, 30)

    def paintEvent(self, e):
        p = self._mk()
        r = QRectF(self.rect())
        if self.sel or self.h > 0:
            p.setPen(QPen(alpha(P["text"], 255 if self.sel else 150), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(r.adjusted(2, 2, -2, -2))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.color)
        p.drawEllipse(r.adjusted(6, 6, -6, -6))


class Toggle(Hover):
    toggled = pyqtSignal(bool)

    def __init__(self, on=False):
        super().__init__()
        self.on, self.k = on, (1.0 if on else 0.0)
        self.setFixedSize(48, 28)
        self._ka = QVariantAnimation(self)
        self._ka.setDuration(320)
        self._ka.setEasingCurve(QEasingCurve.Type.OutBack)
        self._ka.valueChanged.connect(self._kv)

    def _kv(self, v):
        self.k = float(v)
        self.update()

    def activate(self, e):
        self.on = not self.on
        self._ka.stop()
        self._ka.setStartValue(float(self.k))
        self._ka.setEndValue(1.0 if self.on else 0.0)
        self._ka.start()
        self.toggled.emit(self.on)

    def paintEvent(self, e):
        p = self._mk()
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setPen(Qt.PenStyle.NoPen)
        off = alpha(P["text"], 40 + 20 * self.h)
        kc = max(0.0, min(1.0, self.k))
        p.setBrush(QBrush(grad(0, 0, r.width(), 0, mix(off, P["acc"], kc), mix(off, P["acc2"], kc))))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        d = r.height() - 6
        x = 4 + self.k * (r.width() - d - 6)
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(QRectF(x, 4, d, d))


class Slider(Hover):
    changed = pyqtSignal(int)

    def __init__(self, lo, hi, val, rainbow=False):
        super().__init__()
        self.lo, self.hi, self.v, self.rb = lo, hi, val, rainbow
        self.setFixedHeight(28)
        self.setMinimumWidth(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _set(self, x):
        t = max(0.0, min(1.0, (x - 11) / max(1, self.width() - 22)))
        self.v = int(round(self.lo + (self.hi - self.lo) * t))
        self.update()
        self.changed.emit(self.v)

    def mousePressEvent(self, e):
        e.accept()
        self._set(e.position().x())

    def mouseMoveEvent(self, e):
        if bool(e.buttons() & Qt.MouseButton.LeftButton):
            self._set(e.position().x())

    def mouseReleaseEvent(self, e):
        pass

    def paintEvent(self, e):
        p = self._mk()
        w, h = self.width(), self.height()
        track = QRectF(11, h / 2 - 3, w - 22, 6)
        p.setPen(Qt.PenStyle.NoPen)
        t = (self.v - self.lo) / max(1, (self.hi - self.lo))
        if self.rb:
            g = QLinearGradient(11, 0, w - 11, 0)
            for i in range(7):
                g.setColorAt(i / 6, QColor.fromHsv(min(359, i * 60), 200, 255))
            p.setBrush(QBrush(g))
            p.drawRoundedRect(track, 3, 3)
        else:
            p.setBrush(alpha(P["text"], 40))
            p.drawRoundedRect(track, 3, 3)
            p.setBrush(QBrush(grad(11, 0, w - 11, 0, P["acc"], P["acc2"])))
            p.drawRoundedRect(QRectF(track.x(), track.y(), track.width() * t, 6), 3, 3)
        kx = 11 + t * (w - 22)
        p.setPen(QPen(P["acc"], 2.5))
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(QPointF(kx, h / 2), 9 + 1.5 * self.h, 9 + 1.5 * self.h)


class TabChip(Hover):
    closeRequested = pyqtSignal()
    contextRequested = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.title, self.sel, self.ch = "New Tab", False, False
        self.icon_pm = None
        self.setFixedHeight(34)
        self.setMinimumWidth(100)
        self.setMaximumWidth(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.RightButton:
            self.contextRequested.emit(e.globalPosition().toPoint())
        elif e.button() == Qt.MouseButton.MiddleButton:
            self.closeRequested.emit()
        elif e.button() == Qt.MouseButton.LeftButton:
            self._press_anim(True)
        e.accept()

    def set_icon(self, icon):
        pm = None
        if icon is not None and not icon.isNull():
            pm = icon.pixmap(QSize(32, 32))
            if pm.isNull():
                pm = None
        self.icon_pm = pm
        self.update()

    def compact(self):
        return self.width() < 80

    def close_rect(self):
        if self.compact():
            return QRectF()
        return QRectF(self.width() - 28, (self.height() - 20) / 2, 20, 20)

    def mouseMoveEvent(self, e):
        v = self.close_rect().contains(e.position())
        if v != self.ch:
            self.ch = v
            self.update()

    def activate(self, e):
        if self.close_rect().contains(e.position()):
            self.closeRequested.emit()
        else:
            self.clicked.emit()

    def paintEvent(self, e):
        p = self._mk()
        r = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        rr = corner(r.height()) if not D["pill"] else r.height() / 2
        if self.sel:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad(0, 0, r.width(), 0, P["acc"], P["acc2"])))
            tc = P["onacc"]
        else:
            p.setPen(QPen(alpha(P["text"], 22 + 30 * self.h), 1))
            p.setBrush(alpha(P["text"], 8 + 16 * self.h))
            tc = P["text"]
        p.drawRoundedRect(r, rr, rr)
        p.setPen(Qt.PenStyle.NoPen)
        if self.icon_pm is not None:
            ir = QRectF((r.width() - 16) / 2 if self.compact() else 8, r.height() / 2 - 8, 16, 16)
            p.save()
            clip = QPainterPath()
            clip.addRoundedRect(ir, 4, 4)
            p.setClipPath(clip)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            p.drawPixmap(ir, self.icon_pm, QRectF(self.icon_pm.rect()))
            p.restore()
        else:
            p.setBrush(alpha(tc, 200))
            p.drawEllipse(QPointF(r.width() / 2 if self.compact() else 16, r.height() / 2), 3.5, 3.5)
        want = self.title if self.compact() else ""
        if self.toolTip() != want:
            self.setToolTip(want)
        if self.compact():
            return
        fm = QFontMetrics(F(13))
        p.setFont(F(13))
        p.setPen(tc)
        p.drawText(QRectF(28, 0, r.width() - 60, r.height()), AL_L,
                   fm.elidedText(self.title, Qt.TextElideMode.ElideRight, int(r.width() - 60)))
        if self.sel or self.h > 0.2:
            cr = self.close_rect()
            if self.ch:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(alpha(tc, 50))
                p.drawEllipse(cr)
            p.save()
            p.translate(cr.x(), cr.y())
            draw_icon(p, "close", QRectF(0, 0, 20, 20).toRect(), tc)
            p.restore()


class CoinChip(Hover):
    def __init__(self):
        super().__init__()
        self.coins = 0
        self.setFixedHeight(34)
        self.set_coins(0)

    def set_coins(self, n):
        self.coins = n
        self.setFixedWidth(QFontMetrics(F(13, QFont.Weight.Bold)).horizontalAdvance(str(n)) + 58)
        self.update()

    def paintEvent(self, e):
        p = self._mk()
        r = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        p.setPen(QPen(alpha(QColor("#ffc857"), 90 + 100 * self.h), 1))
        p.setBrush(alpha(QColor("#ffc857"), 26 + 30 * self.h))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad(0, 0, 0, r.height(), QColor("#ffe08a"), QColor("#ff9f1c"))))
        cr = QRectF(8, r.height() / 2 - 9, 18, 18)
        p.drawEllipse(cr)
        p.setPen(QColor("#7a4a00"))
        p.setFont(F(11, QFont.Weight.Bold))
        p.drawText(cr, AL_C, "C")
        p.setPen(P["text"])
        p.setFont(F(13, QFont.Weight.Bold))
        p.drawText(QRectF(32, 0, r.width() - 32, r.height()), AL_L, str(self.coins))


class AddressBar(QWidget):
    engineClicked = pyqtSignal()
    siteChosen = pyqtSignal(str)
    searchChosen = pyqtSignal(str)
    ICON_W = 54

    def __init__(self):
        super().__init__()
        self.setFixedHeight(40)
        self.ih = 0.0
        self._over = False
        self.pop, self.provider = None, None
        self.setMouseTracking(True)
        self._ian = QVariantAnimation(self)
        self._ian.setDuration(160)
        self._ian.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._ian.valueChanged.connect(self._iv)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(self.ICON_W, 0, 16, 0)
        self.edit = QLineEdit()
        self.edit.setObjectName("bare")
        self.edit.setPlaceholderText("Search or type a web address")
        self.edit.installEventFilter(self)
        self.edit.textEdited.connect(self._typed)
        lay.addWidget(self.edit)

    def eventFilter(self, o, e):
        t = e.type()
        if o is self.edit:
            if t == QEvent.Type.FocusIn:
                self.update()
            elif t == QEvent.Type.FocusOut:
                self.update()
                self._dismiss()
            elif t == QEvent.Type.KeyPress and self._pop_visible():
                k = e.key()
                if k == Qt.Key.Key_Down:
                    self.pop.move_sel(1)
                    return True
                if k == Qt.Key.Key_Up:
                    self.pop.move_sel(-1)
                    return True
                if k == Qt.Key.Key_Escape:
                    self._dismiss()
                    return True
                if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.pop.current() is not None:
                    r = self.pop.current()
                    self._picked(r["k"], r["val"])
                    return True
        return False

    # ---- live suggestions (recent sites, recent searches, recommended)
    def _pop_visible(self):
        return self.pop is not None and self.pop.isVisible() and not self.pop._out

    def _dismiss(self):
        if self.pop is not None:
            self.pop.dismiss()

    def _typed(self, text):
        if not text.strip() or self.provider is None:
            self._dismiss()
            return
        rows = self.provider(text)
        if not rows:
            self._dismiss()
            return
        if self.pop is None:
            self.pop = SuggestPopup(self.window())
            self.pop.picked.connect(self._picked)
        self.pop.set_rows(rows)
        self.pop.present(QRect(self.mapToGlobal(QPoint(0, 0)), self.size()), D["toolbar"] == "bottom")

    def _picked(self, kind, val):
        self._dismiss()
        (self.siteChosen if kind == "site" else self.searchChosen).emit(val)

    def set_engine_name(self, name):
        self.edit.setPlaceholderText(f"Search {name} or type a web address")

    def _iv(self, v):
        self.ih = float(v)
        self.update()

    def _icon_hot(self, x):
        return x < self.ICON_W - 6

    def _set_over(self, on):
        if on != self._over:
            self._over = on
            self._ian.stop()
            self._ian.setStartValue(float(self.ih))
            self._ian.setEndValue(1.0 if on else 0.0)
            self._ian.start()
            self.setCursor(Qt.CursorShape.PointingHandCursor if on else Qt.CursorShape.ArrowCursor)

    def mouseMoveEvent(self, e):
        self._set_over(self._icon_hot(e.position().x()))

    def leaveEvent(self, e):
        self._set_over(False)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._icon_hot(e.position().x()):
            self.engineClicked.emit()
            e.accept()
        else:
            super().mousePressEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        focus = self.edit.hasFocus()
        p.setBrush(alpha(P["text"], 16 if not focus else 24))
        p.setPen(QPen(P["acc"] if focus else alpha(P["text"], 45), 2 if focus else 1))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        c = mix(P["acc"] if focus else P["muted"], P["text"], .5 * self.ih)
        cy = self.height() / 2
        if self.ih > 0:
            # soft hover pill behind the search icon + chevron
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(alpha(P["text"], 26 * self.ih))
            hr = QRectF(6, 6, self.ICON_W - 12, self.height() - 12)
            p.drawRoundedRect(hr, hr.height() / 2, hr.height() / 2)
        p.setPen(QPen(c, 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(21, cy - 1.5), 5.6, 5.6)          # magnifier lens
        p.drawLine(QPointF(25.2, cy + 2.7), QPointF(29.5, cy + 7))  # handle
        p.setPen(QPen(c, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawPolyline(QPolygonF([QPointF(38, cy - 1.2), QPointF(41, cy + 1.8), QPointF(44, cy - 1.2)]))  # chevron


class Toast(QWidget):
    """Notification pill that slides open out of the toolbar (the address bar
    smoothly gives up the space), holds, then slides closed again."""
    SLIDE_IN = 750    # ms - slow, smooth open
    HOLD = 2600       # ms - how long it stays fully open
    SLIDE_OUT = 650   # ms - satisfying glide shut

    def __init__(self):
        super().__init__()
        self.text, self.full, self.p = "", 0, 0.0   # p: 0 = closed, 1 = fully open
        self.setFixedHeight(32)
        self.setFixedWidth(0)
        self.hide()
        self.anim = QVariantAnimation(self)
        self.anim.valueChanged.connect(self._on_anim)
        self.anim.finished.connect(self._on_anim_done)
        self.closing = False
        self.hold_t = QTimer(self)
        self.hold_t.setSingleShot(True)
        self.hold_t.timeout.connect(self.slide_out)

    def _animate(self, to, ms, curve):
        self.anim.stop()
        self.anim.setStartValue(float(self.p))
        self.anim.setEndValue(float(to))
        self.anim.setDuration(max(1, int(ms * abs(to - self.p))))
        self.anim.setEasingCurve(curve)
        self.anim.start()

    def show_msg(self, text):
        self.hold_t.stop()
        self.closing = False
        self.text = text
        self.full = QFontMetrics(F(13, QFont.Weight.DemiBold)).horizontalAdvance(text) + 36
        if not self.isVisible():
            self.p = 0.0
            self.setFixedWidth(1)
            self.show()
        # new message while one is showing: just glide to the new width
        self._animate(1.0, self.SLIDE_IN, QEasingCurve.Type.OutCubic)
        self.update()

    def slide_out(self):
        self.closing = True
        self._animate(0.0, self.SLIDE_OUT, QEasingCurve.Type.InOutCubic)

    def _on_anim(self, v):
        self.p = float(v)
        self.setFixedWidth(max(1, int(round(self.full * self.p))))
        self.update()

    def _on_anim_done(self):
        if self.closing:
            self.closing = False
            self.p = 0.0
            self.hide()
            self.setFixedWidth(0)
        else:
            self.hold_t.start(self.HOLD)

    def paintEvent(self, e):
        if self.p <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad(0, 0, max(1.0, r.width()), 0, P["acc"], P["acc2"])))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        # text is revealed as the pill opens: fades in over the back half of the slide
        t_op = max(0.0, min(1.0, (self.p - 0.45) / 0.55))
        if t_op > 0:
            clip = QPainterPath()
            clip.addRoundedRect(r, r.height() / 2, r.height() / 2)
            p.setClipPath(clip)
            p.setOpacity(t_op)
            p.setPen(P["onacc"])
            p.setFont(F(13, QFont.Weight.DemiBold))
            p.drawText(QRectF(0, 0, self.full, self.height()), AL_C, self.text)


class ThemePreview(QWidget):
    def __init__(self, name):
        super().__init__()
        self.th = THEMES[name]
        self.setFixedHeight(60)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad(0, 0, r.width(), r.height(), QColor(self.th["bg"]), QColor(self.th["bg2"]))))
        p.drawRoundedRect(r, 12, 12)
        a = QColor(self.th["accent"])
        p.setBrush(alpha(QColor(self.th["text"]), 50))
        p.drawRoundedRect(QRectF(12, 12, r.width() * .45, 10), 5, 5)
        p.setBrush(a)
        p.drawRoundedRect(QRectF(12, 34, 70, 14), 7, 7)
        p.drawEllipse(QPointF(r.width() - 26, r.height() / 2), 10, 10)


class ToolRow(QWidget):
    contextRequested = pyqtSignal(object)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.RightButton:
            self.contextRequested.emit(e.globalPosition().toPoint())

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        rr = r.height() / 2 if D["pill"] else min(D["radius"] + 6, r.height() / 2)
        if D["gradient"]:
            p.setBrush(QBrush(grad(0, 0, r.width(), 0, alpha(P["acc"], 110), alpha(P["acc2"], 30))))
        else:
            p.setBrush(alpha(P["text"], 12))
        p.setPen(QPen(alpha(P["text"], 34), 1))
        p.drawRoundedRect(r, rr, rr)


# ------------------------------------------------------------------ custom context menu
def MI(label, fn, on=True, hint=""):
    return {"k": "item", "label": label, "fn": fn, "on": on, "hint": hint}


SEP = {"k": "sep"}


def ICONS(*cells):
    """cells: (icon_kind, callback, enabled)"""
    return {"k": "icons", "cells": list(cells)}


class CtxMenu(QWidget):
    PAD = 24

    def __init__(self, items, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.a, self.hot, self.sub, self.t0 = 0.0, -1, -1, time.time()
        self._fading = False
        self._dead = False
        fm, fh = QFontMetrics(F(13)), QFontMetrics(F(12))
        lab = max([fm.horizontalAdvance(i["label"]) for i in items if i["k"] == "item"] or [0])
        hint = max([fh.horizontalAdvance(i["hint"]) for i in items if i["k"] == "item"] or [0])
        icons = max([len(i["cells"]) for i in items if i["k"] == "icons"] or [0])
        self.w = max(200, 12 + 28 + lab + (hint + 28 if hint else 0), icons * 46 + 12)
        y, self.rows = 6, []
        for it in items:
            h = {"item": 32, "sep": 9, "icons": 40}[it["k"]]
            self.rows.append((it, y, h))
            y += h
        self.h = y + 6
        self.resize(self.w + 2 * self.PAD, self.h + 2 * self.PAD)
        self._an = QVariantAnimation(self)
        self._an.setDuration(190)
        self._an.setStartValue(0.0)
        self._an.setEndValue(1.0)
        self._an.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._an.valueChanged.connect(self._av)
        self._an.finished.connect(self._anim_done)

    def _av(self, v):
        self.a = float(v)
        self.update()

    def _anim_done(self):
        if self._fading:
            self._dead = True
            self.close()

    # ---- fade-out: clicking away (or Esc) fades the menu instead of snapping shut
    def closeEvent(self, e):
        if self._dead:
            e.accept()
            return
        e.ignore()
        self.fade_out()

    def fade_out(self, ms=170):
        if self._fading:
            return
        self._fading = True
        self.hot = self.sub = -1
        self._an.stop()
        self._an.setEasingCurve(QEasingCurve.Type.InCubic)
        self._an.setDuration(ms)
        self._an.setStartValue(float(self.a))
        self._an.setEndValue(0.0)
        self._an.start()

    def close_now(self):
        self._dead = True
        self._an.stop()
        self.close()

    def popup(self, gpos):
        scr = QApplication.screenAt(gpos) or QApplication.primaryScreen()
        g = scr.availableGeometry()
        ix, iy = gpos.x() + 2, gpos.y() + 2
        if ix + self.w > g.right():
            ix = max(g.left(), gpos.x() - self.w - 2)
        if iy + self.h > g.bottom():
            iy = max(g.top(), gpos.y() - self.h - 2)
        self.move(ix - self.PAD, iy - self.PAD)
        self.show()
        self._an.start()
        self.setFocus()

    # ---- hit testing / input
    def hit(self, pos):
        x, y = pos.x() - self.PAD, pos.y() - self.PAD
        for i, (it, ry, h) in enumerate(self.rows):
            if not (ry <= y < ry + h):
                continue
            if it["k"] == "item" and it["on"]:
                return i, -1
            if it["k"] == "icons" and 6 <= x < self.w - 6:
                n = len(it["cells"])
                k = int((x - 6) // ((self.w - 12) / n))
                if 0 <= k < n and it["cells"][k][2]:
                    return i, k
        return -1, -1

    def mouseMoveEvent(self, e):
        if self._fading:
            return
        self.hot, self.sub = self.hit(e.position())
        self.setCursor(Qt.CursorShape.PointingHandCursor if self.hot >= 0 else Qt.CursorShape.ArrowCursor)
        self.update()

    def leaveEvent(self, e):
        self.hot = self.sub = -1
        self.update()

    def mousePressEvent(self, e):
        e.accept()

    def mouseReleaseEvent(self, e):
        if self._fading or e.button() != Qt.MouseButton.LeftButton or time.time() - self.t0 < 0.25:
            return
        i, k = self.hit(e.position())
        if i >= 0:
            self.fire(i, k)

    def fire(self, i, k=-1):
        it = self.rows[i][0]
        fn = it["fn"] if it["k"] == "item" else it["cells"][k][1]
        self.fade_out(110)
        QTimer.singleShot(10, fn)

    def keyPressEvent(self, e):
        if self._fading:
            return
        k = e.key()
        sel = [i for i, (it, _, _) in enumerate(self.rows) if it["k"] == "item" and it["on"]]
        if k == Qt.Key.Key_Escape:
            self.close()
        elif k in (Qt.Key.Key_Down, Qt.Key.Key_Up) and sel:
            if self.hot not in sel:
                self.hot = sel[0] if k == Qt.Key.Key_Down else sel[-1]
            else:
                self.hot = sel[(sel.index(self.hot) + (1 if k == Qt.Key.Key_Down else -1)) % len(sel)]
            self.sub = -1
            self.update()
        elif k in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.hot in sel:
            self.fire(self.hot)

    # ---- painting
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(self.a)
        sc = 0.95 + 0.05 * self.a
        mx = self.width() / 2
        p.translate(mx, self.PAD)
        p.scale(sc, sc)
        p.translate(-mx, -self.PAD)
        p.translate(0, (1 - self.a) * -6)
        inner = QRectF(self.PAD, self.PAD, self.w, self.h)
        R = float(max(6, 20 if D["pill"] else min(D["radius"] + 4, 22)))
        p.setPen(Qt.PenStyle.NoPen)
        sh = 220 if P["dark"] else 90
        for i in range(18):
            p.setBrush(QColor(0, 0, 0, max(1, int(sh / 18 * 0.5 * (1 - i / 18) ** 2))))
            p.drawRoundedRect(inner.adjusted(-i, -i, i, i).translated(0, 6), R + i, R + i)
        base = mix(P["bg2"], P["bg"], .35)
        p.setPen(QPen(alpha(P["text"], 55), 1))
        p.setBrush(QBrush(grad(0, inner.top(), 0, inner.bottom(), mix(base, P["text"], .09), base)))
        p.drawRoundedRect(inner.adjusted(.5, .5, -.5, -.5), R, R)
        # soft accent glow along the top edge + glassy inner highlight
        glow = QLinearGradient(inner.left(), 0, inner.right(), 0)
        glow.setColorAt(0, alpha(P["acc"], 0))
        glow.setColorAt(.5, alpha(P["acc"], 140))
        glow.setColorAt(1, alpha(P["acc2"], 0))
        p.setPen(QPen(QBrush(glow), 1.2))
        p.drawLine(QPointF(inner.left() + R * .8, inner.top() + .8), QPointF(inner.right() - R * .8, inner.top() + .8))
        p.setPen(QPen(alpha(QColor("#ffffff"), 22 if P["dark"] else 90), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(inner.adjusted(1.5, 1.5, -1.5, -1.5), R - 1, R - 1)
        for i, (it, ry, h) in enumerate(self.rows):
            top = inner.y() + ry
            if it["k"] == "sep":
                p.setPen(QPen(alpha(P["text"], 40), 1))
                p.drawLine(QPointF(inner.x() + 16, top + h / 2), QPointF(inner.right() - 16, top + h / 2))
            elif it["k"] == "item":
                r = QRectF(inner.x() + 6, top, self.w - 12, h)
                hot = i == self.hot
                tc = P["text"]
                if hot:
                    rr = corner(h)
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QBrush(grad(r.x(), 0, r.right(), 0, P["acc"], P["acc2"])))
                    p.drawRoundedRect(r, rr, rr)
                    tc = P["onacc"]
                p.setOpacity(self.a * (1.0 if it["on"] else .4))
                tr = QRectF(r.x() + 14, r.y(), r.width() - 28, h)
                p.setPen(tc)
                p.setFont(F(13))
                p.drawText(tr, AL_L, it["label"])
                if it["hint"]:
                    p.setFont(F(12))
                    p.setPen(alpha(tc, 190) if hot else P["muted"])
                    p.drawText(tr, AL_R, it["hint"])
                p.setOpacity(self.a)
            else:
                n = len(it["cells"])
                cw = (self.w - 12) / n
                for k, (kind, _fn, on) in enumerate(it["cells"]):
                    cx, cy = inner.x() + 6 + cw * (k + .5), top + h / 2
                    hot = i == self.hot and k == self.sub
                    col = P["text"]
                    if hot:
                        p.setPen(Qt.PenStyle.NoPen)
                        p.setBrush(QBrush(grad(cx - 17, cy - 17, cx + 17, cy + 17, P["acc"], P["acc2"])))
                        p.drawEllipse(QPointF(cx, cy), 17, 17)
                        col = P["onacc"]
                    p.setOpacity(self.a * (1.0 if on else .35))
                    p.save()
                    p.translate(cx - 18, cy - 18)
                    draw_icon(p, kind, QRectF(0, 0, 36, 36).toRect(), col)
                    p.restore()
                    p.setOpacity(self.a)


def popup_menu(items, gpos):
    """Show the custom context menu at a global position."""
    global _MENU
    clean = []
    for it in items:
        if it["k"] == "sep" and (not clean or clean[-1]["k"] == "sep"):
            continue
        clean.append(it)
    while clean and clean[-1]["k"] == "sep":
        clean.pop()
    if not clean:
        return
    try:
        if _MENU is not None:
            _MENU.close_now()
    except RuntimeError:
        pass
    _MENU = CtxMenu(clean, QApplication.activeWindow())
    _MENU.popup(gpos)


def text_menu(w, extra=None):
    """Context menu for QLineEdit / QPlainTextEdit."""
    if isinstance(w, QLineEdit):
        sel, has = w.hasSelectedText(), bool(w.text())
        undo, redo = w.isUndoAvailable(), w.isRedoAvailable()
    else:
        sel, has = w.textCursor().hasSelection(), bool(w.toPlainText())
        undo, redo = w.document().isUndoAvailable(), w.document().isRedoAvailable()
    ro = w.isReadOnly()
    items = []
    if not ro:
        items += [MI("Undo", w.undo, undo, MOD + "Z"),
                  MI("Redo", w.redo, redo, MOD + ("\u21e7Z" if IS_MAC else "Y")), SEP,
                  MI("Cut", w.cut, sel, MOD + "X")]
    items.append(MI("Copy", w.copy, sel, MOD + "C"))
    if not ro:
        items.append(MI("Paste", w.paste, bool(QApplication.clipboard().text()), MOD + "V"))
    items.append(MI("Select all", w.selectAll, has, MOD + "A"))
    if extra:
        items += [SEP] + extra
    popup_menu(items, QCursor.pos())


def attach_text_menu(w, extra_fn=None):
    w.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    w.customContextMenuRequested.connect(lambda _p, w=w: text_menu(w, extra_fn() if extra_fn else None))


FAV = {}  # host -> favicon pixmap (this session)


def paint_glass(p, inner, R):
    """Shared soft-shadow glass panel used by popups."""
    p.setPen(Qt.PenStyle.NoPen)
    sh = 220 if P["dark"] else 90
    for i in range(18):
        p.setBrush(QColor(0, 0, 0, max(1, int(sh / 18 * 0.5 * (1 - i / 18) ** 2))))
        p.drawRoundedRect(inner.adjusted(-i, -i, i, i).translated(0, 6), R + i, R + i)
    base = mix(P["bg2"], P["bg"], .35)
    p.setPen(QPen(alpha(P["text"], 55), 1))
    p.setBrush(QBrush(grad(0, inner.top(), 0, inner.bottom(), mix(base, P["text"], .09), base)))
    p.drawRoundedRect(inner.adjusted(.5, .5, -.5, -.5), R, R)
    glow = QLinearGradient(inner.left(), 0, inner.right(), 0)
    glow.setColorAt(0, alpha(P["acc"], 0))
    glow.setColorAt(.5, alpha(P["acc"], 140))
    glow.setColorAt(1, alpha(P["acc2"], 0))
    p.setPen(QPen(QBrush(glow), 1.2))
    p.drawLine(QPointF(inner.left() + R * .8, inner.top() + .8), QPointF(inner.right() - R * .8, inner.top() + .8))
    p.setPen(QPen(alpha(QColor("#ffffff"), 22 if P["dark"] else 90), 1))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(inner.adjusted(1.5, 1.5, -1.5, -1.5), R - 1, R - 1)


class SuggestPopup(QWidget):
    """Address-bar dropdown. Never takes keyboard focus, so typing keeps working."""
    PAD, HEAD, ROW = 22, 28, 38
    picked = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowDoesNotAcceptFocus
                         | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMouseTracking(True)
        self.rows, self.hot, self.a, self.w, self.h, self.above = [], -1, 0.0, 420, 60, False
        self._out = False
        self._an = QVariantAnimation(self)
        self._an.valueChanged.connect(self._av)
        self._an.finished.connect(self._fin)

    def _av(self, v):
        self.a = float(v)
        self.update()

    def _fin(self):
        if self._out:
            self._out = False
            self.hide()

    def _fade(self, to, ms, curve):
        self._an.stop()
        self._an.setStartValue(float(self.a))
        self._an.setEndValue(float(to))
        self._an.setDuration(ms)
        self._an.setEasingCurve(curve)
        self._an.start()

    def set_rows(self, rows):
        self.rows, y = [], 8
        for r in rows:
            h = self.HEAD if r["k"] == "head" else self.ROW
            self.rows.append((r, y, h))
            y += h
        self.h = y + 8
        self.hot = -1

    def present(self, anchor, above):
        self.w, self.above = max(360, anchor.width()), above
        self.resize(self.w + 2 * self.PAD, self.h + 2 * self.PAD)
        x = anchor.left() - self.PAD
        y = (anchor.top() - 6 - self.h - self.PAD) if above else (anchor.bottom() + 6 - self.PAD)
        g = (QApplication.screenAt(anchor.center()) or QApplication.primaryScreen()).availableGeometry()
        x = max(g.left() - self.PAD, min(x, g.right() - self.w - self.PAD))
        self.move(x, y)
        self._out = False
        if not self.isVisible():
            self.a = 0.0
            self.show()
        self._fade(1.0, 170, QEasingCurve.Type.OutCubic)
        self.update()

    def dismiss(self):
        if self.isVisible() and not self._out:
            self._out = True
            self._fade(0.0, 130, QEasingCurve.Type.InCubic)

    def move_sel(self, d):
        sel = [i for i, (r, _, _) in enumerate(self.rows) if r["k"] != "head"]
        if not sel:
            return
        if self.hot not in sel:
            self.hot = sel[0] if d > 0 else sel[-1]
        else:
            self.hot = sel[(sel.index(self.hot) + d) % len(sel)]
        self.update()

    def current(self):
        return self.rows[self.hot][0] if 0 <= self.hot < len(self.rows) else None

    def hit(self, pos):
        y = pos.y() - self.PAD
        for i, (r, ry, h) in enumerate(self.rows):
            if ry <= y < ry + h and r["k"] != "head":
                return i
        return -1

    def mouseMoveEvent(self, e):
        self.hot = self.hit(e.position())
        self.setCursor(Qt.CursorShape.PointingHandCursor if self.hot >= 0 else Qt.CursorShape.ArrowCursor)
        self.update()

    def leaveEvent(self, e):
        self.hot = -1
        self.update()

    def mousePressEvent(self, e):
        e.accept()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            i = self.hit(e.position())
            if i >= 0:
                r = self.rows[i][0]
                self.picked.emit(r["k"], r["val"])

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(self.a)
        p.translate(0, (1 - self.a) * (8 if self.above else -8))
        inner = QRectF(self.PAD, self.PAD, self.w, self.h)
        R = float(max(8, 22 if D["pill"] else min(D["radius"] + 6, 24)))
        paint_glass(p, inner, R)
        fm = QFontMetrics(F(13))
        for i, (r, ry, h) in enumerate(self.rows):
            top = inner.y() + ry
            if r["k"] == "head":
                f = F(11, QFont.Weight.Bold)
                f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.9)
                p.setFont(f)
                p.setPen(P["muted"])
                p.drawText(QRectF(inner.x() + 20, top + 6, self.w - 40, h - 6), AL_L, r["label"].upper())
                continue
            rr = QRectF(inner.x() + 6, top, self.w - 12, h)
            hot = i == self.hot
            tc, mc = P["text"], P["muted"]
            if hot:
                cr = corner(h)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(grad(rr.x(), 0, rr.right(), 0, P["acc"], P["acc2"])))
                p.drawRoundedRect(rr, cr, cr)
                tc, mc = P["onacc"], alpha(P["onacc"], 190)
            cx, cy = rr.x() + 26, rr.center().y()
            if r["k"] == "site":
                ir = QRectF(cx - 11, cy - 11, 22, 22)
                pm = FAV.get(r.get("host", ""))
                if pm is not None and not pm.isNull():
                    p.save()
                    clip = QPainterPath()
                    clip.addRoundedRect(ir, 6, 6)
                    p.setClipPath(clip)
                    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                    p.drawPixmap(ir, pm, QRectF(pm.rect()))
                    p.restore()
                else:
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(alpha(tc, 60) if hot else QBrush(grad(ir.left(), ir.top(), ir.right(), ir.bottom(), P["acc"], P["acc2"])))
                    p.drawRoundedRect(ir, 7, 7)
                    p.setPen(tc if hot else P["onacc"])
                    p.setFont(F(12, QFont.Weight.Bold))
                    p.drawText(ir, AL_C, (r["label"][:1] or "?").upper())
            else:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(tc if hot else mc, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                if r["k"] == "search":  # clock = something you searched before
                    p.drawEllipse(QPointF(cx, cy), 7.5, 7.5)
                    p.drawLine(QPointF(cx, cy), QPointF(cx, cy - 4))
                    p.drawLine(QPointF(cx, cy), QPointF(cx + 3.2, cy + 1.6))
                else:  # magnifier = recommended search
                    p.drawEllipse(QPointF(cx - 1.5, cy - 1.5), 5.2, 5.2)
                    p.drawLine(QPointF(cx + 2.4, cy + 2.4), QPointF(cx + 6.6, cy + 6.6))
            tx = rr.x() + 50
            right = rr.right() - 16
            if r.get("sub"):
                p.setFont(F(12))
                sub = QFontMetrics(F(12)).elidedText(r["sub"], Qt.TextElideMode.ElideRight, int(rr.width() * .34))
                p.setPen(mc)
                p.drawText(QRectF(tx, top, right - tx, h), AL_R, sub)
                right -= QFontMetrics(F(12)).horizontalAdvance(sub) + 14
            p.setFont(F(13))
            p.setPen(tc)
            p.drawText(QRectF(tx, top, max(10, right - tx), h), AL_L,
                       fm.elidedText(r["label"], Qt.TextElideMode.ElideRight, int(max(10, right - tx))))


class Avatar(QWidget):
    def __init__(self, name="", size=64):
        super().__init__()
        self.name = name
        self.setFixedSize(size, size)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad(0, 0, r.width(), r.height(), P["acc"], P["acc2"])))
        p.drawEllipse(r)
        p.setPen(P["onacc"])
        p.setFont(F(int(self.width() * .42), QFont.Weight.Bold))
        p.drawText(r, AL_C, (self.name[:1] or "?").upper())


class AvatarButton(Hover):
    def __init__(self):
        super().__init__()
        self.setFixedSize(36, 36)

    def paintEvent(self, e):
        p = self._mk()
        r = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        if CUR:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad(0, 0, r.width(), r.height(), mix(P["acc"], QColor("#ffffff"), .2 * self.h), P["acc2"])))
            p.drawEllipse(r)
            p.setPen(P["onacc"])
            p.setFont(F(13, QFont.Weight.Bold))
            p.drawText(r, AL_C, (CUR["name"][:1] or "?").upper())
        else:
            col = mix(P["muted"], P["text"], self.h)
            p.setPen(QPen(col, 1.6))
            p.setBrush(alpha(P["text"], 10 + 26 * self.h))
            p.drawEllipse(r)
            cx, cy = r.center().x(), r.center().y()
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(col, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawEllipse(QPointF(cx, cy - 2.6), 3.1, 3.1)
            p.drawArc(QRectF(cx - 5.6, cy + 1.6, 11.2, 10), 35 * 16, 110 * 16)


class ProviderButton(Hover):
    def __init__(self, kind, text):
        super().__init__()
        self.kind, self.text = kind, text
        self.setFixedHeight(40)
        self.setFixedWidth(QFontMetrics(F(13, QFont.Weight.DemiBold)).horizontalAdvance(text) + 78)

    def paintEvent(self, e):
        p = self._mk()
        r = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        rr = r.height() / 2 if D["pill"] else corner(r.height())
        p.setPen(QPen(alpha(P["text"], 45 + 70 * self.h), 1))
        p.setBrush(alpha(P["text"], 14 + 22 * self.h))
        p.drawRoundedRect(r, rr, rr)
        cx, cy = 28.0, r.height() / 2 + .5
        if self.kind == "google":
            for i, col in enumerate(("#ea4335", "#fbbc05", "#34a853", "#4285f4")):
                p.setPen(QPen(QColor(col), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawArc(QRectF(cx - 8, cy - 8, 16, 16), (45 + i * 90) * 16, 90 * 16)
            p.setPen(QPen(QColor("#4285f4"), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
            p.drawLine(QPointF(cx, cy), QPointF(cx + 8, cy))
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(P["text"])
            p.drawEllipse(QPointF(cx, cy), 10, 10)
            p.setPen(QPen(P["bg"], 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(cx - 2.5, cy - 4.5), QPointF(cx - 2.5, cy + 4.5))
            p.drawLine(QPointF(cx + 3, cy - 3), QPointF(cx + 3, cy - .5))
            p.drawLine(QPointF(cx + 3, cy - .5), QPointF(cx - 2.5, cy + 2.5))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(P["bg"])
            for x, y in ((cx - 2.5, cy - 4.5), (cx - 2.5, cy + 4.5), (cx + 3, cy - 3)):
                p.drawEllipse(QPointF(x, y), 1.9, 1.9)
        p.setPen(P["text"])
        p.setFont(F(13, QFont.Weight.DemiBold))
        p.drawText(QRectF(50, 0, r.width() - 58, r.height()), AL_L, self.text)


class ShieldButton(Hover):
    def __init__(self):
        super().__init__()
        self.setFixedSize(36, 36)
        self.n = 0

    def paintEvent(self, e):
        p = self._mk()
        on = bool(D["adblock"])
        cx, cy = 18.0, 19.0
        sh = QPainterPath()
        sh.moveTo(cx, cy - 9.5)
        sh.lineTo(cx + 8, cy - 6.5)
        sh.lineTo(cx + 8, cy + .5)
        sh.quadTo(cx + 8, cy + 7, cx, cy + 10.5)
        sh.quadTo(cx - 8, cy + 7, cx - 8, cy + .5)
        sh.lineTo(cx - 8, cy - 6.5)
        sh.closeSubpath()
        if on:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad(0, cy - 10, 0, cy + 11, mix(P["acc"], QColor("#ffffff"), .25 * self.h), P["acc2"])))
            p.drawPath(sh)
            p.setPen(QPen(P["onacc"], 1.9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPolyline(QPolygonF([QPointF(cx - 3.6, cy + .3), QPointF(cx - 1, cy + 3), QPointF(cx + 3.8, cy - 2.6)]))
        else:
            col = mix(P["muted"], P["text"], self.h)
            p.setPen(QPen(col, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.setBrush(alpha(P["text"], 8 + 24 * self.h))
            p.drawPath(sh)
            p.drawLine(QPointF(cx - 4, cy + 4), QPointF(cx + 4, cy - 4))
        if on and self.n > 0:
            txt = str(self.n) if self.n < 1000 else (f"{self.n / 1000:.1f}k" if self.n < 100000 else "99k+")
            f = F(9, QFont.Weight.Bold)
            tw = QFontMetrics(f).horizontalAdvance(txt)
            br = QRectF(self.width() - tw - 10, 1, tw + 8, 12)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(P["bg"])
            p.drawRoundedRect(br.adjusted(-1.2, -1.2, 1.2, 1.2), 7, 7)
            p.setBrush(P["acc2"])
            p.drawRoundedRect(br, 6, 6)
            p.setPen(P["onacc"])
            p.setFont(f)
            p.drawText(br, AL_C, txt)


class TabStrip(QScrollArea):
    """Tab row: tabs shrink as more open, then show only their icons, then the row scrolls."""
    TEXT_MIN, ICON_W = 100, 38

    def __init__(self, bar, bar_lay):
        super().__init__()
        self.bar, self.bar_lay, self._busy, self._total = bar, bar_lay, False, 0
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea{background:transparent;border:0}")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.inner = QWidget()
        self.setWidget(self.inner)
        self.viewport().setAutoFillBackground(False)
        self.inner.setAutoFillBackground(False)
        self.tab_lay = QHBoxLayout(self.inner)
        self.tab_lay.setContentsMargins(0, 0, 0, 0)
        self.tab_lay.setSpacing(6)
        self.tab_lay.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.inner.installEventFilter(self)

    def eventFilter(self, o, e):
        if o is self.inner and e.type() in (QEvent.Type.ChildAdded, QEvent.Type.ChildRemoved, QEvent.Type.LayoutRequest):
            QTimer.singleShot(0, self.relayout)
        return False

    def avail(self):
        lay, used, n = self.bar_lay, 0, self.bar_lay.count()
        for i in range(n):
            it = lay.itemAt(i)
            if it.widget() is not self:
                used += it.sizeHint().width()
        m = lay.contentsMargins()
        return self.bar.width() - m.left() - m.right() - used - lay.spacing() * (n - 1) - 4

    def relayout(self):
        if self._busy:
            return
        chips = [self.tab_lay.itemAt(i).widget() for i in range(self.tab_lay.count())]
        chips = [c for c in chips if c is not None]
        if not chips:
            return
        n, gap = len(chips), self.tab_lay.spacing()
        per = (self.avail() - gap * (n - 1)) / n
        w = min(220, int(per)) if per >= self.TEXT_MIN else self.ICON_W
        self._busy = True
        for c in chips:
            if c.minimumWidth() != w or c.maximumWidth() != w:
                c.setFixedWidth(w)
        self._busy = False
        total = n * w + gap * (n - 1)
        if total != self._total:
            self._total = total
            self.updateGeometry()

    def sizeHint(self):
        return QSize(max(self._total, 1), 34)

    def minimumSizeHint(self):
        return QSize(40, 20)

    def wheelEvent(self, e):
        d, sb = e.angleDelta(), self.horizontalScrollBar()
        sb.setValue(sb.value() - (d.x() if abs(d.x()) > abs(d.y()) else d.y()))
        e.accept()

    def ensure(self, chip):
        def go():
            try:
                if chip.parent() is self.inner:
                    self.ensureWidgetVisible(chip, 30, 0)
            except RuntimeError:
                pass
        QTimer.singleShot(40, go)


class TitleBar(QWidget):
    contextRequested = pyqtSignal(object)

    def __init__(self, win):
        super().__init__()
        self.win = win
        self.setFixedHeight(46)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(8)
        for col, fn in (("#ff5f57", win.close), ("#febc2e", win.showMinimized), ("#28c840", win.toggle_max)):
            d = Dot(col)
            d.clicked.connect(fn)
            lay.addWidget(d)
        lay.addSpacing(10)
        self.space_chip = Chip("Home", dot=QColor("#b46bff"))
        lay.addWidget(self.space_chip)
        self.strip = TabStrip(self, lay)
        self.tab_lay = self.strip.tab_lay
        lay.addWidget(self.strip)
        self.plus = IconButton("plus", 32)
        lay.addWidget(self.plus)
        lay.addStretch(1)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.RightButton:
            self.contextRequested.emit(e.globalPosition().toPoint())
        elif e.button() == Qt.MouseButton.LeftButton and self.window().windowHandle():
            self.window().windowHandle().startSystemMove()

    def mouseDoubleClickEvent(self, e):
        self.win.toggle_max()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.strip.relayout()


class Shell(QWidget):
    """Window background (gradient + floating orbs) and edge resizing."""

    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)

    def win_radius(self):
        win = self.window()
        if win.isMaximized() or win.isFullScreen():
            return 0.0
        return float(D["win_radius"])

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        wr = self.win_radius()
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, w, h), wr, wr)
        p.setClipPath(clip)
        p.fillRect(self.rect(), QBrush(grad(0, 0, w, h, P["bg"], P["bg2"])))
        if D["orbs"] and "orbs" in D["owned"]:
            t = time.time()
            cols = [P["acc"], P["acc2"], mix(P["acc"], P["text"], .35)]
            for i, col in enumerate(cols):
                cx = w * (0.5 + 0.42 * math.sin(t * (0.21 + i * .07) + i * 2))
                cy = h * (0.5 + 0.42 * math.cos(t * (0.17 + i * .05) + i * 3))
                rad = min(w, h) * (0.35 + 0.08 * i)
                rg = QRadialGradient(cx, cy, rad)
                rg.setColorAt(0, alpha(col, 110))
                rg.setColorAt(1, alpha(col, 0))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(rg))
                p.drawEllipse(QPointF(cx, cy), rad, rad)
        if wr > 0:
            # hairline edge so the rounded window reads cleanly on any desktop
            p.setClipping(False)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(alpha(P["text"], 40), 1))
            p.drawRoundedRect(QRectF(.5, .5, w - 1, h - 1), wr, wr)

    def _edge(self, pos):
        m, e = 7, None
        for cond, edge in ((pos.x() < m, Qt.Edge.LeftEdge), (pos.x() > self.width() - m, Qt.Edge.RightEdge),
                           (pos.y() < m, Qt.Edge.TopEdge), (pos.y() > self.height() - m, Qt.Edge.BottomEdge)):
            if cond:
                e = edge if e is None else e | edge
        return e

    def mouseMoveEvent(self, e):
        pos = e.position().toPoint()
        l, r = pos.x() < 7, pos.x() > self.width() - 7
        t, b = pos.y() < 7, pos.y() > self.height() - 7
        if (l and t) or (r and b):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif (r and t) or (l and b):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif l or r:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif t or b:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.unsetCursor()

    def mousePressEvent(self, e):
        edge = self._edge(e.position().toPoint())
        if edge is not None and self.window().windowHandle():
            self.window().windowHandle().startSystemResize(edge)


class Page(QWebEnginePage):
    def __init__(self, profile, parent, browser):
        super().__init__(profile, parent)
        self.browser = browser
        # Let sites use the clipboard (Copy / Paste buttons use navigator.clipboard).
        # Qt 6.8+ asks per-site through permissionRequested; older Qt allows it via the settings above.
        try:
            self.permissionRequested.connect(self._on_permission)
        except Exception:
            pass

    def _on_permission(self, perm):
        try:
            PT = type(perm).PermissionType
            ok = [getattr(PT, n) for n in ("ClipboardReadWrite", "ClipboardSanitizedWrite") if hasattr(PT, n)]
            if perm.permissionType() in ok:
                perm.grant()
        except Exception:
            pass

    def acceptNavigationRequest(self, url, nav_type, is_main):
        if url.host() == "cdg.start" and url.path() == "/remove":
            q = QUrlQuery(url)
            self.browser.remove_tile(q.queryItemValue("u", QUrl.ComponentFormattingOption.FullyDecoded))
            return False
        if url.host() == "cdg.start" and url.path() == "/chat":
            QTimer.singleShot(0, self.browser.open_chat)
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main)


class WebView(QWebEngineView):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.last_url = ""

    def createWindow(self, _type):
        return self.browser.new_tab("about:blank")

    def contextMenuEvent(self, e):
        e.accept()
        req = self.lastContextMenuRequest()
        if req is None:
            return
        A, R = QWebEnginePage.WebAction, QWebEngineContextMenuRequest
        link, media = req.linkUrl(), req.mediaUrl()
        has_link = link.isValid() and not link.isEmpty()
        is_img = req.mediaType() == R.MediaType.MediaTypeImage and media.isValid()
        sel = req.selectedText().strip()
        editable = req.isContentEditable()
        flags = req.editFlags()

        def can(name):
            try:
                return bool(flags & getattr(R.EditFlag, name))
            except Exception:
                return True

        def act(a):
            return lambda: self.triggerPageAction(a)

        clip = QApplication.clipboard()
        redo_hint = MOD + ("\u21e7Z" if IS_MAC else "Y")
        items = []
        if has_link:
            u = link.toString()
            items += [MI("Open link in new tab", lambda: self.browser.new_tab(u)),
                      MI("Copy link address", lambda: clip.setText(u))]
        if is_img:
            m = media.toString()
            items += [SEP, MI("Open image in new tab", lambda: self.browser.new_tab(m)),
                      MI("Copy image", act(A.CopyImageToClipboard)),
                      MI("Copy image address", lambda: clip.setText(m))]
        if editable:
            items += [SEP, MI("Undo", act(A.Undo), can("CanUndo"), MOD + "Z"),
                      MI("Redo", act(A.Redo), can("CanRedo"), redo_hint), SEP,
                      MI("Cut", act(A.Cut), can("CanCut"), MOD + "X"),
                      MI("Copy", act(A.Copy), can("CanCopy"), MOD + "C"),
                      MI("Paste", act(A.Paste), can("CanPaste"), MOD + "V"),
                      MI("Select all", act(A.SelectAll), can("CanSelectAll"), MOD + "A")]
        elif sel:
            short = sel if len(sel) <= 24 else sel[:24] + "\u2026"
            items += [SEP, MI("Copy", act(A.Copy), True, MOD + "C"),
                      MI(f"Search {D['engine']} for \u201c{short}\u201d",
                         lambda: self.browser.new_tab(self.browser.search_url(sel)))]
        if not (has_link or is_img or editable or sel):
            hist = self.history()
            items = [ICONS(("back", self.back, hist.canGoBack()),
                           ("forward", self.forward, hist.canGoForward()),
                           ("reload", self.reload, True)),
                     SEP, MI("Select all", act(A.SelectAll), True, MOD + "A")]
            u = self.url()
            if u.scheme() in ("http", "https") and u.host() != "cdg.start":
                us = u.toString()
                items += [SEP, MI("Copy page address", lambda: clip.setText(us)),
                          MI("Add to start page", lambda: self.browser.add_tile(self.title(), us)),
                          MI("View page source", lambda: self.browser.new_tab("view-source:" + us))]
        popup_menu(items, e.globalPos())


# ------------------------------------------------------------------ start page
START_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>CDG</title><style>
*{box-sizing:border-box}html,body{margin:0;height:100%;overflow:hidden}
body{background:linear-gradient(135deg,__BG__,__BG2__);color:__TEXT__;font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;display:flex;align-items:center;justify-content:center}
.orb{position:absolute;border-radius:50%;filter:blur(80px);opacity:.5;animation:f 14s ease-in-out infinite alternate}
.o1{width:440px;height:440px;background:__ACC__;top:-100px;left:-80px}
.o2{width:380px;height:380px;background:__ACC2__;bottom:-110px;right:-50px;animation-delay:-5s}
.o3{width:260px;height:260px;background:__ACC__;top:42%;left:58%;animation-delay:-9s;opacity:.3}
@keyframes f{to{transform:translate(70px,-50px) scale(1.18)}}
.wrap{position:relative;z-index:1;width:min(700px,90vw);text-align:center}
.clock{font-size:92px;font-weight:200;letter-spacing:-3px;line-height:1}
.hi{margin:10px 0 32px;font-size:18px;color:__MUTED__}
form{display:flex;gap:10px;padding:8px;border-radius:999px;background:rgba(__TEXTRGB__,.10);border:1px solid rgba(__TEXTRGB__,.22);transition:.25s}
form:focus-within{border-color:__ACC__;box-shadow:0 0 0 4px rgba(__ACCRGB__,.25),0 12px 44px rgba(__ACCRGB__,.4)}
input{flex:1;background:transparent;border:0;outline:0;color:__TEXT__;font-size:18px;padding:12px 18px}
input::placeholder{color:__MUTED__}
button{border:0;border-radius:999px;padding:0 28px;font-size:15px;font-weight:600;color:__ONACC__;background:linear-gradient(90deg,__ACC__,__ACC2__);cursor:pointer}
.tiles{display:flex;flex-wrap:wrap;justify-content:center;gap:14px;margin-top:36px}
.tw{position:relative;width:100px;transition:opacity .2s,transform .22s}.tw.gone{opacity:0;transform:scale(.6)}
.x{position:absolute;top:5px;right:5px;width:22px;height:22px;border-radius:50%;display:grid;place-items:center;font-size:15px;line-height:1;cursor:pointer;opacity:0;transform:scale(.6);transition:.15s;background:rgba(__TEXTRGB__,.18);color:__TEXT__}
.tw:hover .x{opacity:1;transform:scale(1)}.x:hover{background:#ff5f57;color:#fff}
.hint{display:none;margin-top:30px;font-size:13px;color:__MUTED__}
.tile{width:100%;text-decoration:none;color:__TEXT__;font-size:13px;display:flex;flex-direction:column;align-items:center;gap:9px;padding:18px 6px;border-radius:22px;background:rgba(__TEXTRGB__,.07);border:1px solid rgba(__TEXTRGB__,.14);transition:.2s}
.tile:hover{transform:translateY(-6px);background:rgba(__TEXTRGB__,.15);border-color:__ACC__}
.ic{width:48px;height:48px;border-radius:17px;display:grid;place-items:center;font-weight:700;font-size:21px;color:#0b0916;transition:background .2s}
.ic.has{background:rgba(255,255,255,.95)!important}.ic img{width:28px;height:28px;border-radius:6px;display:none}
.tile span.nm{max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.stats{margin-top:32px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap;font-size:13px;color:__MUTED__}
.stats span{padding:7px 15px;border-radius:999px;background:rgba(__TEXTRGB__,.08);border:1px solid rgba(__TEXTRGB__,.14)}
</style></head><body><div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div>
<div class="wrap"><div class="clock" id="c"></div><div class="hi" id="g"></div>
<form id="f" action="__ACTION__" method="get"><input id="q" name="__PARAM__" placeholder="Search __ENGINE__ or type a web address" autofocus autocomplete="off"><button>Search</button></form>
<div class="tiles" id="tl">__TILES__</div><div class="hint" id="hint">No bookmarks yet - right-click any page and choose Add to start page.</div>
<div class="stats"><span>__COINS__ CDG coins</span><span>__VISITS__ pages visited</span><span>__THEME__</span></div></div>
<script>
function t(){var d=new Date(),h=d.getHours(),m=d.getMinutes();document.getElementById('c').textContent=(h%12||12)+':'+(m<10?'0':'')+m;
document.getElementById('g').textContent=(h<12?'Good morning':h<18?'Good afternoon':'Good evening')+' - welcome to CDG';}
t();setInterval(t,10000);
function rm(el,u){var w=el.parentNode;w.classList.add('gone');setTimeout(function(){w.classList.add('dead');w.style.display='none';if(!document.querySelectorAll('.tw:not(.dead)').length)document.getElementById('hint').style.display='block';},230);location.href='https://cdg.start/remove?u='+encodeURIComponent(u);}
if(!document.querySelector('.tw'))document.getElementById('hint').style.display='block';
document.getElementById('f').onsubmit=function(){var v=document.getElementById('q').value.trim();
if(/^[\\w-]+(\\.[\\w-]+)+(\\/\\S*)?$/.test(v)){location.href='https://'+v;return false;}return true;};
</script></body></html>"""


# ------------------------------------------------------------------ main window
class Win(QMainWindow):
    oauthEvent = pyqtSignal(str, object)
    adlistEvent = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.acct_mode, self.oauth, self.oauth_err, self._oauth_run = "signin", None, "", 0
        self._h264, self._codec_asked = None, False
        self._ad_seen, self._ad_dirty, self._ad_saved = 0, False, 0.0
        self.oauthEvent.connect(self.on_oauth)
        self.adlistEvent.connect(self.on_adlist)
        DIR.mkdir(parents=True, exist_ok=True)
        load_session()
        load_data()
        refresh_pal()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("CDG Browse")
        self.resize(1320, 840)
        self.setMinimumSize(900, 600)
        self.cookies = {}
        self.tabs = []
        self.current = None
        self.mode = "browser"

        self.profile = QWebEngineProfile("CDGBrowseV2", self)
        self.profile.setPersistentStoragePath(str(DIR / "web"))
        self.profile.setCachePath(str(DIR / "cache"))
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        store = self.profile.cookieStore()
        store.cookieAdded.connect(self.on_cookie_added)
        store.cookieRemoved.connect(self.on_cookie_removed)
        store.loadAllCookies()
        self.profile.downloadRequested.connect(self.on_download)
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        # Present as a normal Chrome (sites like TikTok/Instagram reject the "QtWebEngine" token),
        # keeping the real Chromium version so features and UA stay consistent.
        m = re.search(r"Chrome/(\d+)", self.profile.httpUserAgent())
        plat = {"darwin": "Macintosh; Intel Mac OS X 10_15_7", "win32": "Windows NT 10.0; Win64; x64"}.get(sys.platform, "X11; Linux x86_64")
        self.profile.setHttpUserAgent(f"Mozilla/5.0 ({plat}) AppleWebKit/537.36 (KHTML, like Gecko) "
                                      f"Chrome/{m.group(1) if m else '124'}.0.0.0 Safari/537.36")
        st = self.profile.settings()
        for name, on in (("PlaybackRequiresUserGesture", False),  # feeds autoplay like a normal browser
                         ("JavascriptCanOpenWindows", True), ("JavascriptCanAccessClipboard", True), ("JavascriptCanPaste", True),
                         ("LocalStorageEnabled", True), ("WebGLEnabled", True),
                         ("Accelerated2dCanvasEnabled", True), ("AllowWindowActivationFromJavaScript", True),
                         ("DnsPrefetchEnabled", True)):
            try:
                st.setAttribute(getattr(QWebEngineSettings.WebAttribute, name), on)
            except Exception:
                pass
        self.adblock = AdBlocker(self)
        self.profile.setUrlRequestInterceptor(self.adblock)
        self.adblock.load_saved()
        self.sync_adblock()

        self.shell = Shell()
        self.setCentralWidget(self.shell)
        root = QVBoxLayout(self.shell)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        self.titlebar = TitleBar(self)
        self.titlebar.plus.clicked.connect(lambda: self.new_tab())
        self.titlebar.contextRequested.connect(self.titlebar_menu)
        root.addWidget(self.titlebar)

        self.toolrow = ToolRow()
        self.toolrow.setFixedHeight(56)
        self.toolrow.contextRequested.connect(self.toolbar_menu)
        tr = QHBoxLayout(self.toolrow)
        tr.setContentsMargins(10, 0, 10, 0)
        tr.setSpacing(4)
        self.tr_lay = tr
        self.tb = {}
        for kind, fn in (("back", lambda: self.nav("back")), ("forward", lambda: self.nav("forward")),
                         ("reload", lambda: self.nav("reload")), ("home", self.go_home)):
            b = IconButton(kind)
            b.clicked.connect(fn)
            self.tb[kind] = b
        self.address = AddressBar()
        self.address.set_engine_name(D["engine"])
        self.address.engineClicked.connect(self.engine_menu)
        self.address.provider = self.suggest_rows
        self.address.siteChosen.connect(lambda u: self.go(u))
        self.address.searchChosen.connect(self.go_search)
        self.address.edit.returnPressed.connect(lambda: self.go(self.address.edit.text()))
        attach_text_menu(self.address.edit, lambda: [
            MI("Paste and go", lambda: self.go(QApplication.clipboard().text()),
               bool(QApplication.clipboard().text().strip()))])
        self.tb["address"] = self.address
        self.toast = Toast()
        self.coin = CoinChip()
        self.coin.clicked.connect(lambda: self.show_panel("shop"))
        self.tb["coins"] = self.coin
        shop = IconButton("shop")
        shop.clicked.connect(lambda: self.show_panel("shop"))
        sett = IconButton("settings")
        sett.clicked.connect(lambda: self.show_panel("settings"))
        self.tb["shop"], self.tb["settings"] = shop, sett
        self.avatar = AvatarButton()
        self.avatar.clicked.connect(lambda: self.show_panel("account"))
        self.tb["account"] = self.avatar
        self.shield = ShieldButton()
        self.shield.clicked.connect(self.adblock_menu)
        self.tb["adblock"] = self.shield
        self.ad_timer = QTimer(self)
        self.ad_timer.timeout.connect(self.ad_sync)
        self.ad_timer.start(1000)
        bld = IconButton("build")
        bld.clicked.connect(lambda: self.show_panel("build"))
        self.tb["build"] = bld
        root.addWidget(self.toolrow)

        self.root_lay = root
        body = QHBoxLayout()
        body.setSpacing(8)
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        self.side_lay = QVBoxLayout(self.sidebar)
        self.side_lay.setContentsMargins(0, 0, 0, 0)
        self.side_lay.setSpacing(6)
        self.side_lay.addStretch(1)
        body.addWidget(self.sidebar)
        self.stack = QStackedWidget()
        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)
        self.pages = {}
        for name in ("settings", "shop", "build", "account"):
            sa = QScrollArea()
            sa.setWidgetResizable(True)
            sa.setFrameShape(QFrame.Shape.NoFrame)
            sa.viewport().setAutoFillBackground(False)
            self.stack.addWidget(sa)
            self.pages[name] = sa

        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(lambda: self.new_tab())
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(lambda: self.current and self.close_view(self.current))
        for keys, fn in (("F5", lambda: self.nav("reload")), ("Ctrl+R", lambda: self.nav("reload")),
                         ("Alt+Left", lambda: self.nav("back")), ("Alt+Right", lambda: self.nav("forward")),
                         ("Ctrl+Tab", lambda: self.cycle_tab(1)), ("Ctrl+Shift+Tab", lambda: self.cycle_tab(-1)),
                         ("Ctrl+B", lambda: self.show_panel("build")), ("Ctrl+,", lambda: self.show_panel("settings")),
                         ("Escape", lambda: self.isFullScreen() and self.current and self.current.page().triggerAction(
                             QWebEnginePage.WebAction.ExitFullScreen))):
            QShortcut(QKeySequence(keys), self).activated.connect(fn)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(
            lambda: (self.address.edit.setFocus(), self.address.edit.selectAll()))

        self.tick_timer = QTimer(self)
        self.tick_timer.setInterval(50)
        self.tick_timer.timeout.connect(self.tick)
        self.tick_timer.start()

        self.restyle()
        self.coin.set_coins(D["coins"])
        self.titlebar.space_chip.clicked.connect(self.space_menu)
        self.apply_layout()
        self.new_tab()

    # ---------- window
    def toggle_max(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def apply_margins(self):
        """Keep the UI tucked inside the window's rounded corners."""
        wr = self.shell.win_radius()
        m = int(round(8 + wr * 0.24))
        self.root_lay.setContentsMargins(m, m, m, m)
        self.shell.update()

    def changeEvent(self, e):
        if e.type() == QEvent.Type.WindowStateChange and hasattr(self, "root_lay"):
            self.apply_margins()
        super().changeEvent(e)

    def fade_in(self, w, ms=280):
        """Soft fade + settle for panels."""
        eff = QGraphicsOpacityEffect(w)
        eff.setOpacity(0.0)
        w.setGraphicsEffect(eff)
        an = QPropertyAnimation(eff, b"opacity", self)
        an.setDuration(ms)
        an.setStartValue(0.0)
        an.setEndValue(1.0)
        an.setEasingCurve(QEasingCurve.Type.OutCubic)
        an.finished.connect(lambda w=w: w.setGraphicsEffect(None))
        self._fade = an
        an.start()

    def tick(self):
        global RAINBOW_H
        if D["rainbow"] and "rainbow_accent" in D["owned"]:
            RAINBOW_H = (RAINBOW_H + 1.2) % 360
            refresh_pal()
            self.refresh_all()
        elif D["orbs"] and "orbs" in D["owned"]:
            self.shell.update()

    def refresh_all(self):
        self.shell.update()
        self.toolrow.update()
        self.address.update()
        for w in self.findChildren(Hover):
            w.update()

    def restyle(self):
        refresh_pal()
        D["spaces"][D["space"]]["theme"] = D["theme"]
        self.sync_space_chip()
        QApplication.instance().setStyleSheet(qss())
        self.apply_margins()
        self.refresh_all()
        save()

    def say(self, text):
        self.toast.show_msg(text)

    # ---------- tabs
    def new_tab(self, url=None):
        view = WebView(self)
        view.setPage(Page(self.profile, view, self))
        view.page().fullScreenRequested.connect(self.on_fullscreen)
        self.stack.addWidget(view)
        chip = TabChip()
        self.add_chip(chip)
        self.tabs.append({"view": view, "chip": chip, "space": D["space"]})
        chip.clicked.connect(lambda v=view: self.select_view(v))
        chip.closeRequested.connect(lambda v=view: self.close_view(v))
        chip.contextRequested.connect(lambda gp, v=view: self.tab_menu(v, gp))
        view.titleChanged.connect(lambda t, v=view: self.set_title(v, t))
        view.iconChanged.connect(lambda ic, v=view: self.set_icon(v, ic))
        view.urlChanged.connect(lambda u, v=view: self.on_url(v, u))
        view.loadFinished.connect(lambda ok, v=view: self.on_load(v, ok))
        if url is None:
            self.open_home(view)
        elif url != "about:blank":
            view.setUrl(QUrl(url))
        if len(self.tabs) >= 5:
            self.award("multitask")
        self.select_view(view)
        return view

    def tab_of(self, view):
        for t in self.tabs:
            if t["view"] is view:
                return t
        return None

    def select_view(self, view):
        self.current = view
        self.mode = "browser"
        self.stack.setCurrentWidget(view)
        for t in self.tabs:
            t["chip"].sel = t["view"] is view
            t["chip"].update()
            if t["view"] is view:
                self.titlebar.strip.ensure(t["chip"])
        self.sync_address()

    def close_view(self, view):
        t = self.tab_of(view)
        if not t:
            return
        sp = t["space"]
        i = [x for x in self.tabs if x["space"] == sp].index(t)
        if sum(1 for x in self.tabs if x["space"] == sp) == 1:
            self.new_tab()
        self.tabs.remove(t)
        self.titlebar.tab_lay.removeWidget(t["chip"])
        self.side_lay.removeWidget(t["chip"])
        t["chip"].deleteLater()
        self.stack.removeWidget(view)
        view.deleteLater()
        if self.current is view:
            rest = [x for x in self.tabs if x["space"] == sp]
            self.select_view(rest[min(i, len(rest) - 1)]["view"])

    def set_title(self, view, title):
        t = self.tab_of(view)
        if t:
            t["chip"].title = title or "New Tab"
            t["chip"].update()
        key = view.url().toString().split("#")[0]
        if title and key.startswith("http"):
            for h in D["history"]:
                if h["url"] == key:
                    h["title"] = title
                    break

    def set_icon(self, view, icon):
        t = self.tab_of(view)
        if t:
            t["chip"].set_icon(icon)
        host = view.url().host().lower()
        if host and icon is not None and not icon.isNull():
            pm = icon.pixmap(QSize(32, 32))
            if not pm.isNull():
                FAV[host] = pm

    def on_url(self, view, url):
        if view is self.current:
            self.sync_address()

    def sync_address(self):
        if not self.current:
            return
        u = self.current.url()
        text = "" if u.host() == "cdg.start" or u.toString() == "about:blank" else u.toString()
        if not self.address.edit.hasFocus():
            self.address.edit.setText(text)

    # ---------- navigation
    def to_url(self, text):
        text = text.strip()
        if text.startswith(("http://", "https://", "file://")):
            return text
        if "." in text and " " not in text:
            return "https://" + text
        return self.search_url(text)

    def search_url(self, text):
        action, param = ENGINES[D["engine"]]
        return f"{action}?{param}={quote(text)}"

    # ---------- context menus
    def tab_menu(self, view, gp):
        def dup():
            u = view.url().toString()
            self.new_tab(u if u.startswith("http") else None)

        def close_others():
            for t in list(self.tabs):
                if t["view"] is not view and t["space"] == D["space"]:
                    self.close_view(t["view"])
            self.select_view(view)
        popup_menu([MI("New tab", lambda: self.new_tab(), True, MOD + "T"),
                    MI("Reload", view.reload),
                    MI("Duplicate tab", dup),
                    MI("Add to start page", lambda: self.add_tile(view.title(), view.url().toString()),
                       view.url().scheme() in ("http", "https") and view.url().host() != "cdg.start"), SEP,
                    MI("Close tab", lambda: self.close_view(view), True, MOD + "W"),
                    MI("Close other tabs", close_others, len(self.tabs) > 1)], gp)

    def titlebar_menu(self, gp):
        popup_menu([MI("New tab", lambda: self.new_tab(), True, MOD + "T"), SEP,
                    MI("Open in default browser", lambda: self.open_external()),
                    MI("CDG Account", lambda: self.show_panel("account")),
                    MI("Build your browser", lambda: self.show_panel("build")),
                    MI("Settings", lambda: self.show_panel("settings")),
                    MI("CDG Shop", lambda: self.show_panel("shop"))], gp)

    def open_external(self):
        """Open the current page in the system browser (for sites whose videos need H.264)."""
        from PyQt6.QtGui import QDesktopServices
        u = self.current.url() if self.current else None
        if u is None or not u.toString().startswith("http"):
            self.say("Open a web page first")
            return
        QDesktopServices.openUrl(u)

    def open_chat(self):
        """Open CDG Chat. Uses the server in Settings (or CDG_CHAT_URL) if set, otherwise runs the
        built-in chat server on this computer."""
        import subprocess, socket
        if not CUR:
            self.say("Sign in to your CDG Account to use CDG Chat")
            self.show_panel("account")
            return
        kf = DIR / "chat_key"
        try:
            sec = kf.read_text().strip()
        except Exception:
            sec = secrets.token_hex(32)
            DIR.mkdir(exist_ok=True)
            kf.write_text(sec)
            os.chmod(kf, 0o600)
        name = re.sub(r"[^A-Za-z0-9_]", "", CUR["name"].split("@")[0].replace(" ", "_"))[:20]
        if len(name) < 2:
            name = ("user" + safe_id(CUR["id"]))[:20]
        key = hmac.new(sec.encode(), (CUR.get("provider", "") + ":" + CUR["id"]).encode(), "sha256").hexdigest()
        base = (os.environ.get("CDG_CHAT_URL") or D.get("chat_url") or "").strip().split("#")[0].rstrip("/")
        if base and not base.startswith(("http://", "https://")):
            base = "http://" + base
        local = not base
        url = (base or f"http://127.0.0.1:{CHAT_PORT}") + "/#u=" + quote(name) + "&k=" + key
        if not local:
            self.new_tab(url)
            return

        def up():
            try:
                socket.create_connection(("127.0.0.1", CHAT_PORT), timeout=0.3).close()
                return True
            except OSError:
                return False
        global CHAT_PROC
        if not up():
            try:
                kw = {"creationflags": 0x08000000} if sys.platform == "win32" else {}
                CHAT_PROC = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--chat-server", "--local"],
                                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)
            except Exception:
                self.say("Couldn't start CDG Chat")
                return
        tries = [0]

        def wait():
            if up() or tries[0] > 25:
                self.new_tab(url)
            else:
                tries[0] += 1
                QTimer.singleShot(150, wait)
        wait()

    # ---------- downloads, fullscreen, tab cycling
    def on_download(self, item):
        d = Path.home() / "Downloads"
        d.mkdir(exist_ok=True)
        name = item.downloadFileName() or "download"
        stem, suf = Path(name).stem, Path(name).suffix
        target, n = d / name, 1
        while target.exists():
            target = d / f"{stem} ({n}){suf}"
            n += 1
        item.setDownloadDirectory(str(d))
        item.setDownloadFileName(target.name)
        item.accept()
        self.say("Downloading " + target.name)

        def done(it=item, nm=target.name):
            if it.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
                self.say("Downloaded " + nm + " to Downloads")
        item.isFinishedChanged.connect(done)

    def on_fullscreen(self, req):
        req.accept()
        on = req.toggleOn()
        self.titlebar.setVisible(not on)
        self.toolrow.setVisible(not on)
        self.sidebar.setVisible(not on and D["tabpos"] == "side")
        self.showFullScreen() if on else self.showNormal()

    def cycle_tab(self, d):
        mine = [t for t in self.tabs if t["space"] == D["space"]]
        if len(mine) > 1 and self.current:
            i = [t["view"] for t in mine].index(self.current) if self.current in [t["view"] for t in mine] else 0
            self.select_view(mine[(i + d) % len(mine)]["view"])

    # ---------- build mode: layout, templates, spaces
    def add_chip(self, chip):
        chip.setFixedHeight(self.tab_h if hasattr(self, "tab_h") else 34)
        if D["tabpos"] == "side":
            chip.setMinimumWidth(100)
            chip.setMaximumWidth(220)
            self.side_lay.insertWidget(max(0, self.side_lay.count() - 1), chip)
        else:
            self.titlebar.tab_lay.addWidget(chip, 1)

    def apply_layout(self):
        tb_h, self.tab_h, gap = {"compact": (46, 28, 6), "cozy": (56, 34, 8), "roomy": (68, 40, 12)}[D["density"]]
        self.toolrow.setFixedHeight(tb_h)
        self.root_lay.setSpacing(gap)
        D["tb_order"] = [k for k in D["tb_order"] if k in DEFAULT_ORDER] + [k for k in DEFAULT_ORDER if k not in D["tb_order"]]
        while self.tr_lay.count():
            self.tr_lay.takeAt(0)
        for key in D["tb_order"]:
            w = self.tb[key]
            self.tr_lay.addWidget(w, 1 if key == "address" else 0)
            w.setVisible(key in LOCKED or key not in D["tb_hidden"])
            if key == "address":
                self.tr_lay.addWidget(self.toast)
        self.root_lay.removeWidget(self.toolrow)
        if D["toolbar"] == "bottom":
            self.root_lay.addWidget(self.toolrow)
        else:
            self.root_lay.insertWidget(1, self.toolrow)
        for t in self.tabs:
            self.titlebar.tab_lay.removeWidget(t["chip"])
            self.side_lay.removeWidget(t["chip"])
            self.add_chip(t["chip"])
        self.sidebar.setVisible(D["tabpos"] == "side")

    def set_layout(self, key, val):
        D[key], D["template"] = val, "Custom"
        save()
        self.apply_layout()
        self.award("builder")
        self.rebuild_later()

    def apply_template(self, name):
        t = TEMPLATES[name]
        D.update(toolbar=t["toolbar"], tabpos=t["tabpos"], density=t["density"],
                 tb_order=list(t["order"]), tb_hidden=list(t["hidden"]), template=name)
        save()
        self.apply_layout()
        self.award("builder")
        self.rebuild_later()
        self.say("Template: " + name)

    def set_tb_visible(self, key, on):
        hid = D["tb_hidden"]
        if on and key in hid:
            hid.remove(key)
        elif not on and key not in hid:
            hid.append(key)
        D["template"] = "Custom"
        save()
        self.apply_layout()
        self.award("builder")

    def move_item(self, i, d):
        o, j = D["tb_order"], i + d
        if 0 <= j < len(o):
            o[i], o[j] = o[j], o[i]
            D["template"] = "Custom"
            save()
            self.apply_layout()
            self.rebuild_later()

    def toolbar_menu(self, gp):
        top, side = D["toolbar"] == "top", D["tabpos"] == "side"
        popup_menu([MI("Customize layout...", lambda: self.show_panel("build")), SEP,
                    MI("Move toolbar to " + ("bottom" if top else "top"),
                       lambda: self.set_layout("toolbar", "bottom" if top else "top")),
                    MI("Put tabs on the " + ("top bar" if side else "side"),
                       lambda: self.set_layout("tabpos", "top" if side else "side"))], gp)

    def sync_space_chip(self):
        sp = D["spaces"][D["space"]]
        self.titlebar.space_chip.set_text(sp["name"], QColor(THEMES[sp["theme"]]["accent"]))

    def space_menu(self):
        items = [MI(sp["name"], lambda i=i: self.switch_space(i), True, "Active" if i == D["space"] else "")
                 for i, sp in enumerate(D["spaces"])]
        c = self.titlebar.space_chip
        popup_menu(items + [SEP, MI("New space", self.add_space),
                            MI("Manage spaces", lambda: self.show_panel("build"))],
                   c.mapToGlobal(c.rect().bottomLeft()))

    def switch_space(self, i):
        if not 0 <= i < len(D["spaces"]):
            return
        was = self.mode
        D["space"] = i
        th = D["spaces"][i]["theme"]
        if th != D["theme"] and th in self.owned_themes():
            D["theme"], D["accent"] = th, ""
        for t in self.tabs:
            t["chip"].setVisible(t["space"] == i)
        mine = [t for t in self.tabs if t["space"] == i]
        self.restyle()
        self.select_view(mine[-1]["view"]) if mine else self.new_tab()
        self.say("Space: " + D["spaces"][i]["name"])
        if was in self.pages:
            self.show_panel(was)

    def add_space(self):
        D["spaces"].append({"name": f"Space {len(D['spaces']) + 1}", "theme": D["theme"]})
        self.award("spacer")
        self.switch_space(len(D["spaces"]) - 1)
        self.rebuild_later()

    def rename_space(self, i, text):
        if i < len(D["spaces"]) and text.strip():
            D["spaces"][i]["name"] = text.strip()[:18]
            save()
            self.sync_space_chip()

    def delete_space(self, i):
        if len(D["spaces"]) < 2:
            return
        for t in [t for t in self.tabs if t["space"] == i]:
            self.tabs.remove(t)
            self.titlebar.tab_lay.removeWidget(t["chip"])
            self.side_lay.removeWidget(t["chip"])
            t["chip"].deleteLater()
            self.stack.removeWidget(t["view"])
            t["view"].deleteLater()
        for t in self.tabs:
            if t["space"] > i:
                t["space"] -= 1
        D["spaces"].pop(i)
        self.current = None
        self.switch_space(max(0, i - 1))
        self.rebuild_later()

    def build_layout(self):
        host, outer = self._host("Build Your Browser")
        sub = QLabel("Pick a starter template, then tweak layout, toolbar items and Spaces.")
        sub.setObjectName("muted")
        outer.addWidget(sub)
        c = self._card(outer, "Starter templates")
        row = QHBoxLayout()
        row.setSpacing(8)
        for name in TEMPLATES:
            ch = Chip(name, selected=(name == D["template"]))
            ch.clicked.connect(lambda n=name: self.apply_template(n))
            row.addWidget(ch)
        row.addStretch(1)
        c.addLayout(row)
        c = self._card(outer, "Layout")
        for label, key, opts in (("Toolbar position", "toolbar", (("Top", "top"), ("Bottom", "bottom"))),
                                 ("Tab position", "tabpos", (("Top bar", "top"), ("Side bar", "side"))),
                                 ("Density", "density", (("Compact", "compact"), ("Cozy", "cozy"), ("Roomy", "roomy")))):
            r = QHBoxLayout()
            r.setSpacing(8)
            for text, val in opts:
                ch = Chip(text, selected=(D[key] == val))
                ch.clicked.connect(lambda k=key, v=val: self.set_layout(k, v))
                r.addWidget(ch)
            r.addStretch(1)
            c.addLayout(self._row(label, r, stretch_last=True))
        c = self._card(outer, "Toolbar items")
        info = QLabel("Show, hide and reorder with the arrows. Address, Build and Settings stay on.")
        info.setObjectName("muted")
        c.addWidget(info)
        for n, key in enumerate(D["tb_order"]):
            h = QHBoxLayout()
            h.setSpacing(8)
            lab = QLabel(ITEM_NAMES[key])
            lab.setFixedWidth(150)
            h.addWidget(lab)
            if key in LOCKED:
                m = QLabel("Always on")
                m.setObjectName("muted")
                h.addWidget(m)
            else:
                tg = Toggle(key not in D["tb_hidden"])
                tg.toggled.connect(lambda on, k=key: self.set_tb_visible(k, on))
                h.addWidget(tg)
            h.addStretch(1)
            for kind, d in (("back", -1), ("forward", 1)):
                b = IconButton(kind, 30)
                b.clicked.connect(lambda i=n, d=d: self.move_item(i, d))
                h.addWidget(b)
            c.addLayout(h)
        c = self._card(outer, "Spaces")
        info = QLabel("Each Space keeps its own tabs and theme. Switch from the chip in the title bar.")
        info.setObjectName("muted")
        c.addWidget(info)
        for i, sp in enumerate(D["spaces"]):
            h = QHBoxLayout()
            h.setSpacing(8)
            name = QLineEdit(sp["name"])
            name.setObjectName("input")
            attach_text_menu(name)
            name.editingFinished.connect(lambda i=i, w=name: self.rename_space(i, w.text()))
            h.addWidget(name, 1)
            th = QLabel(sp["theme"])
            th.setObjectName("muted")
            h.addWidget(th)
            cur = i == D["space"]
            go = PillButton("Active" if cur else "Switch", primary=not cur)
            go.set_off(cur)
            go.clicked.connect(lambda i=i: self.switch_space(i))
            h.addWidget(go)
            if len(D["spaces"]) > 1:
                de = PillButton("Delete")
                de.clicked.connect(lambda i=i: self.delete_space(i))
                h.addWidget(de)
            c.addLayout(h)
        add = PillButton("Add space", primary=True)
        add.clicked.connect(self.add_space)
        ar = QHBoxLayout()
        ar.addWidget(add)
        ar.addStretch(1)
        c.addLayout(ar)
        outer.addStretch(1)
        return host

    def start_html(self):
        text, acc = P["text"], P["acc"]
        action, param = ENGINES[D["engine"]]
        tiles = ""
        acc2 = P["acc2"].name()
        for t in D["tiles"]:
            n, u, c = t.get("name") or t["url"], t["url"], t.get("color") or P["acc"].name()
            host = urlparse(u).hostname or ""
            logo = f"https://icons.duckduckgo.com/ip3/{host}.ico"
            tiles += (f'<div class="tw"><a class="tile" href="{escape(u, True)}">'
                      f'<span class="ic" style="background:linear-gradient(135deg,{c},{acc2})">'
                      f'<b>{escape(n[:1].upper())}</b>'
                      f'<img src="{escape(logo, True)}" onload="this.previousSibling.style.display=\'none\';this.style.display=\'block\';this.parentNode.classList.add(\'has\')" onerror="this.remove()">'
                      f'</span><span class="nm">{escape(n)}</span></a>'
                      f'<span class="x" title="Remove" data-u="{escape(u, True)}" onclick="rm(this,this.dataset.u)">&times;</span></div>')
        rep = {"__BG__": P["bg"].name(), "__BG2__": P["bg2"].name(), "__TEXT__": text.name(),
               "__ACC__": acc.name(), "__ACC2__": P["acc2"].name(), "__MUTED__": P["muted"].name(),
               "__ONACC__": P["onacc"].name(), "__TEXTRGB__": f"{text.red()},{text.green()},{text.blue()}",
               "__ACCRGB__": f"{acc.red()},{acc.green()},{acc.blue()}", "__ACTION__": action, "__PARAM__": param,
               "__ENGINE__": D["engine"], "__TILES__": tiles, "__COINS__": str(D["coins"]),
               "__VISITS__": str(D["visits"]), "__THEME__": D["theme"]}
        html = START_HTML
        for k, v in rep.items():
            html = html.replace(k, v)
        return html

    def open_home(self, view):
        h = D["home"].strip()
        if h in ("", "start"):
            view.setHtml(self.start_html(), QUrl("https://cdg.start/"))
        else:
            view.setUrl(QUrl(self.to_url(h)))

    def remove_tile(self, url):
        D["tiles"] = [t for t in D["tiles"] if t["url"] != url]
        save()

    def add_tile(self, title, url):
        if not url.startswith(("http://", "https://")):
            return
        if any(t["url"].rstrip("/") == url.rstrip("/") for t in D["tiles"]):
            self.say("Already on your start page")
            return
        host = (urlparse(url).hostname or url).replace("www.", "")
        name = (title or host).strip()
        name = name if len(name) <= 14 else host
        col = QColor.fromHsv(sum(map(ord, host)) % 360, 150, 255).name()
        D["tiles"].append({"name": name, "url": url, "color": col})
        save()
        self.say("Added to start page")

    def reset_tiles(self):
        D["tiles"] = [dict(t) for t in DEFAULT_TILES]
        save()
        self.refresh_start_pages()
        self.say("Default bookmarks restored")

    def refresh_start_pages(self):
        for t in self.tabs:
            v = t["view"]
            if v.url().host() == "cdg.start":
                v.setHtml(self.start_html(), QUrl("https://cdg.start/"))

    def go_search(self, q):
        if q.strip() and self.current:
            self.select_view(self.current)
            self.current.setUrl(QUrl(self.search_url(q)))
            self.current.setFocus()

    def suggest_rows(self, text):
        s = suggestions(text)
        rows = []
        if s["sites"]:
            rows.append({"k": "head", "label": "Recent sites"})
            for h in s["sites"]:
                host = (h.get("host") or "")
                bare = host[4:] if host.startswith("www.") else host
                rows.append({"k": "site", "label": h.get("title") or bare, "sub": bare, "val": h["url"],
                             "host": host.lower()})
        if s["searches"]:
            rows.append({"k": "head", "label": "Recent searches"})
            rows += [{"k": "search", "label": x, "val": x} for x in s["searches"]]
        if s["rec"]:
            rows.append({"k": "head", "label": "Recommended searches"})
            rows += [{"k": "rec", "label": x, "val": x} for x in s["rec"]]
        return rows

    # ---------- CDG accounts
    def switch_account(self, acct, copy_current=False):
        """Switch to an account (or None for guest). Each account has its own saved data."""
        global CUR
        save()
        first = acct is not None and not (DIR / f"acct_{safe_id(acct['id'])}.json").exists()
        CUR = acct
        write_session()
        if first and copy_current:
            save()  # a brand-new account starts from what you have right now
        else:
            load_data()
        for t in self.tabs:
            t["space"] = D["space"]
            t["chip"].setVisible(True)
        self.restyle()
        self.apply_layout()
        self.coin.set_coins(D["coins"])
        self.address.set_engine_name(D["engine"])
        self.avatar.update()
        self.sync_adblock()
        self.refresh_start_pages()
        self.rebuild_later()
        if acct is None:
            self.say("Signed out - back to guest data")

    def account_submit(self, mode, ident, pw, pw2):
        ident = ident.strip()
        if not ident or not pw:
            return "Enter a username (or email) and a password."
        if "@" in ident:
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", ident):
                return "That email doesn't look right."
            if ident.rsplit("@", 1)[1].lower() in GOOGLE_DOMAINS:
                return "That's a Google address - use Continue with Google instead."
            kind = "email"
        else:
            if not re.fullmatch(r"[A-Za-z0-9_.-]{3,24}", ident):
                return "Usernames are 3-24 letters, numbers, dots, dashes or underscores."
            kind = "username"
        key = ident.lower()
        users = users_load()
        if mode == "create":
            if key in users:
                return "That name is already taken on this device."
            if len(pw) < 6:
                return "Use at least 6 characters for the password."
            if pw != pw2:
                return "The passwords don't match."
            salt = os.urandom(16)
            users[key] = {"id": "u_" + uuid.uuid4().hex[:16], "name": ident, "kind": kind,
                          "salt": salt.hex(), "hash": pw_hash(pw, salt)}
            users_save(users)
        else:
            u = users.get(key)
            if not u or not hmac.compare_digest(pw_hash(pw, bytes.fromhex(u["salt"])), u["hash"]):
                return "Wrong username/email or password."
        u = users[key]
        self.switch_account({"id": u["id"], "name": u["name"], "provider": u["kind"]}, copy_current=(mode == "create"))
        self.say("Signed in as " + u["name"])
        return None

    def set_acct_mode(self, mode):
        self.acct_mode = mode
        self.rebuild_later()

    def start_social(self, provider):
        cfg = oauth_cfg()
        if not cfg["google_id" if provider == "google" else "github_id"]:
            how = ("Create a 'Desktop app' OAuth client in Google Cloud and add its ID" if provider == "google"
                   else "Register a GitHub OAuth app (enable Device Flow) and add its client ID")
            self.oauth_err = (f"{provider.title()} sign-in isn't set up yet. {how} to {OAUTH} as "
                              '{"google_client_id": "...", "google_client_secret": "...", "github_client_id": "..."}')
            self.rebuild_later()
            return
        self._oauth_run += 1
        self.oauth, self.oauth_err = {"provider": provider, "code": "", "url": ""}, ""
        threading.Thread(target=google_flow if provider == "google" else github_flow,
                         args=(self, cfg, self._oauth_run), daemon=True).start()
        self.rebuild_later()

    def cancel_social(self):
        self._oauth_run += 1
        self.oauth, self.oauth_err = None, ""
        self.rebuild_later()

    def on_oauth(self, kind, d):
        if d.get("run") != self._oauth_run:
            return
        if kind == "open":
            QDesktopServices.openUrl(QUrl(d["url"]))
        elif kind == "code":
            if self.oauth is not None:
                self.oauth.update(code=d["code"], url=d["url"])
            QDesktopServices.openUrl(QUrl(d["url"]))
            self.rebuild_later()
        elif kind == "done":
            self.oauth = None
            self.switch_account({"id": d["id"], "name": d["name"], "provider": d["provider"]}, copy_current=True)
            self.say("Signed in as " + d["name"])
        elif kind == "error":
            self.oauth, self.oauth_err = None, d.get("msg", "Sign-in failed.")
            self.rebuild_later()

    def add_social_tiles(self):
        have = {(urlparse(t["url"]).hostname or "").replace("www.", "") for t in D["tiles"]}
        added = 0
        for n, u, c in SOCIAL_TILES:
            if (urlparse(u).hostname or "").replace("www.", "") not in have:
                D["tiles"].append({"name": n, "url": u, "color": c})
                added += 1
        save()
        self.refresh_start_pages()
        self.say(f"Added {added} social bookmarks" if added else "Social bookmarks already there")

    def check_codecs(self, cb, view=None):
        view = view or self.current or (self.tabs[0]["view"] if self.tabs else None)
        if view is None:
            cb("Open a tab first.")
            return

        def got(res):
            try:
                r = json.loads(res)
            except Exception:
                cb("Couldn't check right now.")
                return
            ok = lambda k: bool(r.get(k))
            self._h264 = ok("h264") and ok("aac")
            msg = "  ".join(f"{n}: {'yes' if ok(k) else 'NO'}" for n, k in
                            (("H.264", "h264"), ("AAC", "aac"), ("VP9", "vp9"), ("Opus", "opus")))
            if not self._h264:
                msg += ("  -  TikTok and Instagram videos need H.264 + AAC. The pip version of Qt WebEngine is built "
                        "without them and the app can't switch them on. Use Menu > Open in default browser "
                        "for those pages.")
            cb(msg)
        view.page().runJavaScript(CODEC_JS, got)

    # ---------- ad blocker
    def sync_adblock(self):
        self.adblock.enabled = bool(D["adblock"])
        self.adblock.allow = frozenset(D["adblock_allow"])
        col = self.profile.scripts()
        for sc in col.find("cdg-adblock"):
            col.remove(sc)
        if D["adblock"]:
            sc = QWebEngineScript()
            sc.setName("cdg-adblock")
            sc.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
            sc.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
            sc.setRunsOnSubFrames(True)
            sc.setSourceCode(AD_JS.replace("__ALLOW__", json.dumps(list(D["adblock_allow"]))))
            col.insert(sc)
        if hasattr(self, "shield"):
            self.shield.update()

    def set_adblock(self, on):
        D["adblock"] = bool(on)
        self.sync_adblock()
        save()
        self.say("Ad blocker " + ("on" if on else "off"))
        if self.current is not None and self.current.url().host() not in ("", "cdg.start"):
            self.current.reload()

    def toggle_site_adblock(self, host):
        if host in D["adblock_allow"]:
            D["adblock_allow"].remove(host)
            self.say("Ad blocker resumed on " + host)
        else:
            D["adblock_allow"].append(host)
            self.say("Ad blocker paused on " + host)
        self.sync_adblock()
        save()
        if self.current is not None:
            self.current.reload()

    def adblock_menu(self):
        on = bool(D["adblock"])
        cur = self.current
        host = cur.url().host().lower() if cur is not None else ""
        host = host[4:] if host.startswith("www.") else host
        web = bool(host) and host != "cdg.start" and cur.url().scheme() in ("http", "https")
        paused = host in D["adblock_allow"]
        site = ("Resume on " if paused else "Pause on ") + (host if web else "this site")
        items = [MI("Ad blocker", lambda: self.set_adblock(not on), True, "On" if on else "Off"),
                 MI(site, lambda: self.toggle_site_adblock(host), web and on), SEP,
                 MI(f"Blocked this session: {self.adblock.n:,}", lambda: None, False),
                 MI(f"{len(self.adblock.domains):,} rules loaded", lambda: None, False),
                 MI("Update filter lists", self.update_adlists)]
        popup_menu(items, self.shield.mapToGlobal(self.shield.rect().bottomLeft()))

    def ad_sync(self):
        n = self.adblock.n
        if n != self._ad_seen:
            D["blocked"] += n - self._ad_seen
            self._ad_seen, self._ad_dirty = n, True
            self.shield.n = n
            self.shield.update()
        if self._ad_dirty and time.time() - self._ad_saved > 30:
            save()
            self._ad_dirty, self._ad_saved = False, time.time()

    def update_adlists(self):
        self.say("Updating filter lists...")
        threading.Thread(target=download_lists, args=(self,), daemon=True).start()

    def on_adlist(self, d):
        if not d.get("ok"):
            self.say("Couldn't download the filter lists")
            return
        doms = set(d["domains"]) - NEVER_BLOCK
        try:
            (DIR / "adblock_domains.txt").write_text("\n".join(sorted(doms)))
        except Exception:
            pass
        self.adblock.domains = frozenset(BUILTIN_AD_DOMAINS | doms)
        self.say(f"Ad blocker updated - {len(self.adblock.domains):,} rules")
        self.rebuild_later()

    def go_home(self):
        if self.current:
            self.select_view(self.current)
            self.open_home(self.current)

    def go(self, text):
        if text.strip() and self.current:
            self.select_view(self.current)
            self.current.setUrl(QUrl(self.to_url(text)))
            self.current.setFocus()

    def nav(self, what):
        if not self.current:
            return
        self.select_view(self.current)
        getattr(self.current, what)()

    # ---------- coins & achievements
    def add_coins(self, n):
        D["coins"] += n
        self.coin.set_coins(D["coins"])

    def award(self, aid):
        if not D["achievements_on"] or aid in D["unlocked"]:
            return
        D["unlocked"].append(aid)
        a = ACH[aid]
        self.add_coins(a["coins"])
        self.say(f"{a['name']}  +{a['coins']} CDG")
        save()

    def on_load(self, view, ok):
        u = view.url()
        url = u.toString()
        if not ok or not url.startswith("http") or u.host() == "cdg.start" or url == view.last_url:
            return
        view.last_url = url
        record_visit(url, view.title())
        if not self._codec_asked and any(h in u.host() for h in SOCIAL_HOSTS):
            self._codec_asked = True
            self.check_codecs(lambda _m: self._h264 is False and self.say("Videos may not play here. Menu > Open in default browser"), view)
        D["visits"] += 1
        v = D["visits"]
        if D["achievements_on"]:
            if v >= 1: self.award("first_steps")
            if v >= 10: self.award("explorer")
            if v >= 50: self.award("marathon")
            if v % 5 == 0:
                self.add_coins(2)
        save()

    # ---------- cookies
    def on_cookie_added(self, c):
        flags = [n for n, on in (("HttpOnly", c.isHttpOnly()), ("Secure", c.isSecure()), ("Session", c.isSessionCookie())) if on]
        self.cookies[(str(c.domain()), bytes(c.name()).decode(errors="ignore"), c.path())] = ", ".join(flags)

    def on_cookie_removed(self, c):
        self.cookies.pop((str(c.domain()), bytes(c.name()).decode(errors="ignore"), c.path()), None)

    def cookie_text(self):
        if not self.cookies:
            return "(no cookies yet - visit some websites!)"
        lines = [f"{d}   {n}" + (f"   [{f}]" if f else "") for (d, n, _p), f in sorted(self.cookies.items())]
        return "\n".join(lines)

    # ---------- shop logic
    def owned_themes(self):
        names = ["Neon Night"]
        for sid in D["owned"]:
            if sid in SHOP and SHOP[sid]["kind"] == "theme":
                names.append(SHOP[sid]["value"])
        return names

    def has(self, sid):
        return sid in D["owned"]

    def equip(self, theme):
        D["theme"], D["accent"] = theme, ""
        self.restyle()
        self.award("stylist")
        self.rebuild_later()

    def buy(self, sid):
        item = SHOP[sid]
        if self.has(sid):
            return
        if D["coins"] < item["price"]:
            self.say("Not enough CDG coins yet")
            return
        D["coins"] -= item["price"]
        D["owned"].append(sid)
        for k, key in (("pill_buttons", "pill"), ("gradient_bar", "gradient"), ("orbs", "orbs"), ("rainbow_accent", "rainbow")):
            if sid == k:
                D[key] = True
        if item["kind"] == "theme":
            D["theme"], D["accent"] = item["value"], ""
        self.coin.set_coins(D["coins"])
        self.restyle()
        self.award("shopper")
        self.say(f"Purchased {item['name']}!")
        self.rebuild_later()

    def set_flag(self, key, on):
        D[key] = on
        self.restyle()

    def rebuild_later(self):
        QTimer.singleShot(0, self.rebuild_panels)

    def rebuild_panels(self):
        builders = {"settings": self.build_settings, "shop": self.build_shop, "build": self.build_layout,
                    "account": self.build_account}
        for name in ("settings", "shop", "build", "account"):
            sa = self.pages[name]
            v = sa.verticalScrollBar().value()
            sa.setWidget(builders[name]())
            sa.widget().setAutoFillBackground(False)
            QTimer.singleShot(0, lambda s=sa, val=v: s.verticalScrollBar().setValue(val))

    def show_panel(self, name):
        if self.mode == name:
            if self.current:
                self.select_view(self.current)
            return
        self.mode = name
        self.rebuild_panels()
        self.stack.setCurrentWidget(self.pages[name])
        self.fade_in(self.pages[name])
        for t in self.tabs:
            t["chip"].sel = False
            t["chip"].update()
        if name == "settings":
            pass

    # ---------- panel builders
    def _host(self, title_text):
        host = QWidget()
        host.setAutoFillBackground(False)
        outer = QVBoxLayout(host)
        outer.setContentsMargins(36, 22, 36, 36)
        outer.setSpacing(16)
        t = QLabel(title_text)
        t.setObjectName("h1")
        outer.addWidget(t)
        return host, outer

    def _card(self, outer, heading):
        f = QFrame()
        f.setObjectName("card")
        lay = QVBoxLayout(f)
        lay.setContentsMargins(22, 18, 22, 20)
        lay.setSpacing(14)
        if heading:
            h = QLabel(heading)
            h.setObjectName("h2")
            lay.addWidget(h)
        outer.addWidget(f)
        return lay

    def _row(self, label, *items, stretch_last=False):
        h = QHBoxLayout()
        h.setSpacing(8)
        l = QLabel(label)
        l.setFixedWidth(150)
        h.addWidget(l)
        for i, it in enumerate(items):
            if isinstance(it, QHBoxLayout):
                h.addLayout(it)
            else:
                h.addWidget(it, 1 if (stretch_last and i == len(items) - 1) else 0)
        if not stretch_last:
            h.addStretch(1)
        return h

    def _locked(self):
        b = PillButton("Unlock in Shop")
        b.clicked.connect(lambda: self.show_panel("shop"))
        return b

    def _feature(self, lay, label, sid, key):
        if self.has(sid):
            tg = Toggle(D[key])
            tg.toggled.connect(lambda on, k=key: self.set_flag(k, on))
            lay.addLayout(self._row(label, tg))
        else:
            lay.addLayout(self._row(label, self._locked()))

    def build_settings(self):
        host, outer = self._host("Settings")

        c = self._card(outer, "Appearance")
        owned = self.owned_themes()
        names = list(THEMES)
        for ri, group in enumerate((names[:4], names[4:])):
            chips = QHBoxLayout()
            chips.setSpacing(8)
            for name in group:
                ok = name in owned
                ch = Chip(name, selected=(name == D["theme"]), dot=QColor(THEMES[name]["accent"]), locked=not ok)
                ch.clicked.connect(lambda n=name, ok=ok: self.equip(n) if ok else self.show_panel("shop"))
                chips.addWidget(ch)
            chips.addStretch(1)
            c.addLayout(self._row("Theme" if ri == 0 else "", chips, stretch_last=True))

        if self.has("accent_picker"):
            sw = QHBoxLayout()
            sw.setSpacing(2)
            cur = D["accent"]
            for col in SWATCHES:
                s = Swatch(col, cur.lower() == col)
                s.clicked.connect(lambda col=col: self.set_accent(col))
                sw.addWidget(s)
            sw.addStretch(1)
            c.addLayout(self._row("Accent color", sw, stretch_last=True))
            hue = Slider(0, 359, max(QColor(cur or THEMES[D["theme"]]["accent"]).hue(), 0), rainbow=True)
            hue.changed.connect(lambda v: self.set_accent(QColor.fromHsv(v, 200, 255).name(), rebuild=False))
            c.addLayout(self._row("Custom hue", hue, stretch_last=True))
        else:
            c.addLayout(self._row("Accent color", self._locked()))

        rad = Slider(0, 28, D["radius"])
        rad.changed.connect(lambda v: self.set_flag("radius", v))
        c.addLayout(self._row("Corner roundness", rad, stretch_last=True))
        wrad = Slider(0, 40, D["win_radius"])
        wrad.changed.connect(lambda v: self.set_flag("win_radius", v))
        c.addLayout(self._row("Window corners", wrad, stretch_last=True))
        self._feature(c, "Pill buttons", "pill_buttons", "pill")
        self._feature(c, "Gradient toolbar", "gradient_bar", "gradient")
        self._feature(c, "Floating orbs", "orbs", "orbs")
        self._feature(c, "Rainbow accent", "rainbow_accent", "rainbow")

        c = self._card(outer, "Browsing")
        home = QLineEdit(D["home"])
        home.setObjectName("input")
        home.setPlaceholderText("start (CDG start page) or any address")
        attach_text_menu(home)

        def set_home():
            t = home.text().strip()
            D["home"] = "start" if t in ("", "start") else self.to_url(t)
            home.setText(D["home"])
            save()
        home.editingFinished.connect(set_home)
        c.addLayout(self._row("Home page", home, stretch_last=True))
        chat = QLineEdit(D.get("chat_url", ""))
        chat.setObjectName("input")
        chat.setPlaceholderText("blank = run CDG Chat on this computer, or http://host:8765")
        attach_text_menu(chat)

        def set_chat():
            D["chat_url"] = chat.text().strip()
            save()
        chat.editingFinished.connect(set_chat)
        c.addLayout(self._row("Chat server", chat, stretch_last=True))
        eng = QHBoxLayout()
        eng.setSpacing(8)
        for name in ENGINES:
            ch = Chip(name, selected=(name == D["engine"]))
            ch.clicked.connect(lambda n=name: self.set_engine(n))
            eng.addWidget(ch)
        eng.addStretch(1)
        c.addLayout(self._row("Search engine", eng, stretch_last=True))
        rb = PillButton("Restore default bookmarks")
        rb.clicked.connect(self.reset_tiles)
        c.addLayout(self._row("Start page", rb))
        sb = PillButton("Add social media bookmarks")
        sb.clicked.connect(self.add_social_tiles)
        c.addLayout(self._row("Social media", sb))
        cb = PillButton("Check video support")
        res = QLabel("")
        res.setObjectName("muted")
        res.setWordWrap(True)

        def show_res(txt, lab=res):
            try:
                lab.setText(txt)
            except RuntimeError:
                pass
        cb.clicked.connect(lambda: self.check_codecs(show_res))
        vr = QHBoxLayout()
        vr.setSpacing(10)
        vr.addWidget(cb)
        vr.addWidget(res, 1)
        c.addLayout(self._row("Video support", vr))
        adt = Toggle(D["adblock"])
        adt.toggled.connect(self.set_adblock)
        c.addLayout(self._row("Ad blocker", adt))
        ub = PillButton("Update filter lists")
        ub.clicked.connect(self.update_adlists)
        ulab = QLabel(f"{len(self.adblock.domains):,} rules  -  {D['blocked']:,} blocked so far")
        ulab.setObjectName("muted")
        ur = QHBoxLayout()
        ur.setSpacing(10)
        ur.addWidget(ub)
        ur.addWidget(ulab, 1)
        c.addLayout(self._row("Filter lists", ur))

        c = self._card(outer, "Cookie Jar")
        info = QLabel("Cookies are saved automatically, so your logins stay between sessions.")
        info.setObjectName("muted")
        c.addWidget(info)
        out = QPlainTextEdit()
        out.setReadOnly(True)
        out.setFixedHeight(150)
        attach_text_menu(out)
        out.setPlainText(self.cookie_text())
        c.addWidget(out)
        count = QLabel(f"{len(self.cookies)} cookies stored")
        count.setObjectName("muted")
        c.addWidget(count)
        btns = QHBoxLayout()
        b1 = PillButton("Refresh")
        b2 = PillButton("Clear all cookies", primary=True)

        def refresh():
            out.setPlainText(self.cookie_text())
            count.setText(f"{len(self.cookies)} cookies stored")
            self.award("cookie")

        def clear():
            self.profile.cookieStore().deleteAllCookies()
            self.cookies.clear()
            out.setPlainText(self.cookie_text())
            count.setText("0 cookies stored")
            self.say("All cookies cleared")
        b1.clicked.connect(refresh)
        b2.clicked.connect(clear)
        btns.addWidget(b1)
        btns.addWidget(b2)
        btns.addStretch(1)
        c.addLayout(btns)
        QTimer.singleShot(0, lambda: self.award("cookie"))

        c = self._card(outer, "Achievements")
        tg = Toggle(D["achievements_on"])
        tg.toggled.connect(lambda on: (D.__setitem__("achievements_on", on), save(),
                                       self.say("Achievements " + ("on" if on else "off"))))
        c.addLayout(self._row("Earn CDG coins", tg))
        for aid, a in ACH.items():
            done = aid in D["unlocked"]
            dot = P["acc"].name() if done else P["muted"].name()
            l = QLabel(f"<span style='color:{dot}'>&#9679;</span>&nbsp; <b>{a['name']}</b> "
                       f"<span style='color:{P['muted'].name()}'>{a['desc']} &middot; +{a['coins']} CDG</span>")
            l.setTextFormat(Qt.TextFormat.RichText)
            c.addWidget(l)
        outer.addStretch(1)
        return host

    def set_accent(self, col, rebuild=True):
        D["accent"] = col
        self.restyle()
        self.award("stylist")
        if rebuild:
            self.rebuild_later()

    def set_engine(self, name):
        D["engine"] = name
        save()
        self.address.set_engine_name(name)
        self.refresh_start_pages()
        self.rebuild_later()

    def engine_menu(self):
        items = [MI("Search with", lambda: None, False), SEP]
        for name in ENGINES:
            items.append(MI(name, lambda n=name: (self.set_engine(n), self.say("Search engine: " + n)),
                            True, "\u2713" if name == D["engine"] else ""))
        gp = self.address.mapToGlobal(self.address.rect().bottomLeft())
        gp.setX(gp.x() + 6)
        gp.setY(gp.y() + 4)
        popup_menu(items, gp)

    def build_account(self):
        host, outer = self._host("CDG Account")
        if CUR:
            c = self._card(outer, None)
            row = QHBoxLayout()
            row.setSpacing(16)
            row.addWidget(Avatar(CUR["name"], 64))
            col = QVBoxLayout()
            col.setSpacing(2)
            nm = QLabel(CUR["name"])
            nm.setObjectName("h3")
            pv = QLabel(PROVIDER_NAMES.get(CUR["provider"], "CDG account"))
            pv.setObjectName("muted")
            col.addStretch(1)
            col.addWidget(nm)
            col.addWidget(pv)
            col.addStretch(1)
            row.addLayout(col, 1)
            so = PillButton("Sign out", primary=True)
            so.clicked.connect(lambda: self.switch_account(None))
            row.addWidget(so)
            c.addLayout(row)
            info = QLabel("Your theme, coins, bookmarks, history and layout are saved to this account on this device. "
                          "Signing out switches back to your guest data.")
            info.setObjectName("muted")
            info.setWordWrap(True)
            c.addWidget(info)
            outer.addStretch(1)
            return host

        c = self._card(outer, "Sign in to CDG")
        intro = QLabel("Your theme, coins, bookmarks and history follow your account. "
                       "Google and GitHub sign-ins only share your name - never your email.")
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        c.addWidget(intro)
        if self.oauth:
            prov = "Google" if self.oauth["provider"] == "google" else "GitHub"
            if self.oauth.get("code"):
                code = QLabel(self.oauth["code"])
                code.setObjectName("h1")
                c.addWidget(code)
                t = QLabel(f"Enter this code at {self.oauth['url']} - it's open in your browser now.")
            else:
                t = QLabel(f"Finish signing in with {prov} in your browser window...")
            t.setObjectName("muted")
            t.setWordWrap(True)
            c.addWidget(t)
            cancel = PillButton("Cancel")
            cancel.clicked.connect(self.cancel_social)
            cr = QHBoxLayout()
            cr.addWidget(cancel)
            cr.addStretch(1)
            c.addLayout(cr)
        else:
            row = QHBoxLayout()
            row.setSpacing(10)
            g = ProviderButton("google", "Continue with Google")
            g.clicked.connect(lambda: self.start_social("google"))
            gh = ProviderButton("github", "Continue with GitHub")
            gh.clicked.connect(lambda: self.start_social("github"))
            row.addWidget(g)
            row.addWidget(gh)
            row.addStretch(1)
            c.addLayout(row)
            if self.oauth_err:
                lab = QLabel(self.oauth_err)
                lab.setWordWrap(True)
                lab.setStyleSheet("color: #ff7a7a; font-size: 12px;")
                c.addWidget(lab)

        c = self._card(outer, "Or use a CDG username or email")
        note = QLabel("No email needed - just pick a username. If you'd rather use an email, any non-Google address works.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        c.addWidget(note)
        modes = QHBoxLayout()
        modes.setSpacing(8)
        for label, key in (("Sign in", "signin"), ("Create account", "create")):
            ch = Chip(label, selected=(self.acct_mode == key))
            ch.clicked.connect(lambda k=key: self.set_acct_mode(k))
            modes.addWidget(ch)
        modes.addStretch(1)
        c.addLayout(modes)
        user = QLineEdit()
        user.setObjectName("input")
        user.setPlaceholderText("Username or email")
        attach_text_menu(user)
        pw = QLineEdit()
        pw.setObjectName("input")
        pw.setPlaceholderText("Password")
        pw.setEchoMode(QLineEdit.EchoMode.Password)
        c.addLayout(self._row("Username or email", user, stretch_last=True))
        c.addLayout(self._row("Password", pw, stretch_last=True))
        pw2 = None
        if self.acct_mode == "create":
            pw2 = QLineEdit()
            pw2.setObjectName("input")
            pw2.setPlaceholderText("Repeat password")
            pw2.setEchoMode(QLineEdit.EchoMode.Password)
            c.addLayout(self._row("Confirm password", pw2, stretch_last=True))
        errl = QLabel("")
        errl.setWordWrap(True)
        errl.setStyleSheet("color: #ff7a7a; font-size: 12px;")
        errl.setVisible(False)
        c.addWidget(errl)

        def submit():
            err = self.account_submit(self.acct_mode, user.text(), pw.text(), pw2.text() if pw2 else "")
            if err:
                errl.setText(err)
                errl.setVisible(True)
        go = PillButton("Create account" if self.acct_mode == "create" else "Sign in", primary=True)
        go.clicked.connect(submit)
        for w in (user, pw, pw2):
            if w is not None:
                w.returnPressed.connect(submit)
        br = QHBoxLayout()
        br.addWidget(go)
        br.addStretch(1)
        c.addLayout(br)
        outer.addStretch(1)
        return host

    def build_shop(self):
        host, outer = self._host("CDG Shop")
        bal = QLabel(f"You have {D['coins']} CDG coins"
                     + ("" if D["achievements_on"] else "  (achievements are off - turn them on in Settings)"))
        bal.setObjectName("h2")
        outer.addWidget(bal)
        grid = QGridLayout()
        grid.setSpacing(16)
        for n, (sid, item) in enumerate(SHOP.items()):
            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(20, 18, 20, 18)
            cl.setSpacing(10)
            if item["kind"] == "theme":
                cl.addWidget(ThemePreview(item["value"]))
            t = QLabel(item["name"])
            t.setObjectName("h3")
            d = QLabel(item["desc"])
            d.setObjectName("muted")
            d.setWordWrap(True)
            cl.addWidget(t)
            cl.addWidget(d)
            cl.addStretch(1)
            bottom = QHBoxLayout()
            if self.has(sid):
                if item["kind"] == "theme":
                    eq = D["theme"] == item["value"]
                    b = PillButton("Equipped" if eq else "Equip", primary=not eq)
                    b.set_off(eq)
                    b.clicked.connect(lambda th=item["value"]: self.equip(th))
                else:
                    b = PillButton("Owned - toggle in Settings")
                    b.set_off(True)
                bottom.addWidget(b)
            else:
                price = QLabel(f"{item['price']} CDG")
                price.setObjectName("h3")
                b = PillButton("Buy", primary=True)
                b.set_off(D["coins"] < item["price"])
                b.clicked.connect(lambda s=sid: self.buy(s))
                bottom.addWidget(price)
                bottom.addStretch(1)
                bottom.addWidget(b)
            cl.addLayout(bottom)
            grid.addWidget(card, n // 2, n % 2)
        outer.addLayout(grid)
        outer.addStretch(1)
        return host


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("CDG Browse")
    app.setOrganizationName("CDG")
    app.setApplicationVersion("2.1.0")
    app.setStyle("Fusion")
    app.aboutToQuit.connect(lambda: CHAT_PROC and CHAT_PROC.terminate())
    win = Win()
    win.apply_margins()
    win.setWindowOpacity(0.0)
    win.show()
    _open = QPropertyAnimation(win, b"windowOpacity")
    _open.setDuration(420)
    _open.setStartValue(0.0)
    _open.setEndValue(1.0)
    _open.setEasingCurve(QEasingCurve.Type.OutCubic)
    _open.start()
    sys.exit(app.exec())
