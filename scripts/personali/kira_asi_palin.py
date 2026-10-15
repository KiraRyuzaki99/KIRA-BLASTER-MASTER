#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Palinsesto settimanale da asiria.is SENZA link streaming
Fonte: indexgol.txt
"""

import re
import urllib.request
from datetime import date, timedelta, datetime
from collections import defaultdict
from jinja2 import Environment

URL_TXT = "https://asiria.is/indexgol.txt"
OUTPUT_HTML = "Eventi della Settimana.html"
GIORNI = 7

MESI = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}


def scarica_testo(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def parsa_data(stringa):
    """Parsa 'Sunday, 11 October 2026' in date."""
    m = re.match(
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(\d+)\s+(\w+)\s+(\d{4})",
        stringa.strip(), re.IGNORECASE
    )
    if not m:
        return None
    try:
        return date(int(m.group(4)), MESI[m.group(3).lower()], int(m.group(2)))
    except (ValueError, KeyError):
        return None


def parsa_indexgol_completo(testo):
    """
    Parsa TUTTO indexgol.txt.
    Ritorna: {data_iso: {sport: [eventi]}}
    """
    palinsesto = defaultdict(lambda: defaultdict(list))
    
    # Dividi per date: ogni data è un header "Day, DD Month YYYY"
    pattern_data = re.compile(
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+\d+\s+\w+\s+\d{4}",
        re.IGNORECASE
    )
    
    # Trova tutte le date e le loro posizioni
    matches = list(pattern_data.finditer(testo))
    
    for i, m in enumerate(matches):
        data_str = m.group(0)
        data_obj = parsa_data(data_str)
        if not data_obj:
            continue
        data_iso = data_obj.isoformat()
        
        inizio = m.end()
        fine = matches[i + 1].start() if i + 1 < len(matches) else len(testo)
        
        sezione = testo[inizio:fine]
        
        # Dividi in blocchi per separatore -----
        blocchi = re.split(r"-{10,}", sezione)
        
        for blocco in blocchi:
            blocco = blocco.strip()
            if not blocco:
                continue
            righe = [r.strip() for r in blocco.split("\n") if r.strip()]
            if not righe:
                continue
            
            prima = righe[0]
            m2 = re.match(r"^(\d{1,2}:\d{2})\s+(.+)$", prima)
            if not m2:
                continue
            
            orario = m2.group(1)
            resto = m2.group(2)
            
            if ":" in resto:
                sport_raw, evento = resto.split(":", 1)
                sport = sport_raw.strip().capitalize()
                evento = evento.strip()
            else:
                if resto.lower().startswith("tennis"):
                    sport = "Tennis"
                else:
                    sport = "Altro"
                evento = resto
            
            palinsesto[data_iso][sport].append({
                "time": orario,
                "event": evento
            })
    
    return {d: dict(s) for d, s in palinsesto.items()}


def estrai_settimana():
    print("=" * 55)
    print("  ASIRIA.IS — PALINSESTO SETTIMANALE (SENZA LINK)")
    print("=" * 55)
    
    testo = scarica_testo(URL_TXT)
    print(f"\n📡 Scaricati {len(testo)} caratteri")
    
    completo = parsa_indexgol_completo(testo)
    print(f"📅 Date trovate nel file: {len(completo)}")
    
    oggi = date.today()
    limite = oggi + timedelta(days=GIORNI)
    
    # Filtra solo i giorni nell'intervallo
    palinsesto = {}
    for d_iso, sport_dict in completo.items():
        d = date.fromisoformat(d_iso)
        if oggi <= d < limite:
            palinsesto[d_iso] = sport_dict
    
    totale = sum(len(v) for sd in palinsesto.values() for v in sd.values())
    print(f"\n✅ {totale} eventi nell'intervallo {oggi} → {limite}")
    for d_iso in sorted(palinsesto):
        n = sum(len(v) for v in palinsesto[d_iso].values())
        print(f"   📅 {d_iso}: {n} eventi")
    
    return palinsesto


HTML_PURO = r"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>KIRA PALINSESTO • {{ settimana_label }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Audiowide&family=Grotesk:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Grotesk', sans-serif;
            background: #0a0a0a;
            color: #00ffcc;
            min-height: 100vh;
            overflow-x: hidden;
        }
        .matrix-bg {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            z-index: -1; background: #0a0a0a; overflow: hidden;
        }
        .matrix-bg::before {
            content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0, 255, 204, 0.12) 3px, rgba(0, 255, 204, 0.12) 6px);
            animation: matrixScroll 15s linear infinite;
        }
        @keyframes matrixScroll { 0% { transform: translateY(0); } 100% { transform: translateY(100%); } }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; position: relative; z-index: 1; }
        .header { text-align: center; padding: 30px 0 40px; border-bottom: 2px solid rgba(0, 255, 204, 0.3); margin-bottom: 40px; }
        .header h1 {
            font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 3.5rem;
            text-shadow: 0 0 20px rgba(0, 255, 204, 0.5);
            background: linear-gradient(135deg, #00ffcc, #00ccff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 4px;
        }
        .header .subtitle { font-family: 'Audiowide', cursive; color: #88ffdd; font-size: 1.2rem; margin-top: 10px; }
        .event-counter {
            text-align: center; font-family: 'Orbitron', monospace; font-size: 1.2rem; color: #00ffcc;
            background: rgba(0, 255, 204, 0.08); border: 1px solid rgba(0, 255, 204, 0.2);
            padding: 12px 20px; border-radius: 30px; display: inline-block; margin: 0 auto 30px;
        }
        .event-counter span { font-weight: 900; font-size: 1.5rem; }
        
        .day-section { margin-bottom: 50px; }
        .day-header {
            font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 1.8rem;
            color: #00ffcc; padding: 15px 20px; background: rgba(0, 255, 204, 0.08);
            border-left: 4px solid #00ffcc; margin-bottom: 25px;
            text-shadow: 0 0 15px rgba(0, 255, 204, 0.3);
        }
        .sport-header {
            font-family: 'Audiowide', cursive; font-size: 1.2rem; color: #88ffdd;
            padding: 8px 15px; margin: 20px 0 15px; background: rgba(0, 255, 204, 0.05);
            border-radius: 8px; display: inline-block;
        }
        
        .events-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 25px; margin-top: 15px; }
        .event-card {
            background: rgba(0, 30, 30, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(0, 255, 204, 0.2);
            border-radius: 15px; padding: 25px; transition: all 0.3s ease; display: flex; flex-direction: column;
        }
        .event-card:hover { transform: translateY(-5px); border-color: rgba(0, 255, 204, 0.6); box-shadow: 0 0 40px rgba(0, 255, 204, 0.15); }
        .event-info h3 { font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 1.1rem; color: #00ffcc; margin-bottom: 8px; }
        .event-info .datetime { color: #88ddff; font-size: 0.9rem; opacity: 0.8; margin-bottom: 10px; }
        .fonte-badge {
            display: inline-block; font-size: 0.75rem; background: rgba(0, 255, 204, 0.15);
            color: #88ffdd; padding: 2px 12px; border-radius: 12px; margin-top: 5px;
            border: 1px solid rgba(0, 255, 204, 0.2);
        }
        .event-links { margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(0, 255, 204, 0.15); }
        .server-link {
            display: block; font-family: 'Orbitron', monospace; font-weight: 700; color: #0a0a0a;
            background: #00ffcc; padding: 10px 18px; border-radius: 8px; text-decoration: none;
            text-align: center; margin-bottom: 8px; transition: all 0.3s ease;
            font-size: 0.85rem;
        }
        .server-link:hover { background: #00ddbb; box-shadow: 0 0 40px rgba(0, 255, 204, 0.5); }
        .no-link {
            display: block; text-align: center; color: #666; font-size: 0.85rem;
            padding: 10px; font-style: italic;
        }
        .footer { text-align: center; padding: 40px 0 20px; margin-top: 60px; border-top: 1px solid rgba(0, 255, 204, 0.2); color: #88ddff; opacity: 0.7; }
        .footer .neon-text { font-family: 'Orbitron', monospace; color: #00ffcc; font-size: 1rem; }
    </style>
</head>
<body>
    <div class="matrix-bg"></div>
    <div class="container">
        <header class="header">
            <h1>KIRA PALINSESTO</h1>
            <p class="subtitle">• {{ settimana_label }} •</p>
        </header>
        <div style="text-align: center;">
            <div class="event-counter">
                🎯 <span>{{ totale_eventi }}</span> eventi disponibili
            </div>
        </div>
        
        {% for data_iso in giorni_ordinati %}
        <div class="day-section">
            <div class="day-header">📅 {{ giorno_label[data_iso] }}</div>
            
            {% for sport in sport_ordinati[data_iso] %}
            <div class="sport-header">🏆 {{ sport }} ({{ palinsesto[data_iso][sport]|length }})</div>
            <div class="events-grid">
                {% for evento in palinsesto[data_iso][sport] %}
                <div class="event-card">
                    <div class="event-info">
                        <h3>{{ evento.event }}</h3>
                        <p class="datetime">🕒 {{ evento.time }}</p>
                        <span class="fonte-badge">📡 asiria.is</span>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endfor %}
        </div>
        {% endfor %}
        
        <footer class="footer">
            <p class="neon-text">KIRA GSI SPORT • Palinsesto Settimanale • {{ anno }} • Developed by KIRA GSI GROUP</p>
        </footer>
    </div>
</body>
</html>"""


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
    totale = sum(len(v) for sd in palinsesto.values() for v in sd.values())
    out = t.render(palinsesto=palinsesto, giorni_ordinati=giorni,
                   giorno_label=giorno_label, sport_ordinati=sport_ordinati,
                   settimana_label=settimana, totale_eventi=totale,
                   anno=date.today().year)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"\n✅ Generato: {OUTPUT_HTML}")


if __name__ == "__main__":
    p = estrai_settimana()
    if p:
        genera_html(p)
    else:
        print("⚠️ Nessun evento nella settimana")