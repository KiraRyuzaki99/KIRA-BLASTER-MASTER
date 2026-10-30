#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER SPORTORA - Tutti gli eventi del giorno corrente
"""

from curl_cffi import requestsas curl_requests
import json
import re
from datetime import datetime, timedelta
from html import escape

# ============================================================
#  CONFIGURAZIONE
# ============================================================

BASE_URL = "https://sportora.ru"
OUTPUT_HTML = "kira_tora.html"
OUTPUT_M3U = "KIRA_TORA.m3u"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0',
    'Accept': 'application/json',
    'Referer': 'https://sportora.ru/',
    'X-Requested-With': 'XMLHttpRequest'
}

# ============================================================
#  FUNZIONI
# ============================================================

def fetch_events():
    """Recupera gli eventi da sportora.ru usando curl_cffi."""
    url = f"{BASE_URL}/data/matches.json"
    params = {
        "_": int(datetime.now().timestamp() * 1000)
    }
    
    try:
        print(f"📡 Chiamata API: {url}")
        response = curl_requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=20,
            impersonate="chrome124"
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        
        if response.status_code == 200:
            # Controlla che sia davvero JSON e non HTML di errore
            content_type = response.headers.get('content-type', '')
            if 'json' not in content_type:
                print("   ⚠️ Risposta non JSON (possibile blocco Cloudflare)")
                print(f"   Anteprima: {response.text[:200]}")
                return []
            
            data = response.json()
            matches = data.get('matches', [])
            print(f"   ✅ Trovati {len(matches)} match totali")
            return matches
        else:
            print(f"⚠️ Errore HTTP: {response.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ Errore: {e}")
        return []

def extract_date_from_match(match):
    """Estrae la data dal match."""
    timing = match.get('timing', {})
    
    if isinstance(timing, dict):
        readable = timing.get('readable', '')
        if readable:
            match_date = re.search(r'(\d{4}-\d{2}-\d{2})', readable)
            if match_date:
                try:
                    return datetime.strptime(match_date.group(1), '%Y-%m-%d').date()
                except:
                    pass
        
        start_ms = timing.get('start_ms')
        if start_ms:
            try:
                return datetime.fromtimestamp(start_ms / 1000).date()
            except:
                pass
    
    return None

def extract_time_from_match(match):
    """Estrae l'orario dal match e aggiunge 1 ora."""
    timing = match.get('timing', {})
    
    if isinstance(timing, dict):
        readable = timing.get('readable', '')
        if readable:
            match_time = re.search(r'(\d{2}:\d{2})', readable)
            if match_time:
                time_str = match_time.group(1)
                try:
                    # Aggiunge 1 ora all'orario dell'API
                    dt = datetime.strptime(time_str, '%H:%M')
                    dt = dt + timedelta(hours=1)
                    return dt.strftime('%H:%M')
                except:
                    return time_str
    
    return "N/A"

def get_status(match):
    """Determina lo stato dell'evento."""
    timing = match.get('timing', {})
    if isinstance(timing, dict):
        status = timing.get('status', '')
        if status:
            return status.lower()
    
    return "scheduled"

def extract_links(match):
    """Estrae i link dagli streams."""
    links = []
    streams = match.get('streams', [])
    
    if isinstance(streams, list):
        for stream in streams:
            if isinstance(stream, dict):
                embed_url = stream.get('embed_url', '')
                if embed_url and embed_url.startswith('http'):
                    links.append(embed_url)
                
                for key in ['url', 'link', 'stream']:
                    if key in stream:
                        val = stream[key]
                        if isinstance(val, str) and val.startswith('http'):
                            links.append(val)
    
    if not links:
        match_id = match.get('id')
        if match_id:
            links.append(f"{BASE_URL}/watch/{match_id}")
    
    unique_links = []
    seen = set()
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    return unique_links

def scrape_sportora():
    """Funzione principale."""
    today = datetime.now().date()
    
    print("="*70)
    print(f"📡 SPORTORA SCRAPER - Eventi del {today.strftime('%d/%m/%Y')}")
    print("📌 Tutti gli sport - Orari originali dell'API")
    print("="*70)
    
    matches = fetch_events()
    
    if not matches:
        print("❌ Nessun match trovato")
        return []
    
    events_with_links = []
    stats = {
        'total': len(matches),
        'no_date': 0,
        'wrong_date': 0,
        'no_links': 0,
        'accepted': 0,
        'finished': 0
    }
    
    print(f"\n📊 Analisi di {len(matches)} eventi...")
    
    for match in matches:
        if not isinstance(match, dict):
            continue
        
        event_date = extract_date_from_match(match)
        
        if event_date is None:
            stats['no_date'] += 1
            continue
        
        if event_date != today:
            stats['wrong_date'] += 1
            continue
        
        title = match.get('title', 'Evento Sportivo')
        
        category = match.get('category', {})
        if isinstance(category, dict):
            sport = category.get('name', 'Sport')
        else:
            sport = str(category) if category else 'Sport'
        
        # ORARIO ORIGINALE DELL'API - SENZA ALCUNA CONVERSIONE
        time_str = extract_time_from_match(match)
        
        status = get_status(match)
        
        if status == 'finished':
            stats['finished'] += 1
            continue
        
        links = extract_links(match)
        
        if not links:
            stats['no_links'] += 1
            continue
        
        events_with_links.append({
            'title': title,
            'sport': sport,
            'time': time_str,  # Orario originale dell'API
            'status': status,
            'links': links[:5],
            'source': 'Sportora'
        })
        stats['accepted'] += 1
    
    print(f"\n📊 Statistiche filtri:")
    print(f"   ✅ Accettati (oggi, non finiti): {stats['accepted']}")
    print(f"   ⏭️ Senza data: {stats['no_date']}")
    print(f"   ⏭️ Data diversa da oggi: {stats['wrong_date']}")
    print(f"   ⏭️ Già finiti: {stats['finished']}")
    print(f"   ⏭️ Senza link: {stats['no_links']}")
    
    return events_with_links

def generate_html(events):
    """Genera la pagina HTML."""
    today = datetime.now().strftime('%d/%m/%Y')
    
    if not events:
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Kira Sportora</title></head>
<body><h1>Nessun evento trovato per oggi</h1></body>
</html>"""
    
    event_items = ""
    for event in events:
        valid_links = event['links']
        
        status_badge = ""
        if event['status'] == 'live':
            status_badge = '<span class="status-live">🔴 LIVE</span>'
        else:
            status_badge = '<span class="status-next">⏳ PROSSIMO</span>'
        
        if len(valid_links) > 1:
            options = "\n".join([f'<option value="{l}">Canale {i+1}</option>' for i, l in enumerate(valid_links)])
            links_html = f'''
            <div class="dropdown">
                <select onchange="window.open(this.value, '_blank'); this.selectedIndex=0;">
                    <option value="">📡 Scegli il canale...</option>
                    {options}
                </select>
            </div>
            '''
        elif len(valid_links) == 1:
            links_html = f'<a href="{valid_links[0]}" target="_blank" class="server-link">▶ GUARDA IN DIRETTA</a>'
        else:
            links_html = '<span class="no-link">🔗 Link non disponibile</span>'
        
        event_items += f'''
        <div class="event-card">
            <div class="event-info">
                <h3>{escape(event['title'])} {status_badge}</h3>
                <p class="sport-badge">🏆 {escape(event['sport'])}</p>
                <p class="datetime">🕒 {escape(event['time'])} • 📅 {today}</p>
                <span class="fonte-badge">📡 {escape(event['source'])}</span>
            </div>
            <div class="event-links">
                {links_html}
            </div>
        </div>
        '''
    
    return f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>CYBER GATE ACCESS</title>
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
            font-size: 1.1rem;
            color: #00ffcc;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .event-info .sport-badge {{
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
        .status-live {{
            display: inline-block;
            font-size: 0.7rem;
            background: rgba(255, 0, 0, 0.3);
            color: #ff4444;
            padding: 2px 10px;
            border-radius: 12px;
            animation: pulse 1.5s ease-in-out infinite;
        }}
        .status-next {{
            display: inline-block;
            font-size: 0.7rem;
            background: rgba(0, 100, 255, 0.3);
            color: #4488ff;
            padding: 2px 10px;
            border-radius: 12px;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.4; }}
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
        .dropdown select option {{
            background: #0a1a1a;
            color: #88ffdd;
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
            <h1>KIRA GATE ACCESS</h1>
            <p class="subtitle">• Eventi di Oggi •</p>
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
            <p class="neon-text">KIRA GSI SPORT • Eventi in Diretta • {datetime.now().year} • Developed by KIRA GSI GROUP</p>
        </footer>
    </div>
</body>
</html>'''

def generate_m3u(events):
    """Genera playlist M3U."""
    if not events:
        return "#EXTM3U\n"
    
    lines = ["#EXTM3U"]
    lines.append('#EXTINF:-1 tvg-logo="",KIRA Sportora - Playlist')
    lines.append("")
    
    for event in events:
        if not event.get('links'):
            continue
        
        title = event['title']
        sport = event.get('sport', 'Sport')
        time = event.get('time', '')
        
        for url in event['links'][:5]:
            channel_name = url.split('/')[-1] if url.split('/')[-1] else 'Stream'
            channel_name = re.sub(r'\.(m3u8|m3u|php|html|xml)$', '', channel_name)
            if len(channel_name) > 20:
                channel_name = channel_name[:20]
            
            lines.append(f'#EXTINF:-1 group-title="{sport}",{time} - {title}')
            lines.append(url)
            lines.append("")
    
    return '\n'.join(lines)

def main():
    events = scrape_sportora()
    
    if not events:
        print("❌ Nessun evento trovato per oggi!")
        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write("<h1>Nessun evento trovato per oggi</h1>")
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
