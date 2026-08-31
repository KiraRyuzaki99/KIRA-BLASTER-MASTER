#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DADDYLIVE AUTO - Cattura TUTTE le categorie (generiche + specifiche per TUTTI gli sport)
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
OUTPUT_DIR = "daddy_output"

# ============================================================
#  CATEGORIE REALI - TUTTI GLI SPORT
#  Ogni sport ha: nomi generici + nomi specifici delle competizioni
# ============================================================

SPORT_CATEGORIES = {

    # ===================== CALCIO =====================
    "Calcio": [
        # Nomi generici
        "soccer", "football", "all soccer events", "calcio",
        # Competizioni mondiali
        "world cup", "mondiali", "coppa del mondo",
        "champions league", "uefa champions league", "europa league", "conference league",
        # Inghilterra
        "premier league", "english premier league", "championship", "league one", "league two", "fa cup",
        # Italia
        "serie a", "serie b", "serie c", "coppa italia", "supercoppa italiana",
        # Spagna
        "la liga", "spain - la liga", "segunda division", "copa del rey",
        # Germania
        "bundesliga", "2. bundesliga", "3. liga", "dfb pokal",
        # Francia
        "ligue 1", "ligue 2", "coupe de france",
        # Portogallo
        "primeira liga", "portuguese primeira liga", "taça de portugal",
        # Olanda
        "eredivisie", "keuken kampioen divisie", "knvb beker",
        # Turchia
        "super lig", "turkish super lig", "1. lig",
        # Svezia
        "allsvenskan", "superettan",
        # Finlandia
        "veikkausliiga", "ykkönen",
        # Polonia
        "ekstraklasa", "i liga",
        # Repubblica Ceca
        "nike liga", "fortuna liga",
        # Svizzera
        "super league", "challenge league",
        # Belgio
        "pro league", "jupiler pro league",
        # Grecia
        "super league greece", "super league 2",
        # Russia
        "premier league russia", "russian premier league",
        # Ucraina
        "premier league ukraine", "ukrainian premier league",
        # Scozia
        "scottish premiership", "scottish championship",
        # Altri campionati
        "eredivisie", "liga nos", "liga mx", "mls", "a-league",
        "j league", "k league", "csl", "ligue",
        "coppa", "cup", "pokal", "trophy", "league", "liga", "serie", "bundes"
    ],

    # ===================== TENNIS =====================
    "Tennis": [
        # Nomi generici
        "tennis", "all tennis",
        # Grand Slam
        "us open", "wimbledon", "roland garros", "french open", "australian open",
        # Circuiti ATP/WTA
        "atp", "wta", "atp tour", "wta tour",
        "masters 1000", "masters", "grand slam",
        "challenger", "challenger tour", "futures",
        "davis cup", "billie jean king cup", "laver cup",
        "abierto de", "open de", "open"
    ],

    # ===================== BASKET =====================
    "Basket": [
        # Nomi generici
        "basketball", "basket", "baloncesto", "all basketball",
        # NBA
        "nba", "national basketball association",
        "euroleague", "eurocup", "basketball champions league",
        # Spagna
        "liga acb", "spain basketball league",
        # Italia
        "serie a basket", "italian basketball league",
        # Germania
        "bbl", "german basketball league",
        # Francia
        "lnb", "french basketball league",
        # NCAA
        "ncaa", "college basketball", "march madness",
        # Altri
        "liga endesa", "leb oro", "ligue nationale", 
        "world cup basketball", "olympics basketball"
    ],

    # ===================== HOCKEY =====================
    "Hockey": [
        # Nomi generici
        "hockey", "ice hockey", "all hockey",
        # NHL
        "nhl", "national hockey league",
        # Europa
        "liiga", "shl", "extraliga", "czech extraliga",
        "del", "german ice hockey league",
        "national league", "swiss ice hockey",
        "khl", "russian hockey league",
        # Canada/USA
        "ohl", "whl", "qmjhl", "ahl",
        # Champions
        "champions hockey league",
        # Altri
        "world championship hockey", "olympics hockey"
    ],

    # ===================== BASEBALL =====================
    "Baseball": [
        # Nomi generici
        "baseball", "all baseball",
        # MLB
        "mlb", "major league baseball",
        # Giappone
        "npb", "nippon professional baseball",
        # Corea
        "kbo", "korean baseball organization",
        # Taiwan
        "cpbl", "chinese professional baseball league",
        # Altri
        "world series", "little league",
        "college baseball", "world baseball classic"
    ],

    # ===================== RUGBY =====================
    "Rugby": [
        # Nomi generici
        "rugby", "all rugby",
        # Internazionali
        "six nations", "6 nazioni",
        "champions cup", "challenge cup",
        "world cup rugby",
        # Inghilterra
        "super league", "rugby super league",
        # Australia
        "nrl", "national rugby league",
        # Francia
        "top 14", "pro d2",
        # Sudafrica/NZ/Australia
        "united rugby championship", "super rugby",
        "currie cup", "mitre 10 cup"
    ],

    # ===================== SURF =====================
    "Surf": [
        # Nomi generici
        "surf", "surfing", "all surf",
        # WSL
        "world surf league", "wsl",
        # Eventi
        "fiji pro", "j-bay", "tahiti pro", "pipe masters",
        "gold coast", "bells beach", "margaret river",
        "championship tour", "wsl championship tour",
        "big wave", "big wave tour"
    ],

    # ===================== NUOTO =====================
    "Nuoto": [
        # Nomi generici
        "swimming", "nuoto", "all swimming",
        # Internazionali
        "fina world cup", "world swimming championships",
        "world aquatics championships",
        # Olimpiadi
        "olympics swimming", "olympic swimming",
        # Eventi
        "marathon swimming", "open water swimming",
        "world junior championships", "world masters"
    ],

    # ===================== VOLLEY / PALL. VOLO =====================
    "Voleibol": [
        # Nomi generici
        "volleyball", "voley", "volley", "all volleyball",
        # World League
        "fivb world league", "world league",
        "national league volleyball",
        # Internazionali
        "world cup volleyball",
        "olympics volleyball", "olympics volleyball",
        # Leghe europee
        "champions league volleyball",
        "cev champions league", "cev cup",
        # Nazionali
        "serie a volleyball", "italian volleyball",
        "plusliga", "polish volleyball",
        "superliga", "russian volleyball",
        "liga de voleibol", "spanish volleyball"
    ],

    # ===================== BALONMANO =====================
    "Balonmano": [
        # Nomi generici
        "handball", "balonmano", "all handball",
        # EHF
        "ehf champions league", "ehf cup", "european handball",
        # World
        "world handball championship", "world cup handball",
        # Leghe
        "hbl", "handball bundesliga",
        "liga asobal", "spanish handball",
        "liga de handball", "french handball",
        "olympics handball"
    ],

    # ===================== PUGILATO / MMA =====================
    "Pugilato": [
        # Nomi generici
        "boxing", "pugilato", "all boxing",
        "ufc", "mma", "mixed martial arts",
        "bellator", "one championship",
        # Eventi
        "heavyweight", "lightweight", "welterweight",
        "world championship boxing",
        "fight night", "main event"
    ],

    # ===================== GOLF =====================
    "Golf": [
        # Nomi generici
        "golf", "all golf",
        # PGA
        "pga", "pga tour",
        # Europe
        "european tour", "dp world tour",
        # Major
        "masters", "the masters",
        "ryder cup", "presidents cup",
        "the open", "open championship",
        "pga championship", "us open golf",
        # Altri
        "lpga", "ladies pga tour",
        "champions tour", "senior tour",
        "ryder cup", "solheim cup"
    ],

    # ===================== CICLISMO =====================
    "Ciclismo": [
        # Nomi generici
        "cycling", "ciclismo", "all cycling",
        # Grandi giri
        "tour de france", "tour de france",
        "giro d'italia", "la vuelta", "vuelta a españa",
        # World Tour
        "world tour cycling",
        # Classiche
        "monument", "classics",
        # Altri
        "world championships cycling",
        "olympics cycling", "track cycling",
        "mountain bike", "cyclocross"
    ],

    # ===================== ATLETICA =====================
    "Atletica": [
        # Nomi generici
        "athletics", "atletica", "track and field",
        # Diamond League
        "diamond league", "golden league",
        # World
        "world championships athletics",
        "world athletics",
        # Olimpiadi
        "olympics athletics",
        # Eventi
        "marathon", "half marathon",
        "100m", "200m", "400m", "800m", "1500m",
        "relay", "hurdles", "steeplechase",
        "long jump", "high jump", "pole vault",
        "shot put", "discus", "javelin"
    ],

    # ===================== SPORT INVERNALI =====================
    "Invernali": [
        # Nomi generici
        "winter sports", "sport invernali",
        "ski", "snowboard", "biathlon",
        # World Cup
        "world cup skiing", "alpine skiing",
        "fis world cup",
        # Figure skating
        "figure skating", "speed skating",
        "short track", "ice skating",
        # Altri
        "winter olympics", "olympics winter",
        "cross-country skiing", "ski jumping",
        "nordic combined", "bobsleigh", "luge", "skeleton"
    ],

    # ===================== MOTORI / AUTO =====================
    "Motori": [
        # Nomi generici
        "motorsport", "motorsport",
        # Formula
        "formula 1", "f1", "formula 2", "f2", "formula 3", "f3",
        "formula e", "formula e",
        # Moto
        "motogp", "superbike", "world superbike",
        # Rally
        "rally", "wrc", "world rally championship",
        # Altri
        "nascar", "indycar", "indy 500",
        "wec", "imsa", "btcc", "dtm",
        "touring car", "gt racing", "endurance"
    ],

    # ===================== SPORT ESCLUSI =====================
    "Esclusi": [
        "advertisement", "sponsor", "promo", "bonus",
        "casino", "betting", "slot", "live chat",
        "no event", "coming soon", "off air",
        "banner", "ad", "partners", "affiliate",
        "stream", "watch", "link", "click"
    ]
}

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
        return None
    except:
        return None

def detect_sport(category, event_title=""):
    """Rileva lo sport usando TUTTE le categorie (generiche + specifiche)."""
    text = f"{category} {event_title}".lower()
    
    # Prima controlla se è escluso
    for word in SPORT_CATEGORIES["Esclusi"]:
        if word in text:
            return "Esclusi"
    
    # Controlla ogni sport
    for sport, keywords in SPORT_CATEGORIES.items():
        if sport == "Esclusi":
            continue
        for kw in keywords:
            if kw in text:
                return sport
    
    return "Altri"

def fetch_all_matches():
    """Scarica tutti gli eventi."""
    all_events = []
    
    print(" Scaricamento eventi da DaddyLive...")
    
    for i in range(1, 10):
        filename = f"tv{i}.json"
        url = ENDPOINT_BASE + filename
        print(f"    {filename}...", end=" ")
        
        data = fetch_json(url)
        if not data:
            print("")
            continue
        
        print("")
        
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
                        if sport == "Esclusi":
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
    
    print(f"\n    Trovati {len(all_events)} eventi totali")
    return all_events

def group_and_generate(events):
    """Raggruppa e genera HTML per ogni sport."""
    grouped = defaultdict(list)
    for event in events:
        grouped[event['sport']].append(event)
    
    print("\n Statistiche per sport:")
    for sport, evs in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"    {sport}: {len(evs)} eventi")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    total_events = 0
    for sport, evs in grouped.items():
        evs.sort(key=lambda x: f"{x['date']}_{x['time']}")
        filename = f"KIRA_GSI_{sport}.html".replace(" ", "_").replace("/", "_")
        filepath = os.path.join(OUTPUT_DIR, filename)
        count = generate_html_for_sport(sport, evs, filepath)
        total_events += count
        print(f"    {filename} ({count} eventi)")
    
    # Tutti
    all_events = []
    for evs in grouped.values():
        all_events.extend(evs)
    generate_html_for_sport("Tutti", all_events, os.path.join(OUTPUT_DIR, "KIRA_GSI_Tutti.html"))
    print(f"    KIRA_GSI_Tutti.html ({len(all_events)} eventi)")
    
    return total_events

def generate_html_for_sport(sport, events, output_file):
    """Genera HTML con stile KIRA GSI."""
    event_items = ""
    for event in events:
        valid_links = event['links'][:5]
        
        if len(valid_links) > 1:
            options = "\n".join([f'<option value="{l}">Canale {i+1}</option>' for i, l in enumerate(valid_links)])
            links_html = f'''
            <div class="dropdown">
                <select onchange="window.open(this.value, '_blank'); this.selectedIndex=0;">
                    <option value=""> Scegli il canale...</option>
                    {options}
                </select>
            </div>
            '''
        elif len(valid_links) == 1:
            links_html = f'<a href="{valid_links[0]}" target="_blank" class="server-link"> GUARDA IN DIRETTA</a>'
        else:
            links_html = '<span class="no-link"> Link non disponibile</span>'
        
        event_items += f'''
        <div class="event-card">
            <div class="event-info">
                <h3>{escape(event['title'])}</h3>
                <p class="competition"> {escape(event['category'])}</p>
                <p class="datetime"> {escape(event['time'])} •  {escape(event['date'])}</p>
                <span class="fonte-badge"> {escape(event['sport'])}</span>
            </div>
            <div class="event-links">
                {links_html}
            </div>
        </div>
        '''
    
    if not event_items:
        event_items = '<p style="text-align:center;color:#666;">Nessun evento trovato.</p>'
    
    html = f'''<!DOCTYPE html>
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
            gap: 25px;
            margin-top: 20px;
        }}
        
        .event-card {{
            background: rgba(0, 30, 30, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 255, 204, 0.2);
            border-radius: 15px;
            padding: 25px;
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
            font-size: 1.2rem;
            color: #00ffcc;
            margin-bottom: 8px;
        }}
        .event-info .competition {{
            font-family: 'Audiowide', cursive;
            color: #88ddff;
            font-size: 0.85rem;
            background: rgba(0, 255, 204, 0.1);
            padding: 4px 12px;
            border-radius: 20px;
            display: inline-block;
            margin-bottom: 10px;
        }}
        .event-info .datetime {{
            color: #88ddff;
            font-size: 0.9rem;
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
        .event-links {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(0, 255, 204, 0.15);
        }}
        .server-link {{
            display: inline-block;
            font-family: 'Orbitron', monospace;
            font-weight: 700;
            color: #0a0a0a;
            background: #00ffcc;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            text-align: center;
            width: 100%;
            transition: all 0.3s ease;
            font-size: 0.85rem;
        }}
        .server-link:hover {{
            background: #00ddbb;
            box-shadow: 0 0 40px rgba(0, 255, 204, 0.5);
        }}
        .dropdown select {{
            width: 100%;
            padding: 12px 15px;
            background: rgba(0, 20, 20, 0.9);
            color: #00ffcc;
            border: 1px solid rgba(0, 255, 204, 0.4);
            border-radius: 10px;
            font-family: 'Orbitron', monospace;
            font-size: 0.85rem;
            cursor: pointer;
            outline: none;
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
            margin-top: 60px;
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
        }}
    </style>
</head>
<body>
    <div class="matrix-bg"></div>
    <div class="container">
        <header class="header">
            <h1> KIRA GSI </h1>
            <p class="subtitle">• {sport} - Eventi in Diretta •</p>
        </header>
        
        <div style="text-align: center;">
            <div class="event-counter">
                 <span>{len(events)}</span> eventi disponibili
            </div>
        </div>
        
        <div class="events-grid">
            {event_items}
        </div>
        
        <footer class="footer">
            <p class="neon-text"> KIRA GSI • Eventi in diretta • {datetime.now().year}</p>
        </footer>
    </div>
</body>
</html>'''
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    return len(events)

# ============================================================
#  MAIN
# ============================================================

def main():
    print("="*70)
    print(" KIRA GSI - DaddyLive Auto (TUTTI gli sport)")
    print("="*70)
    
    events = fetch_all_matches()
    
    if not events:
        print(" Nessun evento trovato!")
        return
    
    total = group_and_generate(events)
    
    print("\n" + "="*70)
    print(f" OPERAZIONE COMPLETATA! {total} eventi totali")
    print(f" File generati in: {OUTPUT_DIR}/")
    print("="*70)

if __name__ == "__main__":
    main()