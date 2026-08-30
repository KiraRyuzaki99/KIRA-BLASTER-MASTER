#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERATORE ICA HTML - Trasforma il file TXT in HTML finale
"""

import os
from datetime import datetime

INPUT_FILE = "lista_icastresana_intermedia.txt"
OUTPUT_FILE = "Kira_Ica.html"

def generate_html_from_txt():
    """Legge il file TXT e genera HTML."""
    if not os.path.exists(INPUT_FILE):
        print(f"❌ File {INPUT_FILE} non trovato!")
        return
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    
    if not lines:
        print("⚠️ Nessun dato trovato!")
        return
    
    # Raggruppa eventi per nome
    events = {}
    for line in lines:
        if ' | ' in line:
            parts = line.split(' | ', 1)
            event_name = parts[0].strip()
            url = parts[1].strip()
            if event_name not in events:
                events[event_name] = []
            events[event_name].append(url)
    
    today = datetime.now().strftime('%d/%m/%Y')
    
    # Genera HTML
    events_html = ""
    for event_name, urls in events.items():
        channels_html = ""
        for url in urls:
            # Estrai un nome descrittivo
            channel_name = url.split('/')[-1] if url else 'Canale'
            channels_html += f'<li><a href="{url}" class="channel-link" target="_blank">{channel_name}</a></li>'
        
        events_html += f'''
        <div class="event-group">
            <div class="event-header" onclick="toggleEvent(this)">
                {event_name} <span class="arrow">▶</span>
            </div>
            <ul class="stream-links">
                {channels_html}
            </ul>
        </div>
        '''
    
    html_content = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KIRA ICA - Eventi</title>
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
    <h1>KIRA ICA - ACCESS GATE</h1>
    <h1>{today}</h1>
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
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML generato: {OUTPUT_FILE} ({len(events)} eventi)")

if __name__ == "__main__":
    generate_html_from_txt()