#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DADDYLIVE AUTO - Genera HTML per ogni sport con stile KIRA GSI
"""

import requests
import json
import os
import re
from datetime import datetime
from collections import defaultdict
from html import escape

# ============================================================
#  CONFIGURAZIONE
# ============================================================

ENDPOINT_BASE = "https://daddylive.li/player/"
OUTPUT_DIR = "output/Daddy"  # <- Cartella dedicata

# Mappatura sport - Pattern PRECISI
SPORT_PATTERNS = {
    "Calcio": [
        r"soccer", r"football", r"serie a", r"premier league", r"bundesliga", 
        r"la liga", r"ligue 1", r"eredivisie", r"primeira liga", 
        r"champions league", r"europa league", r"conference league",
        r"calcio", r"coppa italia", r"fa cup", r"dfb pokal", 
        r"copa del rey", r"super lig", r"eredivisie",
        r"serie a", r"serie b", r"serie c",
        r"premier league", r"championship", r"league one", r"league two",
        r"bundesliga", r"2\. bundesliga", r"3\. liga",
        r"la liga", r"segunda division",
        r"ligue 1", r"ligue 2",
        r"primeira liga", r"liga portugal",
        r"eredivisie", r"keuken kampioen divisie",
        r"pro league", r"jupiler pro league",
        r"super lig", r"1\. lig",
        r"allsvenskan", r"superettan",
        r"superliga", r"1\. division",
        r"veikkausliiga", r"ykkönen",
        r"ekstraklasa", r"i liga",
        r"nike liga", r"fortuna liga",
        r"ligue", r"league", r"liga", r"serie", r"bundes", r"calcio",
        r"coppa", r"cup", r"pokal", r"trophy"
    ],
    "Tennis": [
        r"tennis", r"atp", r"wta", r"us open", r"wimbledon", 
        r"australian open", r"roland garros", r"french open",
        r"challenger", r"masters 1000", r"grand slam",
        r"davis cup", r"billie jean king cup",
        r"tennis", r"abierto de", r"open de"
    ],
    "Basket": [
        r"basketball", r"nba", r"euroleague", r"liga acb", 
        r"ncaa", r"basket", r"baloncesto",
        r"eurocup", r"basketball champions league",
        r"liga endesa", r"serie a basket", r"bbl",
        r"lnb", r"basketball bundesliga"
    ],
    "Hockey": [
        r"hockey", r"nhl", r"liiga", r"shl", r"extraliga",
        r"ahl", r"khl", r"del", r"national league",
        r"champions hockey league", r"ohl", r"whl", r"qmjhl"
    ],
    "Motori": [
        r"formula", r"f1", r"f2", r"f3", r"motogp", 
        r"superbike", r"rally", r"nascar", r"indycar",
        r"wec", r"imsa", r"btcc", r"dtm",
        r"automobilismo", r"motorsport", r"racing"
    ],
    "Baseball": [
        r"baseball", r"mlb", r"kbo", r"npb", r"world series",
        r"little league", r"college baseball"
    ],
    "Rugby": [
        r"rugby", r"super league", r"nrl", r"6 nazioni",
        r"six nations", r"champions cup", r"challenge cup",
        r"top 14", r"united rugby championship"
    ],
    "Voleibol": [
        r"volleyball", r"voley", r"volley", r"liga de voleibol",
        r"fivb", r"world league", r"national league"
    ],
    "Balonmano": [
        r"handball", r"balonmano", r"hbl", r"liga asobal",
        r"ehf", r"champions league handball"
    ],
    "Pugilato": [
        r"boxing", r"pugilato", r"ufc", r"mma", r"bellator",
        r"heavyweight", r"fight", r"combat"
    ],
    "Golf": [
        r"golf", r"pga", r"the open", r"masters", r"ryder cup",
        r"lpga", r"european tour", r"dp world tour"
    ],
    "Ciclismo": [
        r"cycling", r"tour de france", r"giro d'italia", 
        r"la vuelta", r"ciclismo", r"world championships",
        r"classics", r"monument"
    ]
}

EXCLUDE_PATTERNS = [
    r"advertisement", r"sponsor", r"promo", r"bonus",
    r"casino", r"betting", r"slot", r"live chat",
    r"no event", r"coming soon", r"off air"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': 'https://daddylive.eu/',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7'
}

# ============================================================
#  FUNZIONI
# ============================================================

def fetch_json(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"   ⚠️ Errore {response.status_code} per {url}")
            return None
    except Exception as e:
        print(f"   ⚠️ Errore connessione per {url}: {e}")
        return None

def detect_sport(category_name, event_name=""):
    text = f"{category_name} {event_name}".lower()
    
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return "Escluso"
    
    for sport, patterns in SPORT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return sport
    
    return "Altri"

def fetch_all_matches():
    all_events = []
    print("📡 Scaricamento dati da DaddyLive...")
    
    for i in range(1, 10):
        filename = f"tv{i}.json"
        url = ENDPOINT_BASE + filename
        print(f"   📥 {filename}...", end=" ")
        
        data = fetch_json(url)
        if not data:
            print("❌")
            continue
        
        print("✅")
        
        for data_corrente, contenuto in data.items():
            if isinstance(contenuto, list):
                items = [("Eventi", contenuto)]
            elif isinstance(contenuto, dict):
                items = contenuto.items()
            else:
                continue
            
            for categoria_o_chiave, eventi in items:
                blocks = eventi if isinstance(eventi, list) else ([eventi] if isinstance(eventi, dict) else [])
                
                for block in blocks:
                    if not isinstance(block, dict):
                        continue
                    
                    categoria = block.get('Category', block.get('category', categoria_o_chiave))
                    if not isinstance(categoria, str) or not categoria.strip():
                        continue
                    
                    lista_eventi = block.get('events', [])
                    if not isinstance(lista_eventi, list):
                        continue
                    
                    for evento in lista_eventi:
                        if not isinstance(evento, dict):
                            continue
                        
                        titolo = evento.get('event', 'Evento')
                        orario = evento.get('time', 'N/A')
                        canali = evento.get('channels', [])
                        
                        links = []
                        for channel in canali:
                            if not isinstance(channel, dict):
                                continue
                            
                            channel_id = channel.get('channel_id')
                            if channel_id:
                                links.append(f"https://daddylive.eu/embed/embed.php?id={channel_id}")
                            
                            for k, v in channel.items():
                                if k.startswith('embed_') and v:
                                    links.append(v)
                        
                        if not links:
                            continue
                        
                        sport = detect_sport(categoria, titolo)
                        if sport == "Escluso":
                            continue
                        
                        all_events.append({
                            'title': titolo,
                            'time': orario,
                            'date': data_corrente,
                            'category': categoria,
                            'sport': sport,
                            'links': links,
                            'source': filename
                        })
    
    print(f"\n   ✅ Trovati {len(all_events)} eventi totali")
    return all_events

def group_by_sport(events):
    grouped = defaultdict(list)
    for event in events:
        grouped[event['sport']].append(event)
    return grouped

def generate_kira_html(sport, events, output_file):
    """Genera HTML con lo stile KIRA GSI (identico a PyGenHtmlM3U.py)"""
    
    events.sort(key=lambda x: f"{x['date']}_{x['time']}")
    
    # Costruisci le card
    event_items = ""
    for event in events:
        valid_links = [l for l in event['links'] if l != '#']
        
        # Badge stato (sempre "prossimo" come stile KIRA)
        status_badge = '<span class="status-next">⏳ PROSSIMO</span>'
        
        # Links HTML (dropdown se multipli, altrimenti bottone singolo)
        if len(valid_links) > 1:
            options = "\n".join([f'<option value="{l}">{l.split("/")[-1][:30]}</option>' for l in valid_links[:10]])
            links_html = f'''
            <div class="dropdown">
                <select onchange="window.open(this.value, '_blank'); this.selectedIndex=0;">
                    <option value="">📡 Scegli il canale...</option>
                    {options}
                </select>
            </div>
            '''
        elif len(valid_links) == 1:
            link = valid_links[0]
            channel_name = link.split('id=')[-1][:30] if 'id=' in link else '▶ GUARDA IN DIRETTA'
            links_html = f'<a href="{link}" target="_blank" class="server-link">{channel_name}</a>'
        else:
            links_html = '<span class="no-link">🔗 Link non disponibile</span>'
        
        fonte_badge = f'<span class="fonte-badge">📡 {event.get("source", "DaddyLive")}</span>'
        
        event_items += f'''
        <div class="event-card">
            <div class="event-info">
                <h3>{escape(event['title'])} {status_badge}</h3>
                <p class="competition">🏆 {escape(event['category'])}</p>
                <p class="datetime">🕒 {escape(event['time'])} • 📅 {escape(event['date'])}</p>
                {fonte_badge}
            </div>
            <div class="event-links">
                {links_html}
            </div>
        </div>
        '''
    
    # Se non ci sono eventi
    if not event_items:
        event_items = '<p style="text-align:center;color:#666;padding:40px;">Nessun evento disponibile</p>'
    
    # STILE IDENTICO A PyGenHtmlM3U.py
    html_content = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KIRA GSI - {sport}</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Audiowide&family=Grotesk:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Grotesk', sans-serif;
            background: #0a0a0a;
            color: #00ffcc;
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }}
        .matrix-bg {{
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; background: #0a0a0a; overflow: hidden;
        }}
        .matrix-bg::before {{
            content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 255, 204, 0.03) 2px, rgba(0, 255, 204, 0.03) 4px);
            animation: matrixScroll 15s linear infinite;
        }}
        @keyframes matrixScroll {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY(100%); }} }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; position: relative; z-index: 1; }}
        
        .header {{
            text-align: center;
            padding: 30px 0 40px;
            border-bottom: 2px solid rgba(0, 255, 204, 0.3);
            margin-bottom: 40px;
        }}
        .header h1 {{
            font-family: 'Orbitron', sans-serif;
            font-weight: 900;
            font-size: 3.5rem;
            text-shadow: 0 0 20px rgba(0, 255, 204, 0.5);
            background: linear-gradient(135deg, #00ffcc, #00ccff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 4px;
        }}
        .header .subtitle {{
            font-family: 'Audiowide', cursive;
            color: #88ffdd;
            font-size: 1.2rem;
            margin-top: 10px;
        }}
        
        .event-counter {{
            text-align: center;
            font-family: 'Orbitron', monospace;
            font-size: 1.2rem;
            color: #00ffcc;
            background: rgba(0, 255, 204, 0.08);
            border: 1px solid rgba(0, 255, 204, 0.2);
            padding: 12px 20px;
            border-radius: 30px;
            display: inline-block;
            margin: 0 auto 30px;
        }}
        .event-counter span {{ font-weight: 900; font-size: 1.5rem; }}
        
        .events-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}
        
        .event-card {{
            background: rgba(0, 30, 30, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 255, 204, 0.2);
            border-radius: 15px;
            padding: 20px;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
        }}
        .event-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(0, 255, 204, 0.6);
            box-shadow: 0 0 40px rgba(0, 255, 204, 0.15);
        }}
        .event-info h3 {{
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            font-size: 1.1rem;
            color: #00ffcc;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .event-info .competition {{
            font-family: 'Audiowide', cursive;
            color: #88ddff;
            font-size: 0.8rem;
            background: rgba(0, 255, 204, 0.1);
            padding: 3px 12px;
            border-radius: 20px;
            display: inline-block;
            margin-bottom: 8px;
        }}
        .event-info .datetime {{
            color: #88ddff;
            font-size: 0.85rem;
            opacity: 0.8;
        }}
        .fonte-badge {{
            display: inline-block;
            font-size: 0.7rem;
            background: rgba(0, 255, 204, 0.15);
            color: #88ffdd;
            padding: 2px 12px;
            border-radius: 12px;
            margin-top: 5px;
            border: 1px solid rgba(0, 255, 204, 0.2);
        }}
        .status-next {{
            display: inline-block;
            font-size: 0.65rem;
            background: rgba(0, 100, 255, 0.3);
            color: #4488ff;
            padding: 2px 10px;
            border-radius: 12px;
        }}
        .event-links {{
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid rgba(0, 255, 204, 0.15);
        }}
        .server-link {{
            display: inline-block;
            font-family: 'Orbitron', monospace;
            font-weight: 700;
            color: #0a0a0a;
            background: #00ffcc;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            text-align: center;
            width: 100%;
            transition: all 0.3s ease;
            font-size: 0.8rem;
        }}
        .server-link:hover {{
            background: #00ddbb;
            box-shadow: 0 0 40px rgba(0, 255, 204, 0.5);
        }}
        .dropdown select {{
            width: 100%;
            padding: 10px 15px;
            background: rgba(0, 20, 20, 0.9);
            color: #00ffcc;
            border: 1px solid rgba(0, 255, 204, 0.4);
            border-radius: 10px;
            font-family: 'Orbitron', monospace;
            font-size: 0.75rem;
            cursor: pointer;
            outline: none;
        }}
        .dropdown select option {{
            background: #0a1a1a;
            color: #88ffdd;
            padding: 8px;
        }}
        .no-link {{
            display: inline-block;
            font-family: 'Orbitron', monospace;
            color: #666;
            text-align: center;
            width: 100%;
            padding: 10px;
        }}
        
        .footer {{
            text-align: center;
            padding: 40px 0 20px;
            margin-top: 40px;
            border-top: 1px solid rgba(0, 255, 204, 0.2);
            color: #88ddff;
            opacity: 0.7;
        }}
        .footer .neon-text {{
            font-family: 'Orbitron', monospace;
            color: #00ffcc;
            font-size: 1rem;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 2rem; }}
            .events-grid {{ grid-template-columns: 1fr; }}
            .container {{ padding: 15px; }}
            .event-card {{ padding: 18px; }}
        }}
    </style>
</head>
<body>
    <div class="matrix-bg"></div>
    <div class="container">
        <header class="header">
            <h1>⚡ KIRA GSI - {sport} ⚡</h1>
            <p class="subtitle">• Eventi in diretta •</p>
        </header>
        
        <div style="text-align: center;">
            <div class="event-counter">
                🎯 <span>{len(events)}</span> eventi disponibili
            </div>
        </div>
        
        <div class="events-grid">
            {event_items}
        </div>
        
        <footer class="footer">
            <p class="neon-text">🔮 KIRA GSI • {datetime.now().year} • Powered by KIRA</p>
        </footer>
    </div>
</body>
</html>'''
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return len(events)

def main():
    print("="*60)
    print("📡 KIRA GSI - DaddyLive Auto")
    print("="*60)
    
    # Crea cartella output/Daddy
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    events = fetch_all_matches()
    if not events:
        print("❌ Nessun evento trovato!")
        return
    
    grouped = group_by_sport(events)
    
    print("\n📊 Statistiche per sport:")
    for sport, evs in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"   🏆 {sport}: {len(evs)} eventi")
    
    print("\n📄 Generazione HTML...")
    
    total_events = 0
    for sport, evs in grouped.items():
        filename = f"KIRA_GSI_{sport}.html".replace(" ", "_")
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        count = generate_kira_html(sport, evs, filepath)
        total_events += count
        print(f"   ✅ {filename} ({count} eventi)")
    
    # File "Tutti"
    all_events = []
    for evs in grouped.values():
        all_events.extend(evs)
    
    generate_kira_html("Tutti", all_events, os.path.join(OUTPUT_DIR, "KIRA_GSI_Tutti.html"))
    print(f"   ✅ KIRA_GSI_Tutti.html ({len(all_events)} eventi)")
    
    print("\n" + "="*60)
    print(f"✅ OPERAZIONE COMPLETATA! {total_events} eventi totali")
    print(f"📁 File generati in: {OUTPUT_DIR}/")
    print("="*60)

if __name__ == "__main__":
    main()