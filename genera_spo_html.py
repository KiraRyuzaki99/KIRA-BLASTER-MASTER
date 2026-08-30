#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERATORE SPO HTML - Trasforma lista_sportsonlineci.xml in Kira_Spo.html
"""

import xml.etree.ElementTree as ET
from datetime import datetime
import os

# ============================================================
#  CONFIGURAZIONE
# ============================================================

INPUT_XML = "lista_sportsonlineci.xml"
OUTPUT_HTML = "Kira_Spo.html"

# ============================================================
#  FUNZIONI
# ============================================================

def parse_xml(xml_file):
    """Legge il file XML e restituisce la lista degli eventi."""
    events = []
    
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    for track in root.findall('track'):
        title = track.find('title')
        if title is None:
            continue
        
        full_title = title.text or ""
        
        # Estrai ora e nome evento
        time = full_title[:5] if len(full_title) >= 5 and full_title[:2].isdigit() else "00:00"
        event_name = full_title[6:].strip() if len(full_title) > 6 else full_title
        
        # Raccolta URL
        urls = []
        for url_elem in track.findall('url'):
            if url_elem.text:
                urls.append(url_elem.text)
        
        events.append({
            'time': time,
            'name': event_name,
            'urls': urls
        })
    
    return events

def generate_html(events):
    """Genera la pagina HTML finale con gli eventi."""
    today = datetime.now().strftime('%d/%m/%Y')
    
    # Costruisci il contenuto degli eventi
    events_html = ""
    for event in events:
        if not event['urls']:
            continue
        
        # Crea il nome dell'evento (incluso orario)
        event_display = f"{event['time']} - {event['name']}"
        
        # Crea i link per ogni canale
        channels_html = ""
        for url in event['urls']:
            # Estrai un nome descrittivo dal link
            link_parts = url.split('/')
            channel_name = link_parts[-2] if len(link_parts) >= 2 else 'Canale'
            channel_name = channel_name.replace('.php', '').upper()
            
            channels_html += f'<li><a href="{url}" class="channel-link" target="_blank">{channel_name}</a></li>'
        
        events_html += f'''
        <div class="event-group">
            <div class="event-header" onclick="toggleEvent(this)">
                {event_display} <span class="arrow">▶</span>
            </div>
            <ul class="stream-links">
                {channels_html}
            </ul>
        </div>
        '''
    
    # Template HTML completo
    html_content = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>KIRA GSI</title>
    <style>
        body {{ background-color: #000; color: #00ff41; font-family: 'Consolas', monospace; margin: 0; padding: 20px; text-shadow: 0 0 5px rgba(0, 255, 65, 0.8); }}
        .container {{ max-width: 800px; margin: 0 auto; border: 2px solid #00ff41; box-shadow: 0 0 20px #00ff41; padding: 10px; background-color: rgba(0, 0, 0, 0.85); }}
        h1 {{ color: #ff00ff; text-align: center; text-shadow: 0 0 10px #ff00ff; border-bottom: 2px dashed #00ff41; padding-bottom: 10px; margin-bottom: 20px; }}
        .event-group {{ margin-bottom: 5px; border-left: 3px solid #00ff41; padding-left: 10px; }}
        .event-header {{ background-color: rgba(0, 255, 65, 0.1); color: #00ff41; padding: 10px; cursor: pointer; font-weight: bold; display: flex; justify-content: space-between; border: 1px solid #00ff41; margin-top: 5px; }}
        .event-header.active {{ background-color: #00ff41; color: #000; }}
        .arrow {{ transition: transform 0.3s; }}
        .event-header.active .arrow {{ transform: rotate(90deg); }}
        .stream-links {{ padding: 0; margin: 0; list-style: none; background-color: rgba(0, 0, 0, 0.95); border: 1px solid #00ff41; border-top: none; max-height: 0; overflow: hidden; transition: max-height 0.4s ease-out; }}
        .stream-links.open {{ max-height: 500px; }}
        .channel-link {{ display: block; padding: 8px 15px; color: #ffcc00; text-decoration: none; font-weight: bold; }}
        .channel-link:hover {{ color: #fff; background-color: rgba(0, 255, 255, 0.1); }}
    </style>
</head>
<body>
<div class="container">
    <h1>KIRA ACCESS GATE</h1>
    <h1>{today} ORARIO GMT +1</h1>
    <div id="events-list">
        {events_html}
    </div>
</div>
<script>
    function toggleEvent(header) {{
        header.classList.toggle('active');
        const links = header.nextElementSibling;
        links.classList.toggle('open');
        links.style.maxHeight = links.classList.contains('open') ? links.scrollHeight + "px" : "0";
    }}
</script>
</body>
</html>'''
    
    return html_content

def main():
    """Funzione principale."""
    print("📄 Generazione HTML da XML...")
    
    if not os.path.exists(INPUT_XML):
        print(f"❌ File {INPUT_XML} non trovato!")
        return
    
    events = parse_xml(INPUT_XML)
    print(f"   Trovati {len(events)} eventi")
    
    html_content = generate_html(events)
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ HTML generato: {OUTPUT_HTML}")

if __name__ == "__main__":
    main()