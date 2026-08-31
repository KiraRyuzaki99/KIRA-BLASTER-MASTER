#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DADDYLIVE AUTO - Genera HTML automatici per ogni sport
"""

import requests
import json
import os
import re
from datetime import datetime
from collections import defaultdict

# ============================================================
#  CONFIGURAZIONE
# ============================================================

ENDPOINT_BASE = "https://daddylive.li/player/"
OUTPUT_DIR = "output"

# Mappatura sport e parole chiave
SPORT_KEYWORDS = {
    "Calcio": ["soccer", "football", "serie a", "premier league", "bundesliga", "la liga", 
               "ligue 1", "eredivisie", "primeira liga", "champions league", "europa league",
               "ligue", "league", "serie", "bundes", "calcio", "football"],
    "Tennis": ["tennis", "atp", "wta", "us open", "wimbledon", "australian open", "roland garros"],
    "Basket": ["basketball", "nba", "euroleague", "liga acb", "ncaa", "basket"],
    "Hockey": ["hockey", "nhl", "liiga", "shl", "extraliga"],
    "Motori": ["formula", "f1", "motogp", "superbike", "rally", "nascar", "automobilismo"],
    "Ciclismo": ["cycling", "tour de france", "giro d'italia", "la vuelta", "ciclismo"],
    "Rugby": ["rugby", "super league", "nrl", "6 nazioni"],
    "Voleibol": ["volleyball", "voley", "volley"],
    "Balonmano": ["handball", "balonmano"],
    "Pugilato": ["boxing", "pugilato", "ufc", "mma"],
    "Golf": ["golf", "pga", "the open"],
    "Altri": ["sport", "event"]
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
    """Scarica un file JSON."""
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
    """Rileva lo sport in base alle parole chiave."""
    text = f"{category_name} {event_name}".lower()
    
    for sport, keywords in SPORT_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return sport
    
    return "Altri"

def fetch_all_matches():
    """Scarica tutti i file JSON e restituisce gli eventi."""
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
        
        # Estrai eventi
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
                    if not isinstance(categoria, str):
                        categoria = "Generale"
                    
                    lista_eventi = block.get('events', [])
                    if not isinstance(lista_eventi, list):
                        continue
                    
                    for evento in lista_eventi:
                        if not isinstance(evento, dict):
                            continue
                        
                        titolo = evento.get('event', 'Evento')
                        orario = evento.get('time', 'N/A')
                        canali = evento.get('channels', [])
                        
                        # Estrai link
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
                        
                        if links:
                            sport = detect_sport(categoria, titolo)
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
    """Raggruppa gli eventi per sport."""
    grouped = defaultdict(list)
    for event in events:
        grouped[event['sport']].append(event)
    return grouped

def generate_html_for_sport(sport, events, output_file):
    """Genera un file HTML per uno sport specifico."""
    
    # Ordina per data/ora
    events.sort(key=lambda x: f"{x['date']}_{x['time']}")
    
    # Costruisci HTML
    events_html = ""
    for event in events:
        # Crea i bottoni per i canali
        buttons_html = ""
        for link in event['links'][:5]:  # Max 5 canali
            channel_name = link.split('id=')[-1] if 'id=' in link else 'Canale'
            buttons_html += f'<a href="{link}" target="_blank" class="channel-btn">▶ {channel_name}</a>'
        
        events_html += f'''
        <div class="evento-card">
            <div class="evento-meta">📅 {event['date']} | 🕒 {event['time']}</div>
            <div class="evento-titolo">{event['title']}</div>
            <div class="categoria-tag">🏷️ {event['category']}</div>
            <div class="canali-container">
                {buttons_html}
            </div>
        </div>
        '''
    
    # Se non ci sono eventi, genera un messaggio
    if not events_html:
        events_html = '<p style="text-align:center;color:#666;">Nessun evento trovato per questo sport.</p>'
    
    # Template HTML
    html = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KIRA - {sport}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e17;
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        
        .header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid #00ffcc;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2.5rem;
            background: linear-gradient(135deg, #00ffcc, #00aaff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header .subtitle {{
            color: #8899bb;
            font-size: 1rem;
        }}
        .header .stats {{
            color: #556688;
            font-size: 0.85rem;
            margin-top: 10px;
        }}
        
        .evento-card {{
            background: rgba(0, 30, 30, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 255, 204, 0.15);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }}
        .evento-card:hover {{
            transform: translateY(-3px);
            border-color: rgba(0, 255, 204, 0.4);
            box-shadow: 0 0 30px rgba(0, 255, 204, 0.05);
        }}
        .evento-meta {{
            font-size: 0.75rem;
            color: #88ddff;
            opacity: 0.7;
            margin-bottom: 5px;
            font-family: 'Courier New', monospace;
        }}
        .evento-titolo {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #00ffcc;
            margin-bottom: 5px;
        }}
        .categoria-tag {{
            display: inline-block;
            font-size: 0.7rem;
            background: rgba(0, 255, 204, 0.1);
            color: #88ddff;
            padding: 2px 12px;
            border-radius: 12px;
            margin-bottom: 12px;
            border: 1px solid rgba(0, 255, 204, 0.15);
        }}
        .canali-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .channel-btn {{
            background: #00ffcc;
            color: #0a0a0a;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-block;
        }}
        .channel-btn:hover {{
            background: #00ddbb;
            box-shadow: 0 0 20px rgba(0, 255, 204, 0.3);
            transform: scale(1.02);
        }}
        
        .footer {{
            text-align: center;
            padding: 30px 0;
            margin-top: 30px;
            border-top: 1px solid rgba(0, 255, 204, 0.1);
            color: #556688;
            font-size: 0.8rem;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.8rem; }}
            .evento-titolo {{ font-size: 0.95rem; }}
            .channel-btn {{ font-size: 0.7rem; padding: 6px 12px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>⚡ {sport} ⚡</h1>
            <p class="subtitle">Eventi in diretta da DaddyLive</p>
            <p class="stats">📅 {datetime.now().strftime('%d/%m/%Y %H:%M')} • {len(events)} eventi</p>
        </header>
        
        {events_html}
        
        <footer class="footer">
            <p>KIRA • DaddyLive • {datetime.now().year}</p>
        </footer>
    </div>
</body>
</html>'''
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    return len(events)

def main():
    print("="*60)
    print("📡 DADDYLIVE AUTO - Generazione automatica per sport")
    print("="*60)
    
    # 1. Scarica tutti i dati
    events = fetch_all_matches()
    
    if not events:
        print("❌ Nessun evento trovato!")
        return
    
    # 2. Raggruppa per sport
    grouped = group_by_sport(events)
    
    print("\n📊 Statistiche per sport:")
    for sport, evs in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"   🏆 {sport}: {len(evs)} eventi")
    
    # 3. Genera HTML per ogni sport
    print("\n📄 Generazione HTML...")
    
    # Crea la cartella output se non esiste
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    total_events = 0
    for sport, evs in grouped.items():
        # Sanitizza il nome per il file
        filename = f"Daddy_{sport}.html".replace(" ", "_")
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        count = generate_html_for_sport(sport, evs, filepath)
        total_events += count
        print(f"   ✅ {filename} ({count} eventi)")
    
    # 4. Genera anche un file "Tutti" con tutto insieme
    all_events = []
    for evs in grouped.values():
        all_events.extend(evs)
    
    generate_html_for_sport("Tutti", all_events, os.path.join(OUTPUT_DIR, "Daddy_Tutti.html"))
    print(f"   ✅ Daddy_Tutti.html ({len(all_events)} eventi)")
    
    print("\n" + "="*60)
    print(f"✅ OPERAZIONE COMPLETATA! {total_events} eventi totali")
    print(f"📁 File generati in: {OUTPUT_DIR}/")
    print("="*60)

if __name__ == "__main__":
    main()