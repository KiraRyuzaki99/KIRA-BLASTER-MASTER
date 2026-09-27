#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Palinsesto settimanale da asiria.is SENZA link streaming
Solo orari e nomi eventi, raggruppati per giorno e sport
"""

import json
import urllib.request
from datetime import date, timedelta
from collections import defaultdict
from jinja2 import Environment

API_URL = "https://asiria.is/api_all.php"
OUTPUT_HTML = "Eventi della Settimana.html"
GIORNI = 7


def scarica_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
        "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def estrai_settimana():
    print("=" * 55)
    print("  ASIRIA.IS — PALINSESTO SETTIMANALE (SENZA LINK)")
    print("=" * 55)

    data = scarica_json(API_URL)
    eventi_raw = data.get("events", [])
    print(f"\n📡 {len(eventi_raw)} eventi totali ricevuti")

    oggi = date.today()
    limite = oggi + timedelta(days=GIORNI)
    print(f"📅 Intervallo: {oggi.isoformat()} → {limite.isoformat()}\n")

    palinsesto = defaultdict(lambda: defaultdict(list))
    count = 0

    for ev in eventi_raw:
        try:
            d = date.fromisoformat(ev.get("date", ""))
        except (ValueError, TypeError):
            continue
        if not (oggi <= d < limite):
            continue
        sport = ev.get("sport", "altro").capitalize()
        palinsesto[ev["date"]][sport].append({
            "time": ev.get("time", "N/D"),
            "event": ev.get("event", "?")
        })
        count += 1

    print(f"✅ {count} eventi nella settimana:")
    for d_iso in sorted(palinsesto):
        d = date.fromisoformat(d_iso)
        n = sum(len(v) for v in palinsesto[d_iso].values())
        print(f"   📅 {d.strftime('%A %d %B')}: {n} eventi")

    return dict(palinsesto)


HTML_PURO = r"""<!DOCTYPE html>
<html lang="it"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CYBER GATE ACCESS • {{ settimana }}</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Audiowide&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Grotesk',sans-serif;background:#0a0a0a;color:#00ffcc;min-height:100vh}
.matrix-bg{position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;background:#0a0a0a}
.matrix-bg::before{content:'';position:absolute;top:0;left:0;width:100%;height:100%;
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
.day-section{margin-bottom:50px}
.day-header{font-family:'Orbitron',sans-serif;font-weight:900;font-size:1.8rem;
color:#00ffcc;padding:15px 20px;background:rgba(0,255,204,.08);
border-left:4px solid #00ffcc;margin-bottom:25px;
text-shadow:0 0 15px rgba(0,255,204,.3)}
.sport-header{font-family:'Audiowide',cursive;font-size:1.2rem;color:#88ffdd;
padding:8px 15px;margin:20px 0 15px;background:rgba(0,255,204,.05);
border-radius:8px;display:inline-block}
.events-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:25px}
.event-card{background:rgba(0,30,30,.7);border:1px solid rgba(0,255,204,.2);
border-radius:15px;padding:25px;transition:all .3s ease}
.event-card:hover{transform:translateY(-5px);border-color:rgba(0,255,204,.6);box-shadow:0 0 40px rgba(0,255,204,.15)}
.event-info h3{font-family:'Orbitron',sans-serif;font-weight:700;font-size:1.1rem;color:#00ffcc;margin-bottom:8px}
.event-info .datetime{color:#88ddff;font-size:.9rem;opacity:.8}
.fonte-badge{display:inline-block;font-size:.75rem;background:rgba(0,255,204,.15);
color:#88ffdd;padding:2px 12px;border-radius:12px;margin-top:8px;border:1px solid rgba(0,255,204,.2)}
.footer{text-align:center;padding:40px 0 20px;margin-top:60px;
border-top:1px solid rgba(0,255,204,.2);color:#88ddff;opacity:.7}
</style></head><body>
<div class="matrix-bg"></div>
<div class="container">
<header class="header">
<h1>KIRA GATE ACCESS </h1>
<p class="subtitle">• Palinsesto Sportivo {{ settimana }} •</p>
</header>
{% for d_iso in giorni %}
<div class="day-section">
<div class="day-header">📅 {{ giorno_label[d_iso] }}</div>
{% for sport in sport_ordinati[d_iso] %}
<div class="sport-header">🏆 {{ sport }} ({{ palinsesto[d_iso][sport]|length }})</div>
<div class="events-grid">
{% for ev in palinsesto[d_iso][sport] %}
<div class="event-card">
<div class="event-info">
<h3>{{ ev.event }}</h3>
<p class="datetime">🕒 {{ ev.time }}</p>
<span class="fonte-badge">📡 asiria.is</span>
</div>
</div>
{% endfor %}
</div>
{% endfor %}
</div>
{% endfor %}
<footer class="footer"><p>KIRA GSI SPORT • Palinsesto Sportivo {{ settimana }} Developed by KIRA GSI GROUP</p></footer>
</div></body></html>"""


def genera_html(palinsesto):
    if not palinsesto:
        print("❌ Nessun evento")
        return
    giorni = sorted(palinsesto.keys())
    giorno_label = {}
    for d_iso in giorni:
        d = date.fromisoformat(d_iso)
        giorno_label[d_iso] = d.strftime("%A %d %B %Y").capitalize()
    sport_ordinati = {}
    for d_iso in giorni:
        sl = list(palinsesto[d_iso].keys())
        sl.sort()
        sport_ordinati[d_iso] = sl
    settimana = f"{date.fromisoformat(giorni[0]).strftime('%d/%m')} - {date.fromisoformat(giorni[-1]).strftime('%d/%m/%Y')}"
    env = Environment()
    t = env.from_string(HTML_PURO)
    out = t.render(palinsesto=palinsesto, giorni=giorni,
                   giorno_label=giorno_label, sport_ordinati=sport_ordinati,
                   settimana=settimana)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"\n✅ Generato: {OUTPUT_HTML}")


if __name__ == "__main__":
    p = estrai_settimana()
    if p:
        genera_html(p)
    else:
        print("⚠️ Nessun evento nella settimana")