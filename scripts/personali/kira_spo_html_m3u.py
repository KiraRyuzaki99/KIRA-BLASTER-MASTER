#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERATORE SPO HTML - Trasforma lista_sportsonlineci.xml in Kira_Spo.html
con stile KIRA unificato e playlist M3U
"""

import xml.etree.ElementTree as ET
from datetime import datetime
import os
import re

# ============================================================
#  CONFIGURAZIONE
# ============================================================

INPUT_XML = "lista_sportsonlineci.xml"
OUTPUT_HTML = "kira_spo.html"
OUTPUT_M3U = "spo_playlist.m3u"

# ============================================================
#  FUNZIONI
# ============================================================

def parse_xml(xml_file):
    """Legge il file XML e restituisce la lista degli eventi."""
    events = []
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ Errore lettura XML: {e}")
        return []
    
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

def generate_event_card(event):
    """Genera una card HTML per un singolo evento."""
    urls = event.get('urls', [])
    time = event.get('time', 'N/A')
    name = event.get('name', 'Evento')
    
    # Badge di stato
    status_badge = '<span class="status-next">⏳ PROSSIMO</span>'
    
    # Genera i link
    if len(urls) > 1:
        options = "\n".join([f'<option value="{url}">Canale {i+1}</option>' for i, url in enumerate(urls)])
        links_html = f'''
        <div class="dropdown">
            <select onchange="window.open(this.value, '_blank'); this.selectedIndex=0;">
                <option value="">📡 Scegli il canale...</option>
                {options}
            </select>
        </div>
        '''
    elif len(urls) == 1:
        links_html = f'<a href="{urls[0]}" target="_blank" class="server-link">▶ GUARDA IN DIRETTA</a>'
    else:
        links_html = '<span class="no-link">🔗 Link non disponibile</span>'
    
    return f'''
    <div class="event-card">
        <div class="event-info">
            <h3>{escape_html(name)} {status_badge}</h3>
            <p class="sport-badge">🏆 Sport</p>
            <p class="datetime">🕒 {escape_html(time)} • 📅 {datetime.now().strftime('%d/%m/%Y')}</p>
            <span class="fonte-badge">📡 SPO</span>
        </div>
        <div class="event-links">
            {links_html}
        </div>
    </div>
    '''

def escape_html(text):
    """Escape caratteri HTML."""
    if not text:
        return ""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

def generate_html(events):
    """Genera la pagina HTML finale con stile KIRA unificato."""
    today = datetime.now().strftime('%d/%m/%Y')
    
    if not events:
        return f'''<!DOCTYPE html>
<html lang="it">
<head><meta charset="UTF-8"><title>KIRA SPO</title></head>
<body><h1>Nessun evento trovato</h1></body>
</html>'''
    
    event_items = ""
    for event in events:
        if event.get('urls'):
            event_items += generate_event_card(event)
    
    # Template HTML con stile KIRA unificato
    html_content = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
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
        
        .events-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 25px; margin-top: 20px; }}
        
        .event-card {{ background: rgba(0, 30, 30, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(0, 255, 204, 0.2); border-radius: 15px; padding: 25px; transition: all 0.3s ease; display: flex; flex-direction: column; }}
        .event-card:hover {{ transform: translateY(-5px); border-color: rgba(0, 255, 204, 0.6); box-shadow: 0 0 40px rgba(0, 255, 204, 0.15); }}
        .event-info h3 {{ font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 1.1rem; color: #00ffcc; margin-bottom: 8px; display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }}
        .event-info .sport-badge {{ font-family: 'Audiowide', cursive; color: #88ddff; font-size: 0.8rem; background: rgba(0, 255, 204, 0.1); padding: 3px 12px; border-radius: 20px; display: inline-block; margin-bottom: 8px; }}
        .event-info .datetime {{ color: #88ddff; font-size: 0.85rem; opacity: 0.8; }}
        .fonte-badge {{ display: inline-block; font-size: 0.7rem; background: rgba(0, 255, 204, 0.15); color: #88ffdd; padding: 2px 12px; border-radius: 12px; margin-top: 5px; border: 1px solid rgba(0, 255, 204, 0.2); }}
        .status-next {{ display: inline-block; font-size: 0.7rem; background: rgba(0, 100, 255, 0.3); color: #4488ff; padding: 2px 10px; border-radius: 12px; }}
        .event-links {{ margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(0, 255, 204, 0.15); }}
        .server-link {{ display: inline-block; font-family: 'Orbitron', monospace; font-weight: 700; color: #0a0a0a; background: #00ffcc; padding: 12px 24px; border-radius: 8px; text-decoration: none; text-align: center; width: 100%; transition: all 0.3s ease; font-size: 0.85rem; }}
        .server-link:hover {{ background: #00ddbb; box-shadow: 0 0 40px rgba(0, 255, 204, 0.5); }}
        .dropdown select {{ width: 100%; padding: 12px 15px; background: rgba(0, 20, 20, 0.9); color: #00ffcc; border: 1px solid rgba(0, 255, 204, 0.4); border-radius: 10px; font-family: 'Orbitron', monospace; font-size: 0.85rem; cursor: pointer; outline: none; }}
        .dropdown select option {{ background: #0a1a1a; color: #88ffdd; }}
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
            <h1>KIRA GATE ACCESS</h1>
            <p class="subtitle">• Eventi di Oggi •</p>
        </header>
        
        <div style="text-align: center;">
            <div class="event-counter">
                🎯 <span>{len([e for e in events if e.get('urls')])}</span> eventi disponibili
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
    
    return html_content

def generate_m3u(events):
    """Genera playlist M3U nello stile degli altri scraper."""
    if not events:
        return "#EXTM3U\n"
    
    lines = ["#EXTM3U"]
    lines.append('#EXTINF:-1 tvg-logo="",KIRA SPO - Playlist')
    lines.append("")
    
    for event in events:
        if not event.get('urls'):
            continue
        
        title = event['name']
        time = event.get('time', '')
        date = datetime.now().strftime('%d/%m/%Y')
        
        for url in event['urls'][:5]:
            # Estrai un nome dal link
            channel_name = url.split('/')[-1] if url.split('/')[-1] else 'Stream'
            channel_name = re.sub(r'\.(m3u8|m3u|php|html|xml)$', '', channel_name)
            if len(channel_name) > 20:
                channel_name = channel_name[:20]
            
            lines.append(f'#EXTINF:-1 group-title="SPO",{date} {time} - {title} - {channel_name}')
            lines.append(url)
            lines.append("")
    
    return '\n'.join(lines)

def main():
    """Funzione principale."""
    print("="*70)
    print("📡 GENERATORE SPO HTML")
    print("="*70)
    
    if not os.path.exists(INPUT_XML):
        print(f"❌ File {INPUT_XML} non trovato!")
        return
    
    print(f"\n📄 Lettura: {INPUT_XML}")
    events = parse_xml(INPUT_XML)
    
    if not events:
        print("❌ Nessun evento trovato nel file XML!")
        return
    
    total_urls = sum(len(e['urls']) for e in events)
    print(f"   📦 {len(events)} eventi, {total_urls} link totali")
    
    # Genera HTML
    print("\n📄 Generazione HTML...")
    html_content = generate_html(events)
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ HTML generato: {OUTPUT_HTML}")
    
    # Genera M3U
    print("\n📄 Generazione M3U...")
    m3u_content = generate_m3u(events)
    
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    
    print(f"✅ M3U generato: {OUTPUT_M3U}")
    print("\n✅ OPERAZIONE COMPLETATA!")

if __name__ == "__main__":
    main()