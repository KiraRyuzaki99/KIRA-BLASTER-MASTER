#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERATORE LIVETV - Adattato per XML con struttura <evento>
"""

import xml.etree.ElementTree as ET
from datetime import datetime
import os
import re

INPUT_XML = "eventos_livetv_sx.xml"
OUTPUT_HTML = "Kira_LiveTV.html"
OUTPUT_M3U = "LiveTV_playlist.m3u"

def parse_livetv_xml(xml_file):
    """Legge il file XML di LiveTV con struttura <evento>."""
    events = []
    
    if not os.path.exists(xml_file):
        print(f"❌ File {xml_file} non trovato!")
        return events
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ Errore nel parsing XML: {e}")
        return events
    
    # Cerca tutti gli elementi <evento>
    for evento in root.findall('evento'):
        nombre = evento.find('nombre')
        deporte = evento.find('deporte')
        competicion = evento.find('competicion')
        fecha = evento.find('fecha')
        hora = evento.find('hora')
        url = evento.find('url')
        
        if nombre is None or not nombre.text:
            continue
        
        # Costruisci il titolo
        title = nombre.text.strip()
        
        # Data e ora
        date_str = fecha.text if fecha is not None else ""
        time_str = hora.text if hora is not None else ""
        
        # Competizione
        competition = competicion.text if competicion is not None else "LiveTV"
        sport = deporte.text if deporte is not None else "Sport"
        
        # URL (link alla pagina evento)
        link = url.text if url is not None and url.text else ""
        
        if link:
            events.append({
                'title': title,
                'date': date_str,
                'time': time_str,
                'competition': competition,
                'sport': sport,
                'url': link,
                'category': 'LiveTV'
            })
    
    print(f"   Trovati {len(events)} eventi")
    return events

def generate_html(events):
    """Genera la pagina HTML finale."""
    today = datetime.now().strftime('%d/%m/%Y')
    
    if not events:
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>KIRA LIVETV</title></head>
<body><h1>Nessun evento trovato</h1></body>
</html>"""
    
    # Raggruppa per data
    events_by_date = {}
    for event in events:
        date_key = event.get('date', 'Oggi')
        if date_key not in events_by_date:
            events_by_date[date_key] = []
        events_by_date[date_key].append(event)
    
    events_html = ""
    for date_key, day_events in events_by_date.items():
        # Ordina per ora
        day_events.sort(key=lambda x: x.get('time', '00:00'))
        
        is_today = date_key.lower() in ['oggi', datetime.now().strftime('%d de %B').lower()]
        today_badge = ' <span style="color: #ff00ff; font-size: 0.7rem;">(OGGI)</span>' if is_today else ''
        
        day_events_html = ""
        for event in day_events:
            event_display = f"{event.get('time', 'N/A')} - {event['title']} ({event.get('competition', '')})"
            
            # Link alla pagina evento
            url = event.get('url', '#')
            if url and url != '#':
                link_html = f'<a href="{url}" class="server-link" target="_blank">▶ Guarda su LiveTV</a>'
            else:
                link_html = '<span class="no-link">🔗 Link non disponibile</span>'
            
            day_events_html += f'''
            <div class="event-card">
                <div class="event-info">
                    <h3>{event['title']}</h3>
                    <p class="competition">🏆 {event.get('competition', '')} - {event.get('sport', '')}</p>
                    <p class="datetime">🕒 {event.get('time', 'N/A')}</p>
                </div>
                <div class="event-links">
                    {link_html}
                </div>
            </div>
            '''
        
        events_html += f'''
        <div class="day-section">
            <div class="day-header" onclick="toggleDay(this)">
                📅 {date_key}{today_badge} <span class="day-arrow">▼</span>
                <span class="day-count">({len(day_events)} eventi)</span>
            </div>
            <div class="day-content">
                <div class="events-grid">
                    {day_events_html}
                </div>
            </div>
        </div>
        '''
    
    return f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KIRA LIVETV</title>
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
        .header .subtitle {{ font-family: 'Audiowide', cursive; color: #88ffdd; font-size: 1.2rem; margin-top: 10px; }}
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
        }}
        .day-header:hover {{ background: rgba(0, 255, 204, 0.1); }}
        .day-header.active {{ background: rgba(0, 255, 204, 0.15); border-bottom: 1px solid rgba(0, 255, 204, 0.2); }}
        .day-arrow {{ transition: transform 0.3s ease; font-size: 0.8rem; }}
        .day-header.active .day-arrow {{ transform: rotate(180deg); }}
        .day-count {{ font-size: 0.8rem; color: #88ddff; opacity: 0.7; font-weight: 400; }}
        .day-content {{ max-height: 0; overflow: hidden; transition: max-height 0.5s ease-out; padding: 0 20px; }}
        .day-content.open {{ max-height: 20000px; padding: 20px; }}
        
        .events-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }}
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
        .event-info .datetime {{ color: #88ddff; font-size: 0.85rem; opacity: 0.8; }}
        .event-links {{ margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(0, 255, 204, 0.15); }}
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
        .server-link:hover {{ background: #00ddbb; box-shadow: 0 0 40px rgba(0, 255, 204, 0.5); }}
        .no-link {{ display: inline-block; font-family: 'Orbitron', monospace; color: #666; text-align: center; width: 100%; padding: 10px; }}
        
        .footer {{ text-align: center; padding: 40px 0 20px; margin-top: 40px; border-top: 1px solid rgba(0, 255, 204, 0.2); color: #88ddff; opacity: 0.7; }}
        .footer .neon-text {{ font-family: 'Orbitron', monospace; color: #00ffcc; font-size: 1rem; }}
    </style>
</head>
<body>
    <div class="matrix-bg"></div>
    <div class="container">
        <header class="header">
            <h1>⚡ LIVETV EVENTS ⚡</h1>
            <p class="subtitle">• Eventi Sportivi da LiveTV •</p>
        </header>
        <div style="text-align: center;">
            <div class="event-counter">
                🎯 <span>{len(events)}</span> eventi disponibili su <span>{len(events_by_date)}</span> giorni
            </div>
        </div>
        <div id="days-container">
            {events_html}
        </div>
        <footer class="footer">
            <p class="neon-text">🔮 LiveTV • Eventi in diretta • {datetime.now().year} • Powered by KIRA</p>
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

def generate_m3u(events):
    """Genera la playlist M3U per WisePlay."""
    if not events:
        return "#EXTM3U\n"
    
    lines = ["#EXTM3U"]
    lines.append('#EXTINF:-1 tvg-logo="",KIRA LIVETV - Playlist')
    lines.append("")
    
    # Raggruppa per data
    events_by_date = {}
    for event in events:
        date_key = event.get('date', 'Oggi')
        if date_key not in events_by_date:
            events_by_date[date_key] = []
        events_by_date[date_key].append(event)
    
    for date_key, day_events in events_by_date.items():
        day_events.sort(key=lambda x: x.get('time', '00:00'))
        lines.append(f"# Playlist: {date_key}")
        lines.append("")
        
        for event in day_events:
            title = f"{event.get('time', 'N/A')} - {event['title']} ({event.get('competition', '')})"
            url = event.get('url', '#')
            if url and url != '#':
                lines.append(f'#EXTINF:-1 group-title="LiveTV - {date_key}",{title}')
                lines.append(url)
                lines.append("")
    
    return '\n'.join(lines)

def main():
    print("="*50)
    print("📄 GENERATORE LIVETV - Struttura <evento>")
    print("="*50)
    
    events = parse_livetv_xml(INPUT_XML)
    
    if not events:
        print("⚠️ Nessun evento trovato. Creo file vuoti.")
        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write("<h1>Nessun evento trovato</h1>")
        with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
        return
    
    html_content = generate_html(events)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"   ✅ HTML generato: {OUTPUT_HTML}")
    
    m3u_content = generate_m3u(events)
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"   ✅ M3U generato: {OUTPUT_M3U}")
    
    print("\n✅ OPERAZIONE COMPLETATA!")

if __name__ == "__main__":
    main()