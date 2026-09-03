#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPVTV.ICU SCRAPER - Eventi del giorno corrente
"""

import requests
import json
import re
from datetime import datetime, timedelta
from html import escape

# ============================================================
#  CONFIGURAZIONE
# ============================================================

API_URL = "https://august.ppvtv.icu/api/matches.json"
OUTPUT_HTML = "kira_ppvvt.html"
OUTPUT_M3U = "PPVTV_playlist.m3u"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0',
    'Accept': 'application/json',
    'Referer': 'https://ppvtv.icu/',
    'Origin': 'https://ppvtv.icu'
}

# ============================================================
#  FUNZIONI
# ============================================================

def fetch_matches():
    """Recupera i match da PPVTV.ICU."""
    try:
        print(f"📡 API: {API_URL}")
        response = requests.get(API_URL, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Dati ricevuti!")
            
            matches = data.get('matches', [])
            print(f"   📦 {len(matches)} match trovati")
            print(f"   🔴 LIVE: {data.get('live', 0)}")
            print(f"   📅 PROGRAMMATI: {data.get('upcoming', 0)}")
            return data
        else:
            print(f"   ❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Errore: {e}")
    
    return None

def parse_matches(data):
    """Converte i match nel formato standard."""
    if not data:
        return []
    
    matches = data.get('matches', [])
    if not matches:
        return []
    
    events = []
    today = datetime.now().date()
    
    for match in matches:
        if not isinstance(match, dict):
            continue
        
        # Titolo
        title = match.get('title', 'Evento')
        if not title:
            continue
        
        # Sport e competizione
        category = match.get('category', 'Sport')
        league = match.get('league', '')
        
        # Competizione completa
        if league:
            competition = f"{category} – {league}"
        else:
            competition = category
        
        # Orario
        time_str = 'N/A'
        start_time = match.get('start_time', '')
        if start_time:
            match_time = re.search(r'(\d{2}:\d{2})', start_time)
            if match_time:
                time_str = match_time.group(1)
        
        # Data
        date_display = 'Oggi'
        if start_time:
            match_date = re.search(r'(\d{4}-\d{2}-\d{2})', start_time)
            if match_date:
                try:
                    event_date = datetime.strptime(match_date.group(1), '%Y-%m-%d').date()
                    if event_date != today:
                        date_display = 'Domani' if event_date > today else 'Passato'
                except:
                    pass
        
        # Status
        status = match.get('status', '')
        if status == 'Live':
            status_display = '🔴 LIVE'
        else:
            status_display = '📅 PROGRAMMATO'
        
        # Link
        link = match.get('page_url', '')
        if not link:
            match_id = match.get('id', '')
            if match_id:
                link = f"https://ppvtv.icu/watch.html?match={match_id}"
        
        # Server - salva direttamente (sono già nella forma giusta)
        servers = match.get('servers', [])
        
        events.append({
            'title': title,
            'competition': competition,
            'sport': category,
            'league': league,
            'time': time_str,
            'date': date_display,
            'status': status_display,
            'link': link,
            'servers': servers,
            'match_id': match.get('id', ''),
            'source': 'PPVTV'
        })
    
    # Ordine cronologico
    events.sort(key=lambda x: (
        0 if x['date'] == 'Oggi' else 1,
        x['time']
    ))
    
    return events

def scrape_ppvtv():
    """Funzione principale."""
    today = datetime.now().strftime('%d/%m/%Y')
    
    print("="*70)
    print(f"📡 PPVTV.ICU - Eventi del {today}")
    print("="*70)
    
    data = fetch_matches()
    
    if not data:
        print("\n❌ Nessun dato ricevuto!")
        return []
    
    events = parse_matches(data)
    
    if not events:
        print("\n❌ Nessun evento trovato!")
        return []
    
    print(f"\n📊 Totale eventi: {len(events)}")
    
    # Anteprima
    print("\n📋 Anteprima eventi (primi 10):")
    for i, event in enumerate(events[:10]):
        print(f"   {i+1}. {event['title']} - {event['date']} {event['time']} - {event['competition']}")
    
    return events

def generate_html(events):
    """Genera HTML con stile KIRA."""
    today = datetime.now().strftime('%d/%m/%Y')
    
    if not events:
        return "<h1>Nessun evento trovato</h1>"
    
    # Dividi per data
    oggi = [e for e in events if e['date'] == 'Oggi']
    domani = [e for e in events if e['date'] == 'Domani']
    
    event_items = ""
    
    if oggi:
        event_items += f'''
        <div class="day-section">
            <div class="day-header" onclick="toggleDay(this)">
                📅 Oggi ({today}) <span class="day-count">({len(oggi)} eventi)</span>
                <span class="day-arrow">▼</span>
            </div>
            <div class="day-content open">
                <div class="events-grid">
        '''
        for event in oggi:
            event_items += generate_event_card(event)
        event_items += '''
                </div>
            </div>
        </div>
        '''
    
    if domani:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y')
        event_items += f'''
        <div class="day-section">
            <div class="day-header" onclick="toggleDay(this)">
                📅 Domani ({tomorrow}) <span class="day-count">({len(domani)} eventi)</span>
                <span class="day-arrow">▼</span>
            </div>
            <div class="day-content">
                <div class="events-grid">
        '''
        for event in domani:
            event_items += generate_event_card(event)
        event_items += '''
                </div>
            </div>
        </div>
        '''
    
    return f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CYBER GATE ACCESS</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Audiowide&family=Grotesk:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Grotesk', sans-serif; background: #0a0a0a; color: #00ffcc; min-height: 100vh; overflow-x: hidden; position: relative; }}
        .matrix-bg {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; background: #0a0a0a; overflow: hidden; }}
        .matrix-bg::before {{ content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 255, 204, 0.03) 2px, rgba(0, 255, 204, 0.03) 4px); animation: matrixScroll 15s linear infinite; }}
        @keyframes matrixScroll {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY(100%); }} }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; position: relative; z-index: 1; }}
        
        .header {{ text-align: center; padding: 30px 0 40px; border-bottom: 2px solid rgba(0, 255, 204, 0.3); margin-bottom: 40px; }}
        .header h1 {{ font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 3.5rem; text-shadow: 0 0 20px rgba(0, 255, 204, 0.5); background: linear-gradient(135deg, #00ffcc, #00ccff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 4px; }}
        .header .subtitle {{ font-family: 'Audiowide', cursive; color: #88ffdd; font-size: 1.2rem; margin-top: 10px; }}
        
        .event-counter {{ text-align: center; font-family: 'Orbitron', monospace; font-size: 1.2rem; color: #00ffcc; background: rgba(0, 255, 204, 0.08); border: 1px solid rgba(0, 255, 204, 0.2); padding: 12px 20px; border-radius: 30px; display: inline-block; margin: 0 auto 30px; }}
        .event-counter span {{ font-weight: 900; font-size: 1.5rem; }}
        
        .day-section {{ background: rgba(0, 30, 30, 0.5); border: 1px solid rgba(0, 255, 204, 0.15); border-radius: 15px; margin-bottom: 20px; overflow: hidden; }}
        .day-header {{ font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 1.2rem; padding: 15px 20px; background: rgba(0, 255, 204, 0.05); cursor: pointer; display: flex; justify-content: space-between; align-items: center; color: #00ffcc; user-select: none; }}
        .day-header:hover {{ background: rgba(0, 255, 204, 0.1); }}
        .day-arrow {{ transition: transform 0.3s ease; font-size: 0.8rem; }}
        .day-header.active .day-arrow {{ transform: rotate(180deg); }}
        .day-count {{ font-size: 0.8rem; color: #88ddff; opacity: 0.7; font-weight: 400; }}
        .day-content {{ max-height: 0; overflow: hidden; transition: max-height 0.5s ease-out; padding: 0 20px; }}
        .day-content.open {{ max-height: 20000px; padding: 20px; }}
        
        .events-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }}
        
        .event-card {{ background: rgba(0, 30, 30, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(0, 255, 204, 0.2); border-radius: 15px; padding: 20px; transition: all 0.3s ease; display: flex; flex-direction: column; }}
        .event-card:hover {{ transform: translateY(-5px); border-color: rgba(0, 255, 204, 0.6); box-shadow: 0 0 40px rgba(0, 255, 204, 0.15); }}
        .event-info h3 {{ font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 1.1rem; color: #00ffcc; margin-bottom: 8px; display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }}
        .event-info .sport-badge {{ font-family: 'Audiowide', cursive; color: #88ddff; font-size: 0.8rem; background: rgba(0, 255, 204, 0.1); padding: 3px 12px; border-radius: 20px; display: inline-block; margin-bottom: 8px; }}
        .event-info .datetime {{ color: #88ddff; font-size: 0.85rem; opacity: 0.8; }}
        .fonte-badge {{ display: inline-block; font-size: 0.7rem; background: rgba(0, 255, 204, 0.15); color: #88ffdd; padding: 2px 12px; border-radius: 12px; margin-top: 5px; border: 1px solid rgba(0, 255, 204, 0.2); }}
        .status-live {{ display: inline-block; font-size: 0.7rem; background: rgba(255, 0, 0, 0.3); color: #ff4444; padding: 2px 10px; border-radius: 12px; animation: pulse 1.5s ease-in-out infinite; }}
        .status-next {{ display: inline-block; font-size: 0.7rem; background: rgba(0, 100, 255, 0.3); color: #4488ff; padding: 2px 10px; border-radius: 12px; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} }}
        .event-links {{ margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(0, 255, 204, 0.15); }}
        .server-link {{ display: inline-block; font-family: 'Orbitron', monospace; font-weight: 700; color: #0a0a0a; background: #00ffcc; padding: 10px 20px; border-radius: 8px; text-decoration: none; text-align: center; width: 100%; transition: all 0.3s ease; font-size: 0.8rem; }}
        .server-link:hover {{ background: #00ddbb; box-shadow: 0 0 40px rgba(0, 255, 204, 0.5); }}
        .no-link {{ display: inline-block; font-family: 'Orbitron', monospace; color: #666; text-align: center; width: 100%; padding: 10px; }}
        
        .footer {{ text-align: center; padding: 40px 0 20px; margin-top: 40px; border-top: 1px solid rgba(0, 255, 204, 0.2); color: #88ddff; opacity: 0.7; }}
        .footer .neon-text {{ font-family: 'Orbitron', monospace; color: #00ffcc; font-size: 1rem; }}
        
        @media (max-width: 768px) {{ .header h1 {{ font-size: 2rem; }} .events-grid {{ grid-template-columns: 1fr; }} .container {{ padding: 15px; }} }}
    </style>
</head>
<body>
    <div class="matrix-bg"></div>
    <div class="container">
        <header class="header">
            <h1>KIRA CYBER GATE</h1>
            <p class="subtitle">• Eventi di Oggi •</p>
        </header>
        
        <div style="text-align: center;">
            <div class="event-counter">
                🎯 <span>{len(events)}</span> eventi disponibili
            </div>
        </div>
        
        <div id="days-container">
            {event_items}
        </div>
        
        <footer class="footer">
            <p class="neon-text">KIRA GSI SPORT • Eventi in Diretta • {datetime.now().year} • Developed by KIRA GSI GROUP</p>
        </footer>
    </div>
    
    <script>
        function toggleDay(header) {{
            header.classList.toggle('active');
            const content = header.nextElementSibling;
            content.classList.toggle('open');
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            const headers = document.querySelectorAll('.day-header');
            if (headers.length > 0) {{
                toggleDay(headers[0]);
            }}
        }});
    </script>
</body>
</html>'''

def generate_event_card(event):
    """Genera una card HTML per un singolo evento."""
    link = event.get('link')
    
    status_badge = ''
    if 'LIVE' in event['status']:
        status_badge = '<span class="status-live">🔴 LIVE</span>'
    else:
        status_badge = '<span class="status-next">⏳ PROGRAMMATO</span>'
    
    if link:
        links_html = f'<a href="{link}" target="_blank" class="server-link">▶ GUARDA IN DIRETTA</a>'
    else:
        links_html = '<span class="no-link">🔗 Link non disponibile</span>'
    
    return f'''
    <div class="event-card">
        <div class="event-info">
            <h3>{escape(event['title'])} {status_badge}</h3>
            <p class="sport-badge">🏆 {escape(event['competition'])}</p>
            <p class="datetime">🕒 {escape(event['time'])} • 📅 {event['date']}</p>
            <span class="fonte-badge">📡 {escape(event['source'])}</span>
        </div>
        <div class="event-links">
            {links_html}
        </div>
    </div>
    '''

def generate_m3u(events):
    """Genera playlist M3U con tutti i server per ogni evento."""
    if not events:
        return "#EXTM3U\n"
    
    lines = ["#EXTM3U"]
    lines.append('#EXTINF:-1 tvg-logo="",KIRA PPVTV - Playlist')
    lines.append("")
    
    for event in events:
        title = event['title']
        competition = event.get('competition', 'PPVTV')
        time = event.get('time', '')
        date = event.get('date', '')
        
        # Estrai i server (già lista di dizionari)
        servers = event.get('servers', [])
        
        if servers and isinstance(servers, list):
            # Se ci sono server, crea un canale per ognuno
            for server in servers:
                if isinstance(server, dict):
                    server_name = server.get('name', 'Server')
                    embed_url = server.get('embed_url', '')
                    
                    if embed_url:
                        lines.append(f'#EXTINF:-1 group-title="{competition}",{date} {time} - {title} [{server_name}]')
                        lines.append(embed_url)
                        lines.append("")
        else:
            # Fallback: usa il link principale
            main_link = event.get('link')
            if main_link:
                lines.append(f'#EXTINF:-1 group-title="{competition}",{date} {time} - {title}')
                lines.append(main_link)
                lines.append("")
    
    return '\n'.join(lines)

def main():
    events = scrape_ppvtv()
    
    if not events:
        print("\n❌ Nessun evento trovato!")
        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write("<h1>Nessun evento trovato</h1>")
        with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
        return
    
    html_content = generate_html(events)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"\n✅ HTML generato: {OUTPUT_HTML}")
    
    m3u_content = generate_m3u(events)
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"✅ M3U generato: {OUTPUT_M3U}")
    
    print(f"\n📊 Totale eventi: {len(events)}")

if __name__ == "__main__":
    main()