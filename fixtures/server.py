#!/usr/bin/env python3
"""Q6 fixtures F1-F4 on one port, namespaced by host: <ns>.localhost:5320.

Pages are plain HTML + inline JS (client-side rendering like the console).
Harness-only admin API lives under /__admin/ and needs the X-Admin-Token header.
All credentials and codes here are dummy values generated per namespace.
"""
import base64
import html
import json
import os
import secrets
import sys
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

PORT = int(os.environ.get("FIXTURE_PORT", "5320"))
ADMIN_TOKEN = os.environ["FIXTURE_ADMIN_TOKEN"]
LOCK = threading.Lock()
NS = {}  # ns -> {"kind", "config", "sessions": {sid: user}, "log": [...]}

BOTS = [
    {"id": "b1", "name": "alpha-trend", "status": "Running"},
    {"id": "b2", "name": "beta-revert", "status": "Running"},
    {"id": "b3", "name": "gamma-carry", "status": "Stopped"},
    {"id": "b4", "name": "delta-breakout", "status": "Error"},
]

BASE_POSITIONS = {
    "b1": [
        {"symbol": "BTCUSDT", "side": "LONG", "qty": "0.120", "avg_price": "61250.5"},
        {"symbol": "ETHUSDT", "side": "SHORT", "qty": "1.500", "avg_price": "2410.2"},
        {"symbol": "SOLUSDT", "side": "LONG", "qty": "30.00", "avg_price": "142.35"},
        {"symbol": "XRPUSDT", "side": "LONG", "qty": "2500", "avg_price": "0.5821"},
        {"symbol": "ADAUSDT", "side": "SHORT", "qty": "4000", "avg_price": "0.3375"},
    ],
    "b2": [
        {"symbol": "BTCUSDT", "side": "SHORT", "qty": "0.050", "avg_price": "61980.0"},
        {"symbol": "BNBUSDT", "side": "LONG", "qty": "3.200", "avg_price": "566.40"},
        {"symbol": "DOGEUSDT", "side": "LONG", "qty": "12000", "avg_price": "0.1188"},
        {"symbol": "LINKUSDT", "side": "SHORT", "qty": "80.0", "avg_price": "13.57"},
        {"symbol": "AVAXUSDT", "side": "LONG", "qty": "45.0", "avg_price": "27.84"},
    ],
    "b3": [
        {"symbol": "ETHUSDT", "side": "LONG", "qty": "0.800", "avg_price": "2388.0"},
        {"symbol": "DOTUSDT", "side": "LONG", "qty": "150", "avg_price": "5.912"},
        {"symbol": "TRXUSDT", "side": "SHORT", "qty": "9000", "avg_price": "0.1563"},
    ],
    "b4": [
        {"symbol": "SOLUSDT", "side": "SHORT", "qty": "12.0", "avg_price": "145.10"},
        {"symbol": "LTCUSDT", "side": "LONG", "qty": "6.00", "avg_price": "71.25"},
        {"symbol": "ATOMUSDT", "side": "LONG", "qty": "210", "avg_price": "6.480"},
    ],
}


def ns_of(host):
    host = (host or "").split(":")[0]
    if host.endswith(".localhost"):
        return host[: -len(".localhost")]
    return None


def page(title, body, script=""):
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>body{{font-family:-apple-system,sans-serif;margin:24px;max-width:900px}}table{{border-collapse:collapse}}
td,th{{border:1px solid #ccc;padding:4px 10px;text-align:left}}.badge{{padding:2px 8px;border-radius:8px;font-size:12px}}
.Running{{background:#d4f7d4}}.Stopped{{background:#eee}}.Error{{background:#fdd}}label{{display:block;margin:8px 0}}</style>
</head><body>{body}<script>{script}</script></body></html>"""


def positions_for(ns_state, bot_id):
    rows = [dict(r) for r in BASE_POSITIONS[bot_id]]
    cfg = ns_state["config"]
    plant = cfg.get("plant")
    if plant and plant["bot"] == bot_id:
        for r in rows:
            if r["symbol"] == plant["symbol"]:
                r[plant["field"]] = plant["actual"]
    if bot_id == cfg.get("target"):
        mode = cfg.get("mode")
        if mode == "bug-value":
            rows[1]["qty"] = cfg.get("bug_qty", "9.999")
        elif mode == "bug-side":
            rows[0]["side"] = "SHORT" if rows[0]["side"] == "LONG" else "LONG"
        elif mode == "bug-extra":
            rows.append({"symbol": "MATICUSDT", "side": "LONG", "qty": "700", "avg_price": "0.7120"})
        elif mode == "bug-missing":
            rows = rows[:-1]
    return rows


class H(BaseHTTPRequestHandler):
    server_version = "fixture/1"

    def log_message(self, fmt, *args):
        pass

    # ---------- helpers
    def send(self, code, body, ctype="text/html; charset=utf-8", headers=None):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def jsend(self, code, obj, headers=None):
        self.send(code, json.dumps(obj), "application/json", headers)

    def body_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            return json.loads(raw or b"{}")
        except Exception:
            return {}

    def cookie(self, name):
        c = SimpleCookie(self.headers.get("Cookie") or "")
        return c[name].value if name in c else None

    def basic(self):
        h = self.headers.get("Authorization") or ""
        if not h.startswith("Basic "):
            return None, None
        try:
            u, p = base64.b64decode(h[6:]).decode().split(":", 1)
            return u, p
        except Exception:
            return None, None

    def record(self, st, event, **kw):
        st["log"].append({"t": time.time(), "event": event, "path": self.path, **kw})

    # ---------- admin
    def admin(self, method):
        if self.headers.get("X-Admin-Token") != ADMIN_TOKEN:
            return self.jsend(403, {"error": "forbidden"})
        parts = urlparse(self.path).path.strip("/").split("/")  # __admin, ns[, name[, mode]]
        with LOCK:
            if method == "POST" and len(parts) == 2 and parts[1] == "ns":
                b = self.body_json()
                NS[b["ns"]] = {"kind": b["kind"], "config": b.get("config", {}), "sessions": {}, "log": []}
                return self.jsend(200, {"ok": True})
            if len(parts) >= 3 and parts[1] == "ns" and parts[2] in NS:
                st = NS[parts[2]]
                if method == "GET":
                    return self.jsend(200, {"kind": st["kind"], "config": st["config"], "log": st["log"],
                                            "sessions": st["sessions"]})
                if method == "POST" and len(parts) == 4 and parts[3] == "mode":
                    st["config"]["mode"] = self.body_json().get("mode", "normal")
                    return self.jsend(200, {"ok": True, "mode": st["config"]["mode"]})
        return self.jsend(404, {"error": "not found"})

    # ---------- routing
    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def route(self, method):
        path = urlparse(self.path).path
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if path.startswith("/__admin/"):
            return self.admin(method)
        ns = ns_of(self.headers.get("Host"))
        with LOCK:
            st = NS.get(ns)
        if not st:
            return self.send(404, page("Not found", "<h1>Unknown site</h1>"))
        kind = st["kind"]
        if kind == "f1":
            return self.f1(st, method, path)
        if kind == "f2":
            return self.f2(st, method, path)
        if kind in ("f3", "f4"):
            return self.dash(st, method, path)
        if kind == "h1":
            return self.h1(st, method, path)
        if kind == "h2":
            return self.h2(st, method, path)
        if kind == "h3":
            return self.h3(st, method, path)
        return self.send(404, "unknown kind")

    # ---------- F1: console-like login persistence (localStorage creds + Basic + session cookie)
    def f1(self, st, method, path):
        cfg = st["config"]
        if method == "GET" and path == "/":
            body = """<h1>Bot console</h1><p>Register a bot connection.</p>
<form id="f"><label>Server URL <input name="url" value="http://bot.local:8080"></label>
<label>ID <input name="id" autocomplete="username"></label>
<label>Password <input name="pw" type="password" autocomplete="current-password"></label>
<button type="submit">Connect</button></form><p id="msg"></p>"""
            script = """document.getElementById('f').onsubmit=async(e)=>{e.preventDefault();
const fd=new FormData(e.target);const c={url:fd.get('url'),id:fd.get('id'),pw:fd.get('pw')};
const r=await fetch('/api/login',{method:'POST',headers:{'Authorization':'Basic '+btoa(c.id+':'+c.pw)}});
if(!r.ok){document.getElementById('msg').textContent='Login failed';return;}
localStorage.setItem('bot-connections',JSON.stringify([c]));location.href='/status';};"""
            return self.send(200, page("Bot console", body, script))
        if method == "GET" and path == "/status":
            body = """<h1>Bot status</h1><p id="out">Loading...</p><p><a href="/">Connections</a></p>"""
            script = """(async()=>{const out=document.getElementById('out');
const conns=JSON.parse(localStorage.getItem('bot-connections')||'[]');
if(!conns.length){out.textContent='No bot connection registered. Please register a connection first.';return;}
const c=conns[0];const r=await fetch('/api/status',{headers:{'Authorization':'Basic '+btoa(c.id+':'+c.pw)}});
if(r.status===401){out.textContent='Session expired. Please log in again.';return;}
const j=await r.json();out.textContent='Status code: '+j.code;})();"""
            return self.send(200, page("Bot status", body, script))
        if method == "POST" and path == "/api/login":
            u, p = self.basic()
            with LOCK:
                if u == cfg["user"] and p == cfg["password"]:
                    sid = secrets.token_hex(16)
                    st["sessions"][sid] = u
                    self.record(st, "login_ok", user=u)
                    return self.jsend(200, {"ok": True},
                                      {"Set-Cookie": f"sid={sid}; Path=/; HttpOnly; SameSite=Lax"})
                self.record(st, "login_fail", user=u)
            return self.jsend(401, {"error": "bad credentials"})
        if method == "GET" and path == "/api/status":
            u, p = self.basic()
            sid = self.cookie("sid")
            with LOCK:
                ok = (u == cfg["user"] and p == cfg["password"] and sid in st["sessions"])
                self.record(st, "status_ok" if ok else "status_denied", has_cookie=bool(sid),
                            basic_ok=(u == cfg["user"] and p == cfg["password"]))
            if ok:
                return self.jsend(200, {"code": cfg["code"]})
            return self.jsend(401, {"error": "unauthorized"})
        return self.send(404, page("Not found", "<h1>Not found</h1>"))

    # ---------- F2: three users on one origin, session cookie decides who you are
    def f2(self, st, method, path):
        users = st["config"]["users"]  # {user: {"password", "code"}}
        if method == "GET" and path == "/":
            body = """<h1>Team portal</h1><form id="f"><label>ID <input name="id"></label>
<label>Password <input name="pw" type="password"></label><button type="submit">Sign in</button></form><p id="msg"></p>"""
            script = """document.getElementById('f').onsubmit=async(e)=>{e.preventDefault();const fd=new FormData(e.target);
const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({id:fd.get('id'),pw:fd.get('pw')})});
if(!r.ok){document.getElementById('msg').textContent='Sign-in failed';return;}location.href='/me';};"""
            return self.send(200, page("Team portal", body, script))
        if method == "POST" and path == "/api/login":
            b = self.body_json()
            time.sleep(1.5)  # widen the window in which concurrent sign-ins overlap
            with LOCK:
                u = b.get("id")
                if u in users and users[u]["password"] == b.get("pw"):
                    sid = secrets.token_hex(16)
                    st["sessions"][sid] = u
                    self.record(st, "login_ok", user=u)
                    return self.jsend(200, {"ok": True},
                                      {"Set-Cookie": f"sid={sid}; Path=/; HttpOnly; SameSite=Lax"})
                self.record(st, "login_fail", user=u)
            return self.jsend(401, {"error": "bad credentials"})
        if method == "GET" and path == "/me":
            sid = self.cookie("sid")
            with LOCK:
                u = st["sessions"].get(sid)
                self.record(st, "me", user=u)
            if not u:
                return self.send(200, page("Not signed in", "<h1>Not signed in</h1><p><a href='/'>Sign in</a></p>"))
            body = (f"<h1>My page</h1><p>Signed in as <b id='who'>{html.escape(u)}</b></p>"
                    f"<p>Your code: <b id='code'>{html.escape(users[u]['code'])}</b></p>")
            return self.send(200, page("My page", body))
        return self.send(404, page("Not found", "<h1>Not found</h1>"))

    # ---------- F3/F4: console-like dashboard
    def dash(self, st, method, path):
        cfg = st["config"]
        if method == "GET" and path == "/":
            body = "<h1>Trading bots</h1><table id='bots'><thead><tr><th>Bot</th><th>Status</th></tr></thead><tbody></tbody></table>"
            script = """(async()=>{const r=await fetch('/api/bots');const bots=await r.json();
const tb=document.querySelector('#bots tbody');for(const b of bots){const tr=document.createElement('tr');
tr.innerHTML=`<td><a href="/bots/${b.link}">${b.name}</a></td><td><span class="badge ${b.status}">${b.status}</span></td>`;
tb.appendChild(tr);}})();"""
            return self.send(200, page("Trading bots", body, script))
        if method == "GET" and path == "/api/bots":
            out = []
            ids = [b["id"] for b in BOTS]
            for b in BOTS:
                link = b["id"]
                if cfg.get("mode") == "bug-nav" and b["id"] == cfg.get("target"):
                    link = ids[(ids.index(b["id"]) + 1) % len(ids)]  # row opens the wrong bot
                out.append({"name": b["name"], "status": b["status"], "link": link})
            return self.jsend(200, out)
        if method == "GET" and path.startswith("/bots/"):
            delay = 2500 if cfg.get("mode") == "slow" else 400
            body = """<p><a href="/">&larr; All bots</a></p><h1 id="title">Bot</h1><p>Status: <span id="status"></span></p>
<h2>Positions</h2><table id="positions"><thead><tr><th>Symbol</th><th>Side</th><th>Qty</th><th>Avg price</th></tr></thead><tbody></tbody></table>"""
            script = """(async()=>{const id=location.pathname.split('/').pop();
const r=await fetch('/api/bots/'+id);if(!r.ok){document.getElementById('title').textContent='Bot not found';return;}
const b=await r.json();document.getElementById('title').textContent=b.name;
document.getElementById('status').innerHTML=`<span class="badge ${b.status}">${b.status}</span>`;
await new Promise(res=>setTimeout(res,DELAY));
const tb=document.querySelector('#positions tbody');for(const p of b.positions){const tr=document.createElement('tr');
tr.innerHTML=`<td>${p.symbol}</td><td>${p.side}</td><td>${p.qty}</td><td>${p.avg_price}</td>`;tb.appendChild(tr);}})();"""
            return self.send(200, page("Bot detail", body, script.replace("DELAY", str(delay))))
        if method == "GET" and path.startswith("/api/bots/"):
            bid = path.rsplit("/", 1)[-1]
            bot = next((b for b in BOTS if b["id"] == bid), None)
            if cfg.get("mode") == "bug-404" and bid == cfg.get("target"):
                return self.jsend(500, {"error": "internal"})
            if not bot:
                return self.jsend(404, {"error": "no such bot"})
            with LOCK:
                self.record(st, "bot_detail", bot=bid)
                rows = positions_for(st, bid)
            return self.jsend(200, {"name": bot["name"], "status": bot["status"], "positions": rows})
        return self.send(404, page("Not found", "<h1>Not found</h1>"))

    # ---------- H1: heavy positions table (400 rows, page order differs from the expected file)
    def h1(self, st, method, path):
        cfg = st["config"]  # {"bots": [{id,name,status}], "target", "rows": {bot_id: [...]}}
        if method == "GET" and path == "/":
            body = "<h1>Trading bots</h1><table id='bots'><thead><tr><th>Bot</th><th>Status</th><th>Positions</th></tr></thead><tbody></tbody></table>"
            script = """(async()=>{const bots=await (await fetch('/api/bots')).json();const tb=document.querySelector('#bots tbody');
for(const b of bots){const tr=document.createElement('tr');tr.innerHTML=`<td><a href="/bots/${b.id}">${b.name}</a></td><td><span class="badge ${b.status}">${b.status}</span></td><td>${b.n}</td>`;tb.appendChild(tr);}})();"""
            return self.send(200, page("Trading bots", body, script))
        if method == "GET" and path == "/api/bots":
            return self.jsend(200, [{**b, "n": len(cfg["rows"][b["id"]])} for b in cfg["bots"]])
        if method == "GET" and path.startswith("/bots/"):
            body = """<p><a href="/">&larr; All bots</a></p><h1 id="title">Bot</h1><p>Status: <span id="status"></span></p>
<h2>Positions</h2><p id="count"></p><table id="positions"><thead><tr><th>Symbol</th><th>Side</th><th>Qty</th><th>Avg price</th><th>Mark price</th><th>uPnL</th><th>Opened</th></tr></thead><tbody></tbody></table>"""
            script = """(async()=>{const id=location.pathname.split('/').pop();const r=await fetch('/api/bots/'+id);
if(!r.ok){document.getElementById('title').textContent='Bot not found';return;}const b=await r.json();
document.getElementById('title').textContent=b.name;document.getElementById('status').innerHTML=`<span class="badge ${b.status}">${b.status}</span>`;
await new Promise(res=>setTimeout(res,300));const tb=document.querySelector('#positions tbody');
document.getElementById('count').textContent=b.positions.length+' open positions';
for(const p of b.positions){const tr=document.createElement('tr');
tr.innerHTML=`<td>${p.symbol}</td><td>${p.side}</td><td>${p.qty}</td><td>${p.avg_price}</td><td>${p.mark}</td><td>${p.upnl}</td><td>${p.opened}</td>`;tb.appendChild(tr);}})();"""
            return self.send(200, page("Bot detail", body, script))
        if method == "GET" and path.startswith("/api/bots/"):
            bid = path.rsplit("/", 1)[-1]
            bot = next((b for b in cfg["bots"] if b["id"] == bid), None)
            if not bot:
                return self.jsend(404, {"error": "no such bot"})
            with LOCK:
                self.record(st, "bot_detail", bot=bid)
            return self.jsend(200, {"name": bot["name"], "status": bot["status"], "positions": cfg["rows"][bid]})
        return self.send(404, page("Not found", "<h1>Not found</h1>"))

    # ---------- H2: long workflow across bots, tabs and a dialog
    def h2(self, st, method, path):
        cfg = st["config"]  # {"bots": [{id,name,status,uptime,max_leverage,risk,orders:[{id,symbol,side,created}]}]}
        if method == "GET" and path == "/":
            body = "<h1>Trading bots</h1><ul id='bots'></ul>"
            script = """(async()=>{const bots=await (await fetch('/api/bots')).json();const ul=document.getElementById('bots');
for(const b of bots){const li=document.createElement('li');li.innerHTML=`<a href="/bots/${b.id}">${b.name}</a>`;ul.appendChild(li);}})();"""
            return self.send(200, page("Trading bots", body, script))
        if method == "GET" and path == "/api/bots":
            return self.jsend(200, [{"id": b["id"], "name": b["name"]} for b in cfg["bots"]])
        if method == "GET" and path.startswith("/bots/"):
            body = """<p><a href="/">&larr; All bots</a></p><h1 id="title">Bot</h1>
<div role="tablist"><button role="tab" data-tab="overview">Overview</button> <button role="tab" data-tab="settings">Settings</button> <button role="tab" data-tab="orders">Orders</button></div>
<section id="panel" role="tabpanel"></section>
<dialog id="dlg"><h3>Open orders</h3><table id="orders"><thead><tr><th>Order id</th><th>Symbol</th><th>Side</th><th>Created</th></tr></thead><tbody></tbody></table><p id="empty"></p><button id="close">Close</button></dialog>"""
            script = """(async()=>{const id=location.pathname.split('/').pop();const r=await fetch('/api/bots/'+id);
if(!r.ok){document.getElementById('title').textContent='Bot not found';return;}const b=await r.json();
document.getElementById('title').textContent=b.name;const panel=document.getElementById('panel');
const show=(t)=>{document.querySelectorAll('[role=tab]').forEach(x=>x.setAttribute('aria-selected',x.dataset.tab===t));
if(t==='overview')panel.innerHTML=`<p>Status: <b>${b.status}</b></p><p>Uptime: ${b.uptime}</p>`;
if(t==='settings')panel.innerHTML=`<table><tr><th>Max leverage</th><td>${b.max_leverage}</td></tr><tr><th>Risk per trade</th><td>${b.risk}</td></tr><tr><th>Exchange</th><td>${b.exchange}</td></tr></table>`;
if(t==='orders'){panel.innerHTML=`<p>Orders are listed in a dialog.</p><button id="open">Open orders</button>`;
document.getElementById('open').onclick=()=>{const tb=document.querySelector('#orders tbody');tb.innerHTML='';
for(const o of b.orders){const tr=document.createElement('tr');tr.innerHTML=`<td>${o.id}</td><td>${o.symbol}</td><td>${o.side}</td><td>${o.created}</td>`;tb.appendChild(tr);}
document.getElementById('empty').textContent=b.orders.length?'':'No open orders';document.getElementById('dlg').showModal();};}};
document.querySelectorAll('[role=tab]').forEach(x=>x.onclick=()=>show(x.dataset.tab));
document.getElementById('close').onclick=()=>document.getElementById('dlg').close();show('overview');})();"""
            return self.send(200, page("Bot detail", body, script))
        if method == "GET" and path.startswith("/api/bots/"):
            bid = path.rsplit("/", 1)[-1]
            bot = next((b for b in cfg["bots"] if b["id"] == bid), None)
            if not bot:
                return self.jsend(404, {"error": "no such bot"})
            with LOCK:
                self.record(st, "bot_detail", bot=bid)
            return self.jsend(200, bot)
        return self.send(404, page("Not found", "<h1>Not found</h1>"))

    # ---------- H3: lazy-loaded feed, transient toast, re-rendering button
    def h3(self, st, method, path):
        cfg = st["config"]  # {"alerts": [{symbol, code, msg}], "target_symbol"}
        if method == "GET" and path == "/":
            body = """<h1>Live monitor</h1>
<section><h2>One-time token</h2><button id="gen">Generate one-time token</button><div id="toast" role="status" aria-live="polite"></div></section>
<section><h2>Confirm</h2><div id="confirm-box"></div><p id="confirm-out"></p></section>
<section><h2>Alerts</h2><p>Newest first. More alerts load as you scroll.</p><ol id="alerts"></ol><div id="sentinel">Loading more…</div></section>"""
            script = """let cursor=0,loading=false,done=false;const ol=document.getElementById('alerts');
async function more(){if(loading||done)return;loading=true;const r=await (await fetch('/api/alerts?cursor='+cursor)).json();
for(const a of r.items){const li=document.createElement('li');li.style.padding='10px 0';li.textContent=`${a.symbol} — ${a.msg} — code ${a.code}`;ol.appendChild(li);}
cursor=r.next;done=r.next===null;if(done)document.getElementById('sentinel').textContent='No more alerts';loading=false;
obs.unobserve(sen);obs.observe(sen);}
const sen=document.getElementById('sentinel');const obs=new IntersectionObserver(es=>{if(es.some(e=>e.isIntersecting))more();});obs.observe(sen);
document.getElementById('gen').onclick=async()=>{const j=await (await fetch('/api/token',{method:'POST'})).json();
const t=document.getElementById('toast');t.textContent='Your one-time token: '+j.token;setTimeout(()=>{t.textContent='';},5000);};
const box=document.getElementById('confirm-box');let gen=0;
function renderConfirm(){gen++;const b=document.createElement('button');b.textContent='Confirm';b.id='confirm-'+gen;
b.onclick=async()=>{const j=await (await fetch('/api/confirm',{method:'POST'})).json();document.getElementById('confirm-out').textContent='Confirmation code: '+j.code;};
box.replaceChildren(b);}renderConfirm();setInterval(renderConfirm,2500);"""
            return self.send(200, page("Live monitor", body, script))
        if method == "GET" and path == "/api/alerts":
            q = urlparse(self.path).query
            cur = int((dict(x.split("=", 1) for x in q.split("&") if "=" in x)).get("cursor", "0") or 0)
            items = cfg["alerts"][cur:cur + 20]
            nxt = cur + 20 if cur + 20 < len(cfg["alerts"]) else None
            time.sleep(0.4)
            with LOCK:
                self.record(st, "alerts_page", cursor=cur)
            return self.jsend(200, {"items": items, "next": nxt})
        if method == "POST" and path == "/api/token":
            tok = "TK-" + secrets.token_hex(3).upper()
            with LOCK:
                st["config"].setdefault("tokens", []).append(tok)
                self.record(st, "token", token=tok)
            return self.jsend(200, {"token": tok})
        if method == "POST" and path == "/api/confirm":
            code = "CF-" + secrets.token_hex(3).upper()
            with LOCK:
                st["config"].setdefault("confirm_codes", []).append(code)
                self.record(st, "confirm", code=code)
            return self.jsend(200, {"code": code})
        return self.send(404, page("Not found", "<h1>Not found</h1>"))


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    srv.daemon_threads = True
    print(f"fixtures on 127.0.0.1:{PORT}", file=sys.stderr, flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
