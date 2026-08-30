import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from pathlib import Path

def extract_events():
    url = "https://www.rojadirecta.st/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        events = []
        
        # METODO 1: Da JSON-LD
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if data.get('@type') == 'ItemList' and 'itemListElement' in data:
                    for item in data['itemListElement']:
                        event_data = item.get('item', {})
                        if event_data.get('@type') == 'SportsEvent':
                            name = event_data.get('name', '')
                            sport = event_data.get('sport', '')
                            
                            competition = sport or ''
                            teams = name
                            
                            # Estrai canali dal HTML (fallback)
                            channels = []
                            
                            events.append({
                                'time': event_data.get('startDate', '').split('T')[1][:5] if 'startDate' in event_data else '',
                                'competition': competition,
                                'teams': teams,
                                'full_title': name,
                                'start_date': event_data.get('startDate', ''),
                                'channels': channels,
                                'channel_count': 0,
                                'source': 'rojadirecta.st'
                            })
                    return events
            except:
                continue
        
        # METODO 2: Da HTML
        match_divs = soup.find_all('div', class_='match')
        
        for match in match_divs:
            row = match.find('div', class_='row')
            if not row:
                continue
            
            time_span = row.find('span', class_='time')
            time = time_span.get_text(strip=True) if time_span else ''
            
            name_span = row.find('span', class_='name')
            if not name_span:
                continue
            
            event_text = name_span.get_text(strip=True)
            event_text = re.sub(r'[▸▼›]$', '', event_text).strip()
            
            competition = ''
            teams = event_text
            if ':' in event_text:
                parts = event_text.split(':', 1)
                competition = parts[0].strip()
                teams = parts[1].strip()
            elif ' - ' in event_text:
                parts = event_text.split(' - ', 1)
                competition = parts[0].strip()
                teams = parts[1].strip() if len(parts) > 1 else ''
            
            channels = []
            channels_div = match.find('div', class_='chans')
            if channels_div:
                channel_links = channels_div.find_all('a')
                for link in channel_links:
                    channel_url = link.get('href', '')
                    channel_name = link.get_text(strip=True)
                    if channel_url and not channel_url.startswith('#'):
                        channels.append({
                            'name': channel_name,
                            'url': channel_url
                        })
            
            events.append({
                'time': time,
                'competition': competition,
                'teams': teams,
                'full_title': event_text,
                'channels': channels,
                'channel_count': len(channels),
                'source': 'rojadirecta.st',
                'start_date': ''
            })
        
        return events
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return []

def generate_html(events):
    today = datetime.now().strftime("%d-%m-%Y")
    filename = f"Agenda Sportiva ({today}).html"
    
    # Raggruppa eventi per orario
    by_time = {}
    for event in events:
        time = event.get('time', '??:??')
        if time not in by_time:
            by_time[time] = []
        by_time[time].append(event)
    
    # Crea le righe HTML degli eventi
    events_html = ""
    for time in sorted(by_time.keys()):
        events_html += f"""
                <div class="time-slot">
                    <div class="time-header">{time}</div>
                    <div class="events-list">"""
        
        for event in by_time[time]:
            channels_html = ""
            if event.get('channels'):
                channels_html = '<div class="channels">'
                for ch in event['channels'][:5]:  # Mostra max 5 canali
                    channels_html += f'<a href="{ch["url"]}" target="_blank" class="channel-link">{ch["name"]}</a>'
                if len(event['channels']) > 5:
                    channels_html += f'<span class="more-channels">+{len(event["channels"])-5} più</span>'
                channels_html += '</div>'
            
            events_html += f"""
                        <div class="event-card">
                            <div class="event-info">
                                <span class="competition">{event['competition']}</span>
                                <span class="teams">{event['teams']}</span>
                            </div>
                            {channels_html}
                        </div>"""
        
        events_html += """
                    </div>
                </div>"""
    
    # HTML completo con stile cyberpunk
    html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KIRA GSI AGENDA SPORTIVA</title>
    <link href="https://fonts.googleapis.com/css2?family=Audiowide&family=Orbitron:wght@400;700;900&family=Space+Grotesk:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Space Grotesk', sans-serif;
            background: #000;
            color: #00ff41;
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }}

        /* Matrix Rain Effect */
        #matrix-bg {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            pointer-events: none;
            opacity: 0.15;
            background: #000;
            overflow: hidden;
        }}

        .matrix-column {{
            position: absolute;
            top: -100%;
            animation: matrixFall linear infinite;
            color: #00ff41;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            text-shadow: 0 0 10px #00ff41;
            white-space: nowrap;
            opacity: 0.3;
        }}

        @keyframes matrixFall {{
            0% {{ transform: translateY(0); opacity: 0.3; }}
            100% {{ transform: translateY(100vh); opacity: 0.1; }}
        }}

        /* Glitch overlay */
        .glitch-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
            pointer-events: none;
            background: 
                linear-gradient(transparent 50%, rgba(0, 255, 65, 0.03) 50%);
            background-size: 100% 4px;
            animation: scanlines 8s linear infinite;
        }}

        @keyframes scanlines {{
            0% {{ background-position: 0 0; }}
            100% {{ background-position: 0 100%; }}
        }}

        /* Main Container */
        .container {{
            position: relative;
            z-index: 2;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Header Cyberpunk */
        .header {{
            text-align: center;
            padding: 40px 20px 30px;
            border-bottom: 2px solid #00ff41;
            margin-bottom: 40px;
            position: relative;
            background: rgba(0, 0, 0, 0.8);
            border-radius: 10px;
            box-shadow: 0 0 40px rgba(0, 255, 65, 0.1);
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: -2px;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, #00ff41, transparent);
            animation: glitchLine 3s infinite;
        }}

        @keyframes glitchLine {{
            0%, 100% {{ transform: translateX(-100%); }}
            50% {{ transform: translateX(100%); }}
        }}

        .header h1 {{
            font-family: 'Orbitron', sans-serif;
            font-weight: 900;
            font-size: 3em;
            color: #00ff41;
            text-shadow: 
                0 0 20px #00ff41,
                0 0 40px #00ff41,
                0 0 80px rgba(0, 255, 65, 0.3);
            letter-spacing: 4px;
            animation: glitch 3s infinite;
        }}

        @keyframes glitch {{
            0%, 100% {{ transform: translate(0); }}
            20% {{ transform: translate(-2px, 2px); }}
            40% {{ transform: translate(2px, -2px); }}
            60% {{ transform: translate(-1px, 1px); }}
            80% {{ transform: translate(1px, -1px); }}
        }}

        .header .subtitle {{
            font-family: 'Audiowide', cursive;
            font-size: 1.2em;
            color: #00cc33;
            margin-top: 10px;
            letter-spacing: 8px;
            text-shadow: 0 0 20px rgba(0, 255, 65, 0.3);
        }}

        .header .date {{
            font-family: 'Orbitron', sans-serif;
            font-weight: 400;
            font-size: 1em;
            color: #00ff41;
            margin-top: 15px;
            padding: 8px 20px;
            border: 1px solid #00ff41;
            display: inline-block;
            border-radius: 5px;
            background: rgba(0, 255, 65, 0.05);
            letter-spacing: 2px;
        }}

        /* Stats Bar */
        .stats-bar {{
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 15px;
            padding: 20px;
            margin-bottom: 30px;
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #00ff41;
            border-radius: 10px;
            box-shadow: 0 0 30px rgba(0, 255, 65, 0.05);
        }}

        .stat-item {{
            text-align: center;
            font-family: 'Orbitron', sans-serif;
        }}

        .stat-item .number {{
            font-size: 2em;
            font-weight: 900;
            color: #00ff41;
            text-shadow: 0 0 20px rgba(0, 255, 65, 0.5);
        }}

        .stat-item .label {{
            font-size: 0.7em;
            color: #00cc33;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 5px;
        }}

        /* Events Grid */
        .events-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
        }}

        .time-slot {{
            background: rgba(0, 0, 0, 0.85);
            border: 1px solid #00ff41;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 0 30px rgba(0, 255, 65, 0.05);
            transition: all 0.3s ease;
        }}

        .time-slot:hover {{
            box-shadow: 0 0 50px rgba(0, 255, 65, 0.15);
            border-color: #00ff41;
        }}

        .time-header {{
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            font-size: 1.5em;
            padding: 15px 20px;
            background: rgba(0, 255, 65, 0.05);
            border-bottom: 1px solid #00ff41;
            color: #00ff41;
            text-shadow: 0 0 20px rgba(0, 255, 65, 0.3);
            letter-spacing: 2px;
        }}

        .events-list {{
            padding: 10px;
        }}

        .event-card {{
            padding: 12px 15px;
            margin: 8px 0;
            background: rgba(0, 255, 65, 0.02);
            border-left: 3px solid #00ff41;
            border-radius: 5px;
            transition: all 0.3s ease;
        }}

        .event-card:hover {{
            background: rgba(0, 255, 65, 0.08);
            transform: translateX(5px);
            box-shadow: 0 0 20px rgba(0, 255, 65, 0.05);
        }}

        .event-info {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: baseline;
        }}

        .competition {{
            font-family: 'Audiowide', cursive;
            font-size: 0.85em;
            color: #00cc33;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 2px 10px;
            border: 1px solid #00cc33;
            border-radius: 3px;
            background: rgba(0, 204, 51, 0.05);
        }}

        .teams {{
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            font-size: 1.1em;
            color: #00ff41;
            text-shadow: 0 0 10px rgba(0, 255, 65, 0.1);
        }}

        .channels {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 8px;
            padding-left: 5px;
        }}

        .channel-link {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.75em;
            color: #000;
            background: #00ff41;
            padding: 3px 12px;
            border-radius: 3px;
            text-decoration: none;
            transition: all 0.3s ease;
            font-weight: 600;
            letter-spacing: 0.5px;
        }}

        .channel-link:hover {{
            background: #fff;
            color: #000;
            box-shadow: 0 0 20px #00ff41;
            transform: scale(1.05);
        }}

        .more-channels {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.75em;
            color: #00cc33;
            padding: 3px 10px;
            border: 1px dashed #00cc33;
            border-radius: 3px;
            opacity: 0.7;
        }}

        /* Footer */
        .footer {{
            margin-top: 50px;
            padding: 30px 20px;
            text-align: center;
            border-top: 2px solid #00ff41;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.9em;
            color: #00cc33;
            letter-spacing: 4px;
            background: rgba(0, 0, 0, 0.8);
            border-radius: 10px;
            position: relative;
            overflow: hidden;
        }}

        .footer::before {{
            content: '◈ ◈ ◈ ◈ ◈';
            display: block;
            margin-bottom: 10px;
            letter-spacing: 10px;
            color: #00ff41;
            opacity: 0.3;
        }}

        .footer .glitch-text {{
            animation: glitch 4s infinite;
            display: inline-block;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            .header .subtitle {{
                font-size: 0.9em;
                letter-spacing: 4px;
            }}
            .stat-item .number {{
                font-size: 1.5em;
            }}
            .time-header {{
                font-size: 1.2em;
            }}
            .teams {{
                font-size: 0.95em;
            }}
            .competition {{
                font-size: 0.75em;
            }}
            .event-card {{
                padding: 10px;
            }}
        }}

        @media (max-width: 480px) {{
            .header h1 {{
                font-size: 1.3em;
            }}
            .stats-bar {{
                flex-direction: column;
                gap: 10px;
            }}
            .channel-link {{
                font-size: 0.7em;
                padding: 2px 8px;
            }}
        }}
    </style>
</head>
<body>
    <!-- Matrix Background -->
    <div id="matrix-bg"></div>
    <div class="glitch-overlay"></div>

    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>KIRA GSI</h1>
            <div class="subtitle">AGENDA SPORTIVA</div>
            <div class="date">📅 {datetime.now().strftime("%A, %d %B %Y").upper()}</div>
        </header>

        <!-- Stats -->
        <div class="stats-bar">
            <div class="stat-item">
                <div class="number">{len(events)}</div>
                <div class="label">Eventi Totali</div>
            </div>
            <div class="stat-item">
                <div class="number">{len(by_time)}</div>
                <div class="label">Fasce Orarie</div>
            </div>
            <div class="stat-item">
                <div class="number">{sum(1 for e in events if e.get('channels'))}</div>
                <div class="label">Con Canali</div>
            </div>
            <div class="stat-item">
                <div class="number">{sum(e.get('channel_count', 0) for e in events)}</div>
                <div class="label">Canali Totali</div>
            </div>
        </div>

        <!-- Events -->
        <div class="events-grid">
            {events_html}
        </div>

        <!-- Footer -->
        <footer class="footer">
            <div class="glitch-text">DEVELOPED BY GSI GROUP 2026</div>
            <div style="font-size: 0.6em; margin-top: 10px; opacity: 0.5; letter-spacing: 2px;">
                ⚡ DATA SOURCE: ROJADIRECTA.ST ⚡
            </div>
        </footer>
    </div>

    <script>
        // Matrix Rain Effect
        (function() {{
            const container = document.getElementById('matrix-bg');
            const columns = Math.floor(window.innerWidth / 20);
            const chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';
            
            for (let i = 0; i < columns; i++) {{
                const col = document.createElement('div');
                col.className = 'matrix-column';
                const x = i * 20 + Math.random() * 10;
                const duration = 8 + Math.random() * 12;
                const delay = Math.random() * 15;
                const length = 15 + Math.floor(Math.random() * 20);
                
                let text = '';
                for (let j = 0; j < length; j++) {{
                    text += chars[Math.floor(Math.random() * chars.length)] + ' ';
                }}
                
                col.textContent = text;
                col.style.left = x + 'px';
                col.style.animationDuration = duration + 's';
                col.style.animationDelay = delay + 's';
                col.style.fontSize = (12 + Math.random() * 10) + 'px';
                col.style.opacity = 0.1 + Math.random() * 0.2;
                
                container.appendChild(col);
            }}
        }})();

        // Glitch effect on header
        setInterval(() => {{
            const header = document.querySelector('.header h1');
            if (Math.random() < 0.05) {{
                header.style.textShadow = '0 0 20px #ff00ff, 0 0 40px #00ffff';
                setTimeout(() => {{
                    header.style.textShadow = '0 0 20px #00ff41, 0 0 40px #00ff41';
                }}, 100);
            }}
        }}, 2000);
    </script>
</body>
</html>"""
    
    # Salva il file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML generato: {filename}")
    return filename

if __name__ == "__main__":
    print("🔍 Estraendo eventi da Rojadirecta.st...")
    events = extract_events()
    
    if events:
        print(f"✅ Estratti {len(events)} eventi")
        filename = generate_html(events)
        print(f"📄 Apri il file: {filename}")
    else:
        print("❌ Nessun evento trovato")