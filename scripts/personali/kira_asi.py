#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Estrae SOLO gli eventi del giorno corrente da asiria.is
Genera HTML con struttura Kira Ultra (con link streaming)
"""

import json
import urllib.request
from datetime import date
from collections import defaultdict
from jinja2 import Environment

API_URL = "https://asiria.is/api_all.php"
API_CHANNELS = "https://asiria.is/channels_api.php"
OUTPUT_HTML = "kira_asi.html"


def scarica_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
        "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def carica_canali():
    try:
        data = scarica_json(API_CHANNELS)
        mappa = {}
        for ch in data.get("channels", []):
            if ch.get("url") and ch.get("name"):
                mappa[ch["url"]] = ch["name"]
        return mappa
    except Exception as e:
        print(f"⚠️ Canali non caricati: {e}")
        return {}


def nome_canale(url, mappa):
    return mappa.get(url, url.split("/")[-1].replace(".php", ""))


def estrai_oggi():
    print("=" * 55)
    print("  ASIRIA.IS — EVENTI DI OGGI")
    print("=" * 55)

    data = scarica_json(API_URL)
    eventi_raw = data.get("events", [])
    print(f"\n📡 Ricevuti {len(eventi_raw)} eventi totali")

    mappa = carica_canali()
    print(f"📺 {len(mappa)} canali caricati")

    oggi_iso = date.today().isoformat()
    print(f"📅 Filtro: {oggi_iso}\n")

    palinsesto = defaultdict(lambda: defaultdict(list))

    for ev in eventi_raw:
        if ev.get("date") != oggi_iso:
            continue
        sport = ev.get("sport", "altro").capitalize()
        links = [{"url": u, "nome": nome_canale(u, mappa)}
                 for u in ev.get("links", [])]
        palinsesto[oggi_iso][sport].append({
            "time": ev.get("time", "N/D"),
            "event": ev.get("event", "?"),
            "links": links
        })

    totale = sum(len(v) for v in palinsesto[oggi_iso].values())
    print(f"✅ {totale} eventi trovati per oggi:")
    for s, evs in palinsesto[oggi_iso].items():
        print(f"   🏆 {s}: {len(evs)}")

    return dict(palinsesto), oggi_iso


HTML_OGGI = r"""<!DOCTYPE html>
<html lang="it"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CYBER GATE ACCESS • {{ data_iso }}</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Audiowide&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Grotesk',sans-serif;background:#0a0a0a;color:#00ffcc;min-height:100vh}
.matrix-bg{position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;background:#0a0a0a}
.matrix-bg::before{content:'';position:absolute;top:0;left:0;width:100%;height:100%;
background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,255,204,.03) 2px,rgba(0,255,204,.03) 4px);
animation:ms 15s linear infinite}
background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,255,204,.03) 2px,rgba(0,255,204,.03) 4px);
animation:ms 15s linear infinite}
@keyframes ms{0%{transform:translateY(0)}100%{transform:translateY(100%)}}
.container{max-width:1200px;margin:0 auto;padding:20px;position:relative;z-index:1}
.header{text-align:center;padding:30px 0 40px;border-bottom:2px solid rgba(0,255,204,.3);margin-bottom:40px}
.header h1{font-family:'Orbitron',sans-serif;font-weight:900;font-size:3.5rem;
text-shadow:0 0 20px rgba(0,255,204,.5);
background:linear-gradient(135deg,#00ffcc,#00ccff);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px}
.header .subtitle{font-family:'Audiowide',cursive;color:#88ffdd;font-size:1.2rem;margin-top:10px}
.counter{text-align:center;font-family:'Orbitron',monospace;font-size:1.2rem;color:#00ffcc;
background:rgba(0,255,204,.08);border:1px solid rgba(0,255,204,.2);
padding:12px 20px;border-radius:30px;display:inline-block;margin:0 auto 30px}
.counter span{font-weight:900;font-size:1.5rem}
.sport-header{font-family:'Audiowide',cursive;font-size:1.2rem;color:#88ffdd;
padding:8px 15px;margin:20px 0 15px;background:rgba(0,255,204,.05);border-radius:8px;display:inline-block}
.events-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:25px}
.event-card{background:rgba(0,30,30,.7);border:1px solid rgba(0,255,204,.2);
border-radius:15px;padding:25px;transition:all .3s ease}
.event-card:hover{transform:translateY(-5px);border-color:rgba(0,255,204,.6);box-shadow:0 0 40px rgba(0,255,204,.15)}
.event-info h3{font-family:'Orbitron',sans-serif;font-weight:700;font-size:1.1rem;color:#00ffcc;margin-bottom:8px}
.event-info .datetime{color:#88ddff;font-size:.9rem;opacity:.8;margin-bottom:10px}
.fonte-badge{display:inline-block;font-size:.75rem;background:rgba(0,255,204,.15);
color:#88ffdd;padding:2px 12px;border-radius:12px;margin-top:5px;border:1px solid rgba(0,255,204,.2)}
.event-links{margin-top:15px;padding-top:15px;border-top:1px solid rgba(0,255,204,.15)}
.server-link{display:block;font-family:'Orbitron',monospace;font-weight:700;color:#0a0a0a;
background:#00ffcc;padding:10px 18px;border-radius:8px;text-decoration:none;
text-align:center;margin-bottom:8px;font-size:.85rem}
.server-link:hover{background:#00ddbb;box-shadow:0 0 40px rgba(0,255,204,.5)}
.no-link{display:block;text-align:center;color:#666;font-size:.85rem;padding:10px;font-style:italic}
.footer{text-align:center;padding:40px 0 20px;margin-top:60px;
border-top:1px solid rgba(0,255,204,.2);color:#88ddff;opacity:.7}
</style></head><body>
<div class="matrix-bg"></div>
<div class="container">
<header class="header">
<h1>KIRA GATE ACCESS</h1>
<p class="subtitle">• Eventi di oggi {{ data_iso }} •</p>
</header>
<div style="text-align:center">
<div class="counter">🎯 <span>{{ totale }}</span> eventi oggi</div>
</div>
{% for sport, eventi in palinsesto[data_iso].items() %}
<div class="sport-header">🏆 {{ sport }} ({{ eventi|length }})</div>
<div class="events-grid">
{% for ev in eventi %}
<div class="event-card">
<div class="event-info">
<h3>{{ ev.event }}</h3>
<p class="datetime">🕒 {{ ev.time }}</p>
<span class="fonte-badge">📡 asiria.is</span>
</div>
<div class="event-links">
{% if ev.links %}
{% for l in ev.links %}
<a href="{{ l.url }}" target="_blank" class="server-link">▶ {{ l.nome }}</a>
{% endfor %}
{% else %}
<span class="no-link">Nessun link</span>
{% endif %}
</div>
</div>
{% endfor %}
</div>
{% endfor %}
<footer class="footer"><p>KIRA GSI SPORT • Eventi in Diretta {{ data_iso }} Developed by KIRA GSI GROUP</p></footer>
</div></body></html>"""


def genera_html(palinsesto, data_iso):
    totale = sum(len(v) for v in palinsesto[data_iso].values())
    env = Environment()
    t = env.from_string(HTML_OGGI)
    out = t.render(palinsesto=palinsesto, data_iso=data_iso, totale=totale)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"\n✅ Generato: {OUTPUT_HTML} ({totale} eventi)")


if __name__ == "__main__":
    palinsesto, data_iso = estrai_oggi()
    if palinsesto.get(data_iso):
        genera_html(palinsesto, data_iso)
    else:
        print("⚠️ Nessun evento oggi")