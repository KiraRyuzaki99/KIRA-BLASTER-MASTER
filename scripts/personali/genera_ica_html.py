#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
genera_ica_html.py
Legge output/lista_icastresana_intermedia.txt,
genera output/Kira_Ica.html (stile KIRA GATE)
e output/lista_icastresana_playlist.m3u.
"""

import os
import re
import html as html_lib
from datetime import datetime

INPUT_TXT = os.path.join("output", "lista_icastresana_intermedia.txt")
OUTPUT_HTML = os.path.join("output", "kira_ica.html")
OUTPUT_M3U = os.path.join("output", "lista_icastresana_playlist.m3u")

ACESTREAM_HASH_RE = re.compile(r'[a-fA-F0-9]{40}')


def extract_acestream_hash(url):
    if 'acestream://' in url:
        raw = url.split('acestream://')[1].strip().strip('/')
        raw = raw.split('?')[0].split('&')[0]
        m = ACESTREAM_HASH_RE.search(raw)
        if m:
            return m.group(0)
    if 'id=' in url:
        raw = url.split('id=')[1].split('&')[0]
        m = ACESTREAM_HASH_RE.search(raw)
        if m:
            return m.group(0)
    return None


def build_acestream_variants(acestream_hash):
    if not acestream_hash:
        return []
    return [
        f"acestream://{acestream_hash}",
        f"http://127.0.0.1:6878/ace/getstream?id={acestream_hash}",
    ]


def parse_txt():
    """Legge il TXT e ritorna dict {event_name: [urls]} con varianti acestream espanse."""
    if not os.path.exists(INPUT_TXT):
        print(f"❌ File {INPUT_TXT} non trovato!")
        return {}

    events = {}
    with open(INPUT_TXT, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or ' | ' not in line:
                continue
            event_name, url = line.split(' | ', 1)
            event_name = event_name.strip()
            url = url.strip()

            if event_name not in events:
                events[event_name] = []

            h = extract_acestream_hash(url)
            if h:
                for v in build_acestream_variants(h):
                    if v not in events[event_name]:
                        events[event_name].append(v)
            else:
                if url not in events[event_name]:
                    events[event_name].append(url)

    print(f"📖 Eventi letti da {INPUT_TXT}: {len(events)}")
    return events


def detect_fonte(urls):
    if not urls:
        return '📡 Stream'
    u = urls[0].lower()
    if u.startswith('acestream://') or '127.0.0.1' in u:
        return '📡 Acestream'
    if 'streamx061' in u:
        return '📡 streamx061.sbs'
    if 'streamxhd' in u:
        return '📡 streamxhd.com'
    if 'streamx305' in u:
        return '📡 streamx305.sbs'
    if 'latamplay' in u:
        return '📡 latamplay1.click'
    return '📡 Stream'


def detect_competition(event_name):
    if ' - ' in event_name:
        head = event_name.split(' - ', 1)[0].strip()
        head = re.sub(r'^\d{1,2}:\d{2}\s*', '', head).strip()
        if head and len(head) < 45:
            return head
    if ':' in event_name:
        comp = event_name.split(':', 1)[0].strip()
        if len(comp) < 45:
            return comp
    keywords = [
        'MLS', 'NFL', 'MLB', 'NBA', 'NHL',
        'UEFA Champions League', 'Champions', 'Europa League',
        'Copa Libertadores', 'Copa Sudamericana',
        'Liga MX', 'Liga Colombia', 'Liga BetPlay',
        'La Vuelta', 'Vuelta', 'US Open',
        'Youth League', 'WRC', 'FIBA',
        'Liga Catalana ACB', 'Irish Open',
        'The Solheim Cup', 'Faun Tour', 'Las Carreras',
    ]
    for kw in keywords:
        if kw.lower() in event_name.lower():
            return kw
    return 'Sport'


def short_label(url):
    if url.startswith('acestream://'):
        h = url.replace('acestream://', '')
        return f'acestream://{h[:12]}...'
    if 'id=' in url:
        return 'getstream?id=' + url.split('id=')[1][:16] + '...'
    if 'channel=' in url:
        return 'channel=' + url.split('channel=')[1].split('&')[0]
    if 'stream=' in url:
        return 'stream=' + url.split('stream=')[1].split('&')[0]
    return url if len(url) <= 65 else url[:62] + '...'


def write_m3u(events):
    lines = ['#EXTM3U']
    for event_name, urls in events.items():
        competition = detect_competition(event_name)
        stream_url = urls[0]
        for u in urls:
            if u.startswith('acestream://'):
                stream_url = u
                break
        lines.append(
            f'#EXTINF:-1 tvg-name="{event_name}" '
            f'group-title="{competition}",{event_name}'
        )
        lines.append(stream_url)

    os.makedirs(os.path.dirname(OUTPUT_M3U), exist_ok=True)
    with open(OUTPUT_M3U, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"✅ M3U generato: {OUTPUT_M3U} ({len(events)} canali)")


def write_html(events):
    total_events = len(events)
    now = datetime.now()

    cards_html = []
    for event_name, urls in events.items():
        name_esc = html_lib.escape(event_name)
        competition = html_lib.escape(detect_competition(event_name))
        fonte = detect_fonte(urls)

        status_html = '<span class="status-next">⏳ PROSSIMO</span>'

        if len(urls) > 1:
            options = []
            for src in urls:
                label = short_label(src)
                options.append(
                    f'<option value="{html_lib.escape(src)}">'
                    f'{html_lib.escape(label)}</option>'
                )
            links_html = (
                '<div class="dropdown">\n'
                '                <select onchange="window.open(this.value, \'_blank\'); this.selectedIndex=0;">\n'
                '                    <option value="">📡 Scegli il server...</option>\n'
                + '\n'.join(options) +
                '\n                </select>\n'
                '            </div>'
            )
        else:
            src = urls[0]
            links_html = (
                f'<a href="{html_lib.escape(src)}" target="_blank" class="server-link">'
                f'▶ GUARDA IN DIRETTA</a>'
            )

        card = f'''
        <div class="event-card">
            <div class="event-info">
                <h3>{name_esc} {status_html}</h3>
                <p class="competition">🏆 {competition}</p>
                <p class="datetime">🕒 --:-- • 📅 {now.strftime('%A, %d %B %Y')}</p>
                <span class="fonte-badge">{fonte}</span>
            </div>
            <div class="event-links">
                {links_html}
            </div>
        </div>
        '''
        cards_html.append(card)

    cards_joined = '\n'.join(cards_html)

    html_output = f'''<!DOCTYPE html>
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
            .header {{ text-align: center; padding: 30px 0 40px; border-bottom: 2px solid rgba(0, 255, 204, 0.3); margin-bottom: 40px; }}
            .header h1 {{
                font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 3.5rem;
                text-shadow: 0 0 20px rgba(0, 255, 204, 0.5);
                background: linear-gradient(135deg, #00ffcc, #00ccff);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 4px;
            }}
            .header .subtitle {{ font-family: 'Audiowide', cursive; color: #88ffdd; font-size: 1.2rem; margin-top: 10px; }}
            .event-counter {{
                text-align: center; font-family: 'Orbitron', monospace; font-size: 1.2rem; color: #00ffcc;
                background: rgba(0, 255, 204, 0.08); border: 1px solid rgba(0, 255, 204, 0.2);
                padding: 12px 20px; border-radius: 30px; display: inline-block; margin: 0 auto 30px;
            }}
            .event-counter span {{ font-weight: 900; font-size: 1.5rem; }}
            .events-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 25px; margin-top: 20px; }}
            .event-card {{
                background: rgba(0, 30, 30, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(0, 255, 204, 0.2);
                border-radius: 15px; padding: 25px; transition: all 0.3s ease; display: flex; flex-direction: column;
            }}
            .event-card:hover {{ transform: translateY(-5px); border-color: rgba(0, 255, 204, 0.6); box-shadow: 0 0 40px rgba(0, 255, 204, 0.15); }}
            .event-info h3 {{ font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 1.3rem; color: #00ffcc; margin-bottom: 8px; }}
            .event-info .competition {{
                font-family: 'Audiowide', cursive; color: #88ffdd; font-size: 0.9rem;
                background: rgba(0, 255, 204, 0.1); padding: 4px 12px; border-radius: 20px; display: inline-block; margin-bottom: 10px;
            }}
            .event-info .datetime {{ color: #88ddff; font-size: 0.9rem; opacity: 0.8; }}
            .fonte-badge {{
                display: inline-block; font-size: 0.75rem; background: rgba(0, 255, 204, 0.15);
                color: #88ffdd; padding: 2px 12px; border-radius: 12px; margin-top: 5px; border: 1px solid rgba(0, 255, 204, 0.2);
            }}
            .status-next {{
                display: inline-block; font-size: 0.7rem; background: rgba(0, 100, 255, 0.3);
                color: #4488ff; padding: 2px 10px; border-radius: 12px; margin-left: 8px;
            }}
            .event-links {{ margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(0, 255, 204, 0.15); }}
            .server-link {{
                display: inline-block; font-family: 'Orbitron', monospace; font-weight: 700; color: #0a0a0a;
                background: #00ffcc; padding: 12px 24px; border-radius: 8px; text-decoration: none;
                text-align: center; width: 100%; transition: all 0.3s ease;
            }}
            .server-link:hover {{ background: #00ddbb; box-shadow: 0 0 40px rgba(0, 255, 204, 0.5); }}
            .dropdown select {{
                width: 100%; padding: 12px 15px; background: rgba(0, 20, 20, 0.9); color: #00ffcc;
                border: 1px solid rgba(0, 255, 204, 0.4); border-radius: 10px; font-family: 'Orbitron', monospace;
                font-size: 0.85rem; cursor: pointer; outline: none;
            }}
            .footer {{ text-align: center; padding: 40px 0 20px; margin-top: 60px; border-top: 1px solid rgba(0, 255, 204, 0.2); color: #88ddff; opacity: 0.7; }}
            .footer .neon-text {{ font-family: 'Orbitron', monospace; color: #00ffcc; font-size: 1rem; }}
        </style>
    </head>
    <body>
        <div class="matrix-bg"></div>
        <div class="container">
            <header class="header">
                <h1>KIRA GATE ACCESS</h1>
                <p class="subtitle">• Embedded Live Sports •</p>
            </header>
            <div style="text-align: center;">
                <div class="event-counter">
                    🎯 <span>{total_events}</span> eventi disponibili
                </div>
            </div>
            <div class="events-grid">
{cards_joined}
            </div>
            <footer class="footer">
                <p class="neon-text">KIRA GSI SPORT • Eventi in Diretta • {now.year} • Developed by KIRA GSI GROUP</p>
            </footer>
        </div>
    </body>
    </html>
    '''

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_output)
    print(f"✅ HTML generato: {OUTPUT_HTML} ({total_events} eventi)")


def main():
    events = parse_txt()
    if not events:
        return
    write_html(events)
    write_m3u(events)


if __name__ == "__main__":
    main()
