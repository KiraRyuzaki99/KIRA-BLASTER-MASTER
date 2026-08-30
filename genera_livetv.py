#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERATORE LIVETV - Genera HTML e M3U da eventos_livetv_sx.xml
"""

import xml.etree.ElementTree as ET
from datetime import datetime
import os
import re

INPUT_XML = "eventos_livetv_sx.xml"
OUTPUT_HTML = "Kira_LiveTV.html"
OUTPUT_M3U = "LiveTV_playlist.m3u"

def parse_livetv_xml(xml_file):
    """Legge il file XML di LiveTV e restituisce gli eventi."""
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
    
    # Prova diversi pattern XML
    # Pattern 1: <event> con <title> e <url>
    for event in root.findall('.//event'):
        title_elem = event.find('title')
        if title_elem is None or not title_elem.text:
            continue
        
        # Estrai data/ora
        date_elem = event.find('date')
        time_elem = event.find('time')
        date_str = date_elem.text if date_elem is not None else ""
        time_str = time_elem.text if time_elem is not None else ""
        
        # Cerca URL
        urls = []
        for url_elem in event.findall('url'):
            if url_elem.text and url_elem.text.startswith('http'):
                urls.append(url_elem.text)
        
        # Se non trova URL, cerca in 'link'
        if not urls:
            for link in event.findall('link'):
                if link.text and link.text.startswith('http'):
                    urls.append(link.text)
        
        if urls:
            events.append({
                'title': title_elem.text,
                'date': date_str,
                'time': time_str,
                'urls': urls,
                'category': 'LiveTV'
            })
    
    # Pattern 2: <item> con <title> e <link>
    if not events:
        for item in root.findall('.//item'):
            title_elem = item.find('title')
            if title_elem is None or not title_elem.text:
                continue
            
            urls = []
            for link in item.findall('link'):
                if link.text and link.text.startswith('http'):
                    urls.append(link.text)
            
            # Cerca anche in <url>
            for url_elem in item.findall('url'):
                if url_elem.text and url_elem.text.startswith('http'):
                    urls.append(url_elem.text)
            
            if urls:
                # Cerca data/ora nei tag <pubDate> o <date>
                date_elem = item.find('pubDate')
                if date_elem is None:
                    date_elem = item.find('date')
                date_str = date_elem.text if date_elem is not None else ""
                
                events.append({
                    'title': title_elem.text,
                    'date': date_str,
                    'time': "",
                    'urls': urls,
                    'category': 'LiveTV'
                })
    
    # Pattern 3: <channel> con <title> e <url>
    if not events:
        for channel in root.findall('.//channel'):
            title_elem = channel.find('title')
            if title_elem is None or not title_elem.text:
                continue
            
            urls = []
            for url_elem in channel.findall('url'):
                if url_elem.text and url_elem.text.startswith('http'):
                    urls.append(url_elem.text)
            
            if urls:
                events.append({
                    'title': title_elem.text,
                    'date': "",
                    'time': "",
                    'urls': urls,
                    'category': 'LiveTV'
                })
    
    return events

def generate_html(events):
    """Genera la pagina HTML finale con gli eventi."""
    today = datetime.now().strftime('%d/%m/%Y')
    
    if not events:
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>KIRA LiveTV</title></head>
<body><h1>Nessun evento trovato per oggi</h1></body>
</html>"""
    
    events_html = ""
    for event in events:
        if not event['urls']:
            continue
        
        # Costruisci il titolo con data e ora
        title_parts = []
        if event['date']:
            title_parts.append(event['date'][:10] if len(event['date']) > 10 else event['date'])
        if event['time']:
            title_parts.append(event['time'][:5] if len(event['time']) > 5 else event['time'])
        title_parts.append(event['title'])
        event_display = " - ".join(title_parts)
        
        channels_html = ""
        for url in event['urls']:
            # Estrai un nome descrittivo dal link
            channel_name = url.split('/')[-1] if url.split('/')[-1] else 'Canale'
            channel_name = re.sub(r'\.(m3u8|m3u|php|html|xml)$', '', channel_name)
            channel_name = channel_name[:25]  # Limita lunghezza
            
            channels_html += f'<li><a href="{url}" class="channel-link" target="_blank">▶ {channel_name}</a></li>'
        
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
    
    return f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>KIRA LIVETV</title>
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
        .stream-links.open {{ max-height: 800px; }}
        .channel-link {{ display: block; padding: 8px 15px; color: #ffcc00; text-decoration: none; font-weight: bold; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .channel-link:hover {{ color: #fff; background-color: rgba(0, 255, 255, 0.1); }}
    </style>
</head>
<body>
<div class="container">
    <h1>KIRA LIVETV - ACCESS GATE</h1>
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

def generate_m3u(events):
    """Genera la playlist M3U per WisePlay."""
    if not events:
        return "#EXTM3U\n"
    
    lines = ["#EXTM3U"]
    lines.append('#EXTINF:-1 tvg-logo="",KIRA LIVETV - Playlist')
    lines.append("")
    
    for event in events:
        if not event['urls']:
            continue
        
        # Titolo dell'evento
        title_parts = []
        if event['time']:
            title_parts.append(event['time'][:5] if len(event['time']) > 5 else event['time'])
        title_parts.append(event['title'])
        event_title = " - ".join(title_parts)
        
        # Categoria
        category = event.get('category', 'LiveTV')
        
        for url in event['urls']:
            # Estrai nome canale dall'URL
            channel_name = url.split('/')[-1] if url.split('/')[-1] else 'Stream'
            channel_name = re.sub(r'\.(m3u8|m3u|php|html|xml)$', '', channel_name)
            channel_name = channel_name[:20]
            
            # Riga EXTINF con group-title per WisePlay
            lines.append(f'#EXTINF:-1 group-title="{category}",{event_title} - {channel_name}')
            lines.append(url)
            lines.append("")
    
    return '\n'.join(lines)

def main():
    print("="*50)
    print("📄 GENERATORE LIVETV - HTML + M3U")
    print("="*50)
    
    # Parsing XML
    events = parse_livetv_xml(INPUT_XML)
    print(f"   Trovati {len(events)} eventi")
    
    if not events:
        print("⚠️ Nessun evento trovato! Creo file vuoti.")
    
    # Genera HTML
    print("\n📄 Generazione HTML...")
    html_content = generate_html(events)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"   ✅ HTML generato: {OUTPUT_HTML}")
    
    # Genera M3U
    print("\n📄 Generazione M3U...")
    m3u_content = generate_m3u(events)
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"   ✅ M3U generato: {OUTPUT_M3U}")
    
    print("\n✅ OPERAZIONE COMPLETATA!")

if __name__ == "__main__":
    main()