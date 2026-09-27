#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Genera un palinsesto settimanale da asiria.is
- Estrae eventi da https://asiria.is/api_all.php
- Raggruppa per giorno e per sport
- Genera HTML con struttura simile a kira_ultra.html
"""

import json
import urllib.request
from datetime import datetime, date, timedelta
from collections import defaultdict

# ============================================================
# CONFIGURAZIONE
# ============================================================
API_URL = "https://asiria.is/api_all.php"
API_CHANNELS = "https://asiria.is/channels_api.php"
OUTPUT_HTML = "kira_asi_sett.html"
GIORNI_DA_MOSTRARE = 7

# ============================================================
# UTILITY
# ============================================================

def scarica_json(url):
    """Scarica JSON da URL con header browser-like."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
            "Accept": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def carica_canali():
    """Crea una mappa URL->nome canale per visualizzazione."""
    try:
        data = scarica_json(API_CHANNELS)
        mappa = {}
        for ch in data.get("channels", []):
            url = ch.get("url", "")
            nome = ch.get("name", "")
            if url and nome:
                mappa[url] = nome
        return mappa
    except Exception as e:
        print(f"⚠️ Impossibile caricare i canali: {e}")
        return {}


def nome_canale(url, mappa_canali):
    """Restituisce il nome del canale se disponibile, altrimenti l'URL."""
    if url in mappa_canali:
        return mappa_canali[url]
    # Fallback: estrai il nome del file
    return url.split("/")[-1].replace(".php", "")


# ============================================================
# ESTRAZIONE DATI
# ============================================================

def estrai_eventi_settimana():
    """Estrae gli eventi di una settimana da api_all.php."""
    print("=" * 60)
    print("  ESTRAZIONE EVENTI DA asiria.is")
    print("=" * 60)
    
    print("\n📡 Scaricando eventi da api_all.php...")
    data = scarica_json(API_URL)
    
    if data.get("status") != "ok":
        print("❌ Errore: risposta API non valida")
        return {}
    
    eventi_raw = data.get("events", [])
    print(f"   ✅ Ricevuti {len(eventi_raw)} eventi totali")
    
    # Carica mappa canali
    print("\n📺 Caricando lista canali...")
    mappa_canali = carica_canali()
    print(f"   ✅ {len(mappa_canali)} canali caricati")
    
    # Data di oggi e intervallo settimanale
    oggi = date.today()
    data_limite = oggi + timedelta(days=GIORNI_DA_MOSTRARE)
    
    print(f"\n📅 Intervallo: da {oggi.isoformat()} a {data_limite.isoformat()}")
    print("-" * 60)
    
    # Struttura: {data_iso: {sport: [eventi]}}
    palinsesto = defaultdict(lambda: defaultdict(list))
    
    eventi_filtrati = 0
    for ev in eventi_raw:
        try:
            data_ev = date.fromisoformat(ev.get("date", ""))
        except (ValueError, TypeError):
            continue
        
        # Filtra solo eventi nell'intervallo settimanale
        if not (oggi <= data_ev < data_limite):
            continue
        
        data_iso = ev["date"]
        sport = ev.get("sport", "altro").capitalize()
        
        # Arricchisci con nomi canali
        links_arricchiti = []
        for url in ev.get("links", []):
            links_arricchiti.append({
                "url": url,
                "nome": nome_canale(url, mappa_canali)
            })
        
        evento = {
            "time": ev.get("time", "N/D"),
            "event": ev.get("event", "Evento sconosciuto"),
            "timestamp": ev.get("timestamp", 0),
            "links": links_arricchiti
        }
        
        palinsesto[data_iso][sport].append(evento)
        eventi_filtrati += 1
    
    print(f"\n   ✅ {eventi_filtrati} eventi nell'intervallo settimanale")
    print("\n📊 Riepilogo per giorno:")
    for data_iso in sorted(palinsesto.keys()):
        d = date.fromisoformat(data_iso)
        sport_count = {s: len(evs) for s, evs in palinsesto[data_iso].items()}
        print(f"   📅 {d.strftime('%A %d %B')}: {sum(sport_count.values())} eventi")
        for sport, count in sport_count.items():
            print(f"      🏆 {sport}: {count}")
    
    return dict(palinsesto)


# ============================================================
# GENERAZIONE HTML
# ============================================================

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
            position: relative;
        }
        .matrix-bg {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; background: #0a0a0a; overflow: hidden;
        }
        .matrix-bg::before {
            content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 255, 204, 0.03) 2px, rgba(0, 255, 204, 0.03) 4px);
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
                    <div class="event-links">
                        {% if evento.links %}
                            {% for link in evento.links %}
                            <a href="{{ link.url }}" target="_blank" class="server-link">▶ {{ link.nome }}</a>
                            {% endfor %}
                        {% else %}
                            <span class="no-link">Nessun link disponibile</span>
                        {% endif %}
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
    """Genera il file HTML finale."""
    from jinja2 import Environment
    
    if not palinsesto:
        print("❌ Nessun evento da mostrare")
        return
    
    # Ordina giorni
    giorni_ordinati = sorted(palinsesto.keys())
    
    # Label giorni
    giorno_label = {}
    for data_iso in giorni_ordinati:
        d = date.fromisoformat(data_iso)
        giorno_label[data_iso] = d.strftime("%A %d %B %Y").capitalize()
    
    # Ordina sport per ogni giorno (prima football, poi altri alfabeticamente)
    sport_ordinati = {}
    for data_iso in giorni_ordinati:
        sport_list = list(palinsesto[data_iso].keys())
        sport_list.sort(key=lambda s: (s.lower() != "football", s))
        sport_ordinati[data_iso] = sport_list
    
    # Label settimana
    inizio = date.fromisoformat(giorni_ordinati[0]).strftime("%d/%m/%Y")
    fine = date.fromisoformat(giorni_ordinati[-1]).strftime("%d/%m/%Y")
    settimana_label = f"{inizio} - {fine}"
    
    # Totale eventi
    totale = sum(
        len(eventi)
        for sport_dict in palinsesto.values()
        for eventi in sport_dict.values()
    )
    
    # Render
    env = Environment()
    template = env.from_string(HTML_TEMPLATE)
    html_output = template.render(
        palinsesto=palinsesto,
        giorni_ordinati=giorni_ordinati,
        giorno_label=giorno_label,
        sport_ordinati=sport_ordinati,
        settimana_label=settimana_label,
        totale_eventi=totale,
        anno=date.today().year
    )
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_output)
    
    print(f"\n✅ File generato: {OUTPUT_HTML}")
    print(f"   Totale eventi: {totale}")
    print(f"   Giorni: {len(giorni_ordinati)}")
    print(f"   Sport unici: {len(set(s for d in palinsesto.values() for s in d.keys()))}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    try:
        # Estrai eventi
        palinsesto = estrai_eventi_settimana()
        
        # Genera HTML
        if palinsesto:
            genera_html(palinsesto)
        else:
            print("\n⚠️ Nessun evento trovato nell'intervallo settimanale")
    
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()