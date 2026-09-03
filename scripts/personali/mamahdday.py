#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER MAMAHD - Solo eventi del giorno corrente
"""

import requests
import json
from datetime import datetime, timedelta
import os
import re
from collections import defaultdict
from html import escape

# ============================================================
#  CONFIGURAZIONE
# ============================================================

API_URL = "https://mamahd.co/api.php"
OUTPUT_HTML = "Kira_Mam.html"
OUTPUT_M3U = "Mama_playlist.m3u"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': 'https://mamahd.co/',
    'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
    'X-Requested-With': 'XMLHttpRequest'
}

# ============================================================
#  FUNZIONI
# ============================================================

def fetch_matches():
    """Recupera i match da api.php."""
    try:
        print(f"📡 Chiamata API: {API_URL}")
        response = requests.get(API_URL, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Errore HTTP: {response.status_code}")
            return []
        
        data = response.json()
        matches = data.get('matches', [])
        print(f"   ✅ Trovati {len(matches)} match totali")
        return matches
        
    except Exception as e:
        print(f"❌ Errore durante il fetch: {e}")
        return []

def parse_matches(matches):
    """Estrae gli eventi e li raggruppa per giorno (SOLO OGGI)."""
    events_by_day = defaultdict(list)
    today = datetime.now().date()
    today_str = today.strftime('%Y-%m-%d')
    today_datetime = datetime.now()  # Aggiungiamo questo per avere un datetime completo
    
    print(f"📅 Filtro: Solo eventi di oggi ({today.strftime('%d/%m/%Y')})")
    
    for match in matches:
        if not isinstance(match, dict):
            continue
        
        match_text = match.get('matchText', '')
        time_str = match.get('time', '')
        league = match.get('league', 'Sconosciuta')
        team1 = match.get('team1', '')
        team2 = match.get('team2', '')
        match_date = match.get('matchDate', '')
        
        # ---- FILTRO: Solo eventi di OGGI ----
        try:
            if match_date:
                date_parts = match_date.split('-')
                if len(date_parts) == 3:
                    event_date = datetime(
                        int(date_parts[0]),
                        int(date_parts[1]),
                        int(date_parts[2])
                    ).date()
                else:
                    event_date = today
            else:
                event_date = today
        except:
            event_date = today
        
        # Salta gli eventi che non sono di oggi
        if event_date != today:
            continue
        
        # Crea titolo
        if team1 and team2:
            title = f"{team1} VS {team2}"
        else:
            title = match_text
            if len(title) > 50:
                parts = title.split(']')
                if len(parts) > 1:
                    title = parts[-1].strip()
        
        # Estrai link
        all_links = []
        channels = match.get('channels', [])
        
        if isinstance(channels, list):
            for channel in channels:
                if not isinstance(channel, dict):
                    continue
                
                links = channel.get('links', [])
                if isinstance(links, list):
                    for link in links:
                        if isinstance(link, str) and link.startswith('http'):
                            all_links.append(link)
                
                old_links = channel.get('oldLinks', [])
                if isinstance(old_links, list):
                    for link in old_links:
                        if isinstance(link, str) and link.startswith('http') and link not in all_links:
                            all_links.append(link)
        
        if not all_links:
            for key in ['link', 'url', 'stream']:
                if key in match and match[key]:
                    link = match[key]
                    if isinstance(link, str) and link.startswith('http'):
                        all_links.append(link)
        
        all_links = list(dict.fromkeys(all_links))
        
        if all_links:
            # CORREZIONE: Usa today_datetime (datetime) invece di today (date)
            try:
                if time_str and ':' in time_str:
                    # Prova a estrarre HH:MM da vari formati
                    time_parts = time_str.split(':')
                    if len(time_parts) >= 2:
                        hour = int(time_parts[0])
                        minute = int(time_parts[1][:2])  # Prendi solo i primi 2 caratteri per i minuti
                        # Assicurati che ora e minuti siano validi
                        hour = max(0, min(23, hour))
                        minute = max(0, min(59, minute))
                        event_time = today_datetime.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    else:
                        # Se il formato è strano, usa mezzogiorno come default
                        event_time = today_datetime.replace(hour=12, minute=0, second=0, microsecond=0)
                else:
                    # Se non c'è orario, usa mezzogiorno come default
                    event_time = today_datetime.replace(hour=12, minute=0, second=0, microsecond=0)
            except (ValueError, IndexError, TypeError):
                # In caso di errore, usa mezzogiorno come default
                event_time = today_datetime.replace(hour=12, minute=0, second=0, microsecond=0)
            
            day_key = event_time.strftime('%Y-%m-%d')
            day_label = event_time.strftime('%A, %d %B %Y')
            
            events_by_day[day_key].append({
                'title': title,
                'orario': event_time.strftime('%H:%M'),
                'datetime': event_time,
                'competizione': league,
                'links': all_links,
                'fonte': 'MamaHD',
                'giorno': day_label,
                'data_ordine': event_time.strftime('%Y-%m-%d %H:%M')
            })
    
    # Rimuovi eventuali giorni non oggi (sicurezza)
    filtered = {k: v for k, v in events_by_day.items() if k == today_str}
    
    total_events = sum(len(e) for e in filtered.values())
    print(f"   📦 Eventi di oggi: {total_events}")
    
    return filtered

def generate_html(events_by_day):
    """Genera HTML con lo stile di PyGenHtmlM3U.py."""
    today = datetime.now().strftime('%d/%m/%Y')
    
    if not events_by_day:
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Kira MamaHD</title></head>
<body><h1>Nessun evento trovato per oggi</h1></body>
</html>"""
    
    event_items = []
    sorted_days = sorted(events_by_day.keys())
    total_events = sum(len(e) for e in events_by_day.values())
    
    for day_key in sorted_days:
        events = events_by_day[day_key]
        day_label = events[0]['giorno'] if events else day_key
        is_today = day_key == datetime.now().strftime('%Y-%m-%d')
        
        events.sort(key=lambda x: x['datetime'])
        
        today_badge = '<span style="background: #ff00cc; padding: 2px 10px; border-radius: 12px; font-size: 0.7rem; margin-left: 10px;">OGGI</span>' if is_today else ''
        
        day_events_html = ""
        for event in events:
            links = event.get('links', ['#'])
            valid_links = [l for l in links if l != '#']
            
            status_badge = '<span class="status-next">⏳ PROSSIMO</span>'
            
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
                channel_name = link.split('/')[-1][:30] or '▶ GUARDA IN DIRETTA'
                links_html = f'<a href="{link}" target="_blank" class="server-link">{channel_name}</a>'
            else:
                links_html = '<span class="no-link">🔗 Link non disponibile</span>'
            
            fonte_badge = f'<span class="fonte-badge">📡 {event.get("fonte", "MamaHD")}</span>'
            
            day_events_html += f'''
            <div class="event-card">
                <div class="event-info">
                    <h3>{escape(event['title'])} {status_badge}</h3>
                    <p class="competition">🏆 {escape(event['competizione'])}</p>
                    <p class="datetime">🕒 {escape(event['orario'])} • 📅 {escape(event['giorno'])}</p>
                    {fonte_badge}
                </div>
                <div class="event-links">
                    {links_html}
                </div>
            </div>
            '''
        
        event_items.append(f'''
        <div class="day-section">
            <div class="day-header" onclick="toggleDay(this)">
                📅 {escape(day_label)} {today_badge} <span class="day-arrow">▼</span>
                <span class="day-count">({len(events)} eventi)</span>
            </div>
            <div class="day-content">
                <div class="events-grid">
                    {day_events_html}
                </div>
            </div>
        </div>
        ''')
    
    html_content = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        
        .day-section {{
            background: rgba(0, 30, 30, 0.5);
            border: 1px solid rgba(0, 255, 204, 0.15);
            border-radius: 15px;
            margin-bottom: 20px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        .day-section:hover {{
            border-color: rgba(0, 255, 204, 0.4);
        }}
        .day-header {{
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            font-size: 1.2rem;
            padding: 15px 20px;
            background: rgba(0, 255, 204, 0.05);
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #00ffcc;
            transition: all 0.3s ease;
            user-select: none;
        }}
        .day-header:hover {{
            background: rgba(0, 255, 204, 0.1);
        }}
        .day-header.active {{
            background: rgba(0, 255, 204, 0.15);
            border-bottom: 1px solid rgba(0, 255, 204, 0.2);
        }}
        .day-arrow {{
            transition: transform 0.3s ease;
            font-size: 0.8rem;
        }}
        .day-header.active .day-arrow {{
            transform: rotate(180deg);
        }}
        .day-count {{
            font-size: 0.8rem;
            color: #88ddff;
            opacity: 0.7;
            font-weight: 400;
        }}
        .day-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.5s ease-out;
            padding: 0 20px;
        }}
        .day-content.open {{
            max-height: 20000px;
            padding: 20px;
        }}
        
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
            .day-header {{ font-size: 1rem; }}
        }}
    </style>
</head>
<body>
    <div class="matrix-bg"></div>
    <div class="container">
        <header class="header">
            <h1>KIRA GATE ACCESS</h1>
            <p class="subtitle">• Eventi Sportivi di Oggi •</p>
        </header>
        
        <div style="text-align: center;">
            <div class="event-counter">
                🎯 <span>{total_events}</span> eventi disponibili per oggi
            </div>
        </div>
        
        <div id="days-container">
            {''.join(event_items)}
        </div>
        
        <footer class="footer">
            <p class="neon-text">KIRA GSI SPORT • Eventi di oggi • {datetime.now().year} • Developed by KIRA GSI GROUP</p>
        </footer>
    </div>
    
    <script>
        function toggleDay(header) {{
            header.classList.toggle('active');
            const content = header.nextElementSibling;
            content.classList.toggle('open');
        }}
        
        // Apri automaticamente il giorno di oggi
        document.addEventListener('DOMContentLoaded', function() {{
            const headers = document.querySelectorAll('.day-header');
            for (let header of headers) {{
                if (header.textContent.includes('OGGI')) {{
                    toggleDay(header);
                    break;
                }}
            }}
        }});
    </script>
</body>
</html>'''
    
    return html_content

def generate_m3u(events_by_day):
    """Genera la playlist M3U per WisePlay."""
    if not events_by_day:
        return "#EXTM3U\n"
    
    lines = ["#EXTM3U"]
    lines.append('#EXTINF:-1 tvg-logo="",KIRA MAMAHD - Playlist')
    lines.append("")
    
    sorted_days = sorted(events_by_day.keys())
    
    for day_key in sorted_days:
        events = events_by_day[day_key]
        events.sort(key=lambda x: x['datetime'])
        
        day_label = events[0]['giorno'] if events else day_key
        lines.append(f"# Playlist: {day_label}")
        lines.append("")
        
        for event in events:
            if not event['links']:
                continue
            
            event_title = f"{event['orario']} - {event['title']}"
            category = event.get('competizione', 'MamaHD')
            
            for url in event['links'][:5]:
                channel_name = url.split('/')[-1] if url.split('/')[-1] else 'Stream'
                channel_name = re.sub(r'\.(m3u8|m3u|php|html|xml)$', '', channel_name)
                if 'id=' in channel_name:
                    channel_name = f"Canal {channel_name.split('id=')[-1]}"
                channel_name = channel_name[:20] or 'Canale'
                
                lines.append(f'#EXTINF:-1 group-title="{day_label} - {category}",{event_title} - {channel_name}')
                lines.append(url)
                lines.append("")
    
    return '\n'.join(lines)

def main():
    print("="*50)
    print("📡 MAMAHD SCRAPER - Solo eventi di OGGI")
    print("="*50)
    
    matches = fetch_matches()
    if not matches:
        print("⚠️ Nessun match trovato")
        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write("<h1>Nessun evento trovato</h1>")
        with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
        return
    
    events_by_day = parse_matches(matches)
    total_events = sum(len(e) for e in events_by_day.values())
    total_days = len(events_by_day)
    
    if total_events == 0:
        print("⚠️ Nessun evento trovato per oggi")
        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write("<h1>Nessun evento per oggi</h1>")
        with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
        return
    
    print(f"   📦 Eventi di oggi: {total_events}")
    
    for day_key in sorted(events_by_day.keys()):
        day_label = events_by_day[day_key][0]['giorno']
        print(f"      📅 {day_label}: {len(events_by_day[day_key])} eventi")
    
    print("\n📄 Generazione HTML...")
    html_content = generate_html(events_by_day)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"   ✅ HTML generato: {OUTPUT_HTML}")
    
    print("\n📄 Generazione M3U...")
    m3u_content = generate_m3u(events_by_day)
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"   ✅ M3U generato: {OUTPUT_M3U}")
    
    print("\n✅ OPERAZIONE COMPLETATA!")

if __name__ == "__main__":
    main()