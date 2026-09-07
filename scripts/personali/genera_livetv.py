#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERATORE LIVETV - Solo eventi del giorno corrente
"""

import xml.etree.ElementTree as ET
from datetime import datetime
import os
import re

INPUT_XML = "output/eventos_livetv_sx.xml"
OUTPUT_HTML = "kira_liv.html"
OUTPUT_M3U = "LiveTV_playlist.m3u"

def parse_livetv_xml(xml_file):
    """Legge il file XML di LiveTV con struttura <evento> e filtra solo oggi."""
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
    
    today = datetime.now().date()
    today_str = today.strftime('%Y-%m-%d')
    
    # Formati data possibili
    date_formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%d de %B de %Y',
        '%d de %B',
        '%B %d, %Y'
    ]
    
    print(f"📅 Filtro: Solo eventi di oggi ({today.strftime('%d/%m/%Y')})")
    
    events_found = 0
    events_skipped = 0
    
    for evento in root.findall('evento'):
        nombre = evento.find('nombre')
        deporte = evento.find('deporte')
        competicion = evento.find('competicion')
        fecha = evento.find('fecha')
        hora = evento.find('hora')
        url = evento.find('url')
        
        if nombre is None or not nombre.text:
            continue
        
        # Estrai data
        date_str = fecha.text if fecha is not None else ""
        event_date = None
        
        if date_str:
            # Pulisci la data
            date_str = date_str.strip()
            # Rimuovi "de" e "del" per il parsing
            clean_date = date_str.replace(' de ', ' ').replace(' del ', ' ')
            
            for fmt in date_formats:
                try:
                    event_date = datetime.strptime(clean_date, fmt).date()
                    break
                except:
                    continue
        
        # Se non c'è data, usa oggi come default
        if event_date is None:
            event_date = today
        
        # FILTRO: Solo eventi di oggi
        if event_date != today:
            events_skipped += 1
            continue
        
        events_found += 1
        
        # Costruisci il titolo
        title = nombre.text.strip()
        
        # Ora
        time_str = hora.text if hora is not None else "N/A"
        
        # Competizione
        competition = competicion.text if competicion is not None else "LiveTV"
        sport = deporte.text if deporte is not None else "Sport"
        
        # URL (link alla pagina evento)
        link = url.text if url is not None and url.text else ""
        
        if link:
            events.append({
                'title': title,
                'date': date_str or today.strftime('%d/%m/%Y'),
                'time': time_str,
                'competition': competition,
                'sport': sport,
                'url': link,
                'category': 'LiveTV'
            })
    
    print(f"   📦 Eventi oggi: {events_found}")
    print(f"   ⏭️ Eventi scartati (altre date): {events_skipped}")
    return events

def generate_html(events):
    """Genera la pagina HTML finale."""
    today = datetime.now().strftime('%d/%m/%Y')
    
    if not events:
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>KIRA LIVETV</title></head>
<body><h1>Nessun evento trovato per oggi</h1></body>
</html>"""
    
    # Ordina per ora
    events.sort(key=lambda x: x.get('time', '00:00'))
    
    events_html = ""
    for event in events:
        event_display = f"{event.get('time', 'N/A')} - {event['title']} ({event.get('competition', '')})"
        
        # Link alla pagina evento
        url = event.get('url', '#')
        if url and url != '#':
            link_html = f'<a href="{url}" class="server-link" target="_blank">▶ GUARDA IN DIRETTA</a>'
        else:
            link_html = '<span class="no-link">🔗 Link non disponibile</span>'
        
        events_html += f'''
        <div class="event-card">
            <div class="event-info">
                <h3>{event['title']}</h3>
                <p class="competition">🏆 {event.get('competition', '')} - {event.get('sport', '')}</p>
                <p class="datetime">🕒 {event.get('time', 'N/A')} • 📅 {today}</p>
            </div>
            <div class="event-links">
                {link_html}
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
        
        .footer {{ text-align: center; padding: 40px 0 20px; margin-top: 60px; border-top: 1px solid rgba(0, 255, 204, 0.2); color: #88ddff; opacity: 0.7; }}
        .footer .neon-text {{ font-family: 'Orbitron', monospace; color: #00ffcc; font-size: 1rem; }}
        
        @media (max-width: 768px) {{ .header h1 {{ font-size: 2rem; }} .events-grid {{ grid-template-columns: 1fr; }} .container {{ padding: 15px; }} }}
    </style>
</head>
<body>
    <div class="matrix-bg"></div>
    <div class="container">
        <header class="header">
            <h1>⚡ LIVETV ⚡</h1>
            <p class="subtitle">• Eventi di Oggi •</p>
        </header>
        
        <div style="text-align: center;">
            <div class="event-counter">
                🎯 <span>{len(events)}</span> eventi disponibili per oggi
            </div>
        </div>
        
        <div class="events-grid">
            {events_html}
        </div>
        
        <footer class="footer">
            <p class="neon-text">🔮 LiveTV • Eventi in diretta • {datetime.now().year} • Powered by KIRA</p>
        </footer>
    </div>
</body>
</html>'''

def generate_m3u(events):
    """Genera la playlist M3U per WisePlay."""
    if not events:
        return "#EXTM3U\n"
    
    lines = ["#EXTM3U"]
    lines.append('#EXTINF:-1 tvg-logo="",KIRA LIVETV - Playlist')
    lines.append("")
    
    # Ordina per ora
    events.sort(key=lambda x: x.get('time', '00:00'))
    
    today = datetime.now().strftime('%d/%m/%Y')
    
    for event in events:
        title = f"{event.get('time', 'N/A')} - {event['title']} ({event.get('competition', '')})"
        url = event.get('url', '#')
        if url and url != '#':
            lines.append(f'#EXTINF:-1 group-title="LiveTV - Oggi",{title}')
            lines.append(url)
            lines.append("")
    
    return '\n'.join(lines)

def main():
    print("="*50)
    print("📄 GENERATORE LIVETV - Solo eventi di oggi")
    print("="*50)
    
    events = parse_livetv_xml(INPUT_XML)
    
    if not events:
        print("⚠️ Nessun evento trovato per oggi. Creo file vuoti.")
        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write("<h1>Nessun evento trovato per oggi</h1>")
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
    
    print(f"\n📊 Totale eventi oggi: {len(events)}")
    print("\n✅ OPERAZIONE COMPLETATA!")

if __name__ == "__main__":
    main()