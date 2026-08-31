import re
from urllib.request import urlopen, Request
from datetime import datetime, timedelta
from html import escape
from bs4 import BeautifulSoup

# --- Configurazione ---

BASE_URL = "https://www.htsport.org/"

def fetch_html(url):
    """Recupera il HTML della pagina."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        req = Request(url, headers=headers)
        with urlopen(req, timeout=20) as response:
            content = response.read().decode('utf-8', errors='ignore')
            return content
    except Exception as e:
        print(f"⚠️ Errore nel recupero di {url}: {e}")
        return None

def parse_htsport_events(html, remove_past=True):
    """Estrae gli eventi dal HTML di htsport.org."""
    events = []
    if not html:
        return events
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Data corrente
    today = datetime.now().date()
    today_str = today.strftime('%d/%m')
    
    print(f"📅 Data corrente: {today.strftime('%A, %d %B %Y')}")
    print(f"📅 Filtro: Rimuovi eventi passati (data < {today_str})")
    
    # Cerca tutte le match-card
    match_cards = soup.find_all('div', class_='match-card')
    
    print(f"📦 Trovate {len(match_cards)} card di eventi")
    
    for card in match_cards:
        try:
            # --- Estrai orario ---
            time_box = card.find('div', class_='time-box')
            time = "N/D"
            if time_box:
                strong = time_box.find('strong')
                if strong:
                    time = strong.text.strip()
            
            # --- Estrai la data ---
            event_date = None
            date_header = card.find_previous_sibling('div', class_='date-header')
            if date_header:
                date_text = date_header.get_text(strip=True)
                date_match = re.search(r'(\d{1,2})/(\d{1,2})', date_text)
                if date_match:
                    day = int(date_match.group(1))
                    month = int(date_match.group(2))
                    year = datetime.now().year
                    try:
                        event_date = datetime(year, month, day).date()
                    except:
                        pass
            
            # Se non c'è una data specifica, usa quella di oggi
            if event_date is None:
                event_date = today
            
            # --- FILTRO: Rimuovi eventi passati ---
            if remove_past and event_date < today:
                continue
            
            # --- Estrai nome evento ---
            teams_box = card.find('div', class_='teams-box')
            if not teams_box:
                continue
            
            event_text = teams_box.get_text(separator=' ', strip=True)
            event_text = re.sub(r'\d+-\d+', '', event_text).strip()
            
            event_name = None
            
            dash_match = re.search(r'([A-Za-zÁ-Úá-úñÑ\s\-\.]+)\s*[-–]\s*([A-Za-zÁ-Úá-úñÑ\s\-\.]+)', event_text)
            if dash_match:
                team1 = dash_match.group(1).strip()
                team2 = dash_match.group(2).strip()
                if team1 and team2:
                    event_name = f"{team1} VS {team2}"
            
            if not event_name:
                vs_match = re.search(r'([A-Za-zÁ-Úá-úñÑ\s\-\.]+)\s+VS\s+([A-Za-zÁ-Úá-úñÑ\s\-\.]+)', event_text, re.IGNORECASE)
                if vs_match:
                    team1 = vs_match.group(1).strip()
                    team2 = vs_match.group(2).strip()
                    if team1 and team2:
                        event_name = f"{team1} VS {team2}"
            
            if not event_name:
                continue
            
            # --- Estrai competizione ---
            competition = "Sconosciuta"
            prev_sibling = card.find_previous_sibling('span', class_='category-label')
            if prev_sibling:
                comp_text = prev_sibling.get_text(strip=True)
                comp_text = re.sub(r'[^\w\s\-]', '', comp_text).strip()
                if comp_text:
                    competition = comp_text
            
            if competition == "Sconosciuta":
                card_text = card.get_text()
                comp_keywords = {
                    'Champions League': ['Champions League', 'Champions'],
                    'Liga': ['Liga', 'La Liga'],
                    'Serie A': ['Serie A'],
                    'Premier League': ['Premier League', 'EPL'],
                    'Bundesliga': ['Bundesliga'],
                    'Ligue 1': ['Ligue 1'],
                    'Copa Libertadores': ['Copa Libertadores', 'Libertadores'],
                    'Copa Sudamericana': ['Copa Sudamericana'],
                    'Coppa Italia': ['Coppa Italia'],
                    'FA Cup': ['FA Cup'],
                    'Carabao Cup': ['Carabao Cup'],
                    'MLS': ['MLS'],
                    'Europa League': ['Europa League']
                }
                for comp, keywords in comp_keywords.items():
                    if any(kw.lower() in card_text.lower() for kw in keywords):
                        competition = comp
                        break
            
            # --- Estrai TUTTI i link ---
            links = []
            btn_group = card.find('div', class_='btn-group')
            if btn_group:
                for a in btn_group.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('/'):
                        full_url = f"https://www.htsport.org{href}"
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = f"https://www.htsport.org/{href}"
                    
                    channel_name = a.get_text(strip=True)
                    links.append({
                        'url': full_url,
                        'channel': channel_name
                    })
            
            # --- Formatta la data ---
            giorno = event_date.strftime('%A, %d %B %Y')
            data_ordine = event_date.strftime('%Y-%m-%d') + ' ' + (time if time != 'N/D' else '00:00')
            
            # Aggiungi un flag per indicare se è oggi o futuro
            is_today = event_date == today
            is_future = event_date > today
            
            # Crea l'evento
            event_data = {
                'nome_evento': event_name,
                'competizione': competition,
                'orario': time,
                'giorno': giorno,
                'data_ordine': data_ordine,
                'links': links,
                'source': 'htsport',
                'is_today': is_today,
                'is_future': is_future
            }
            events.append(event_data)
            
        except Exception as e:
            print(f"   ⚠️ Errore nell'estrazione evento: {e}")
            continue
    
    return events

def group_and_sort_events(events):
    """Raggruppa eventi duplicati e li ordina cronologicamente."""
    grouped = {}
    
    for event in events:
        key = f"{event['nome_evento']}_{event['giorno']}"
        
        if key not in grouped:
            grouped[key] = {
                'nome_evento': event['nome_evento'],
                'competizione': event['competizione'],
                'orario': event['orario'],
                'giorno': event['giorno'],
                'data_ordine': event.get('data_ordine', ''),
                'links': [],
                'channels': [],
                'sources': [],
                'is_today': event.get('is_today', False),
                'is_future': event.get('is_future', False)
            }
        
        for link_data in event['links']:
            url = link_data.get('url', '')
            channel = link_data.get('channel', 'Canale')
            if url and url not in [l['url'] for l in grouped[key]['links']]:
                grouped[key]['links'].append(link_data)
                if channel not in grouped[key]['channels']:
                    grouped[key]['channels'].append(channel)
        
        if event.get('source') not in grouped[key]['sources']:
            grouped[key]['sources'].append(event.get('source', 'unknown'))
    
    result = list(grouped.values())
    result.sort(key=lambda x: x.get('data_ordine', '9999-99-99 99:99'))
    
    return result

def generate_html(events, title="Eventi Sportivi in Diretta", header="HTSport Events", footer="© 2026 HTSport - Tutti i diritti riservati"):
    """Genera la pagina HTML con gli eventi e lo stile cyberpunk."""
    
    event_items = []
    for event in events:
        links_html = ""
        valid_links = event.get('links', [])
        
        sources_text = ""
        if event.get('sources'):
            sources_text = f" ({', '.join(event['sources'])})"
        
        if len(valid_links) > 1:
            options = "\n".join([f'<option value="{l["url"]}">{l["channel"]}</option>' for l in valid_links])
            links_html = f'''
            <div class="dropdown">
                <select onchange="window.open(this.value, '_blank'); this.selectedIndex=0;">
                    <option value="">📡 Scegli il canale...</option>
                    {options}
                </select>
                <div class="source-info">Fonte{sources_text}</div>
            </div>
            '''
        elif len(valid_links) == 1:
            link = valid_links[0]
            channel = link.get('channel', '▶ GUARDA IN DIRETTA')
            links_html = f'''
            <a href="{link["url"]}" target="_blank" class="server-link">{channel}</a>
            <div class="source-info">Fonte{sources_text}</div>
            '''
        else:
            links_html = f'''
            <span class="no-link">🔗 Link non disponibile</span>
            <div class="source-info">Fonte{sources_text}</div>
            '''
        
        # Badge per oggi o futuro
        badge = ""
        if event.get('is_today'):
            badge = '<span style="background: #00ffcc; color: #0a0a0a; padding: 2px 12px; border-radius: 12px; font-size: 0.7rem; margin-left: 10px; font-weight: bold;">OGGI</span>'
        elif event.get('is_future'):
            badge = '<span style="background: #ff00cc; padding: 2px 12px; border-radius: 12px; font-size: 0.7rem; margin-left: 10px;">PROSSIMO</span>'

        event_items.append(f'''
        <div class="event-card">
            <div class="event-info">
                <h3>{escape(event['nome_evento'])}{badge}</h3>
                <p class="competition">🏆 {escape(event['competizione'])}</p>
                <p class="datetime">🕒 {escape(event['orario'])} • 📅 {escape(event['giorno'])}</p>
            </div>
            <div class="event-links">
                {links_html}
            </div>
        </div>
        ''')

    # Conta eventi di oggi e futuri
    oggi_count = sum(1 for e in events if e.get('is_today'))
    futuro_count = sum(1 for e in events if e.get('is_future'))

    html_content = f'''
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{escape(title)}</title>
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
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: -1;
                background: #0a0a0a;
                overflow: hidden;
            }}
            .matrix-bg::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: repeating-linear-gradient(
                    0deg,
                    transparent,
                    transparent 2px,
                    rgba(0, 255, 204, 0.03) 2px,
                    rgba(0, 255, 204, 0.03) 4px
                );
                animation: matrixScroll 15s linear infinite;
            }}
            @keyframes matrixScroll {{
                0% {{ transform: translateY(0); }}
                100% {{ transform: translateY(100%); }}
            }}
            .matrix-bg::after {{
                content: '010010110100100101001000100100101001011010010110100101101001011010010110';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                color: rgba(0, 255, 204, 0.04);
                font-family: 'Orbitron', monospace;
                font-size: 14px;
                line-height: 1.8;
                word-break: break-all;
                animation: matrixText 30s linear infinite;
            }}
            @keyframes matrixText {{
                0% {{ transform: translateY(0); opacity: 0.5; }}
                50% {{ opacity: 1; }}
                100% {{ transform: translateY(-50%); opacity: 0.5; }}
            }}
            .matrix-bg .glow {{
                position: absolute;
                width: 300px;
                height: 300px;
                border-radius: 50%;
                filter: blur(100px);
                opacity: 0.15;
            }}
            .matrix-bg .glow.g1 {{ background: #00ffcc; top: -50px; left: -100px; animation: floatGlow 20s ease-in-out infinite; }}
            .matrix-bg .glow.g2 {{ background: #ff00cc; bottom: -50px; right: -100px; animation: floatGlow 25s ease-in-out infinite reverse; }}
            @keyframes floatGlow {{
                0%, 100% {{ transform: translate(0, 0) scale(1); }}
                50% {{ transform: translate(50px, -30px) scale(1.2); }}
            }}

            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                position: relative;
                z-index: 1;
                backdrop-filter: blur(2px);
            }}

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
                text-shadow: 0 0 20px rgba(0, 255, 204, 0.5), 0 0 40px rgba(0, 255, 204, 0.2);
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
                opacity: 0.9;
                text-shadow: 0 0 15px rgba(0, 255, 204, 0.3);
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
                backdrop-filter: blur(10px);
            }}
            .event-counter span {{
                font-weight: 900;
                font-size: 1.5rem;
            }}

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
                box-shadow: 0 0 30px rgba(0, 255, 204, 0.05);
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
                font-size: 1.3rem;
                color: #00ffcc;
                margin-bottom: 8px;
                text-shadow: 0 0 10px rgba(0, 255, 204, 0.2);
            }}
            .event-info .competition {{
                font-family: 'Audiowide', cursive;
                color: #88ddff;
                font-size: 0.9rem;
                background: rgba(0, 255, 204, 0.1);
                padding: 4px 12px;
                border-radius: 20px;
                display: inline-block;
                margin-bottom: 10px;
                letter-spacing: 1px;
            }}
            .event-info .datetime {{
                font-family: 'Grotesk', sans-serif;
                color: #88ddff;
                font-size: 0.9rem;
                opacity: 0.8;
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
                transition: all 0.3s ease;
                font-size: 0.85rem;
                letter-spacing: 1px;
                box-shadow: 0 0 20px rgba(0, 255, 204, 0.3);
                width: 100%;
                text-align: center;
            }}
            .server-link:hover {{
                background: #00ddbb;
                box-shadow: 0 0 40px rgba(0, 255, 204, 0.5);
                transform: scale(1.02);
            }}
            .no-link {{
                color: #ff6688;
                font-size: 0.9rem;
                text-align: center;
                display: block;
            }}
            .source-info {{
                font-size: 0.7rem;
                color: #88ddff;
                opacity: 0.6;
                text-align: center;
                margin-top: 5px;
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
                transition: all 0.3s ease;
                appearance: none;
                background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2300ffcc' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
                background-repeat: no-repeat;
                background-position: right 15px center;
                background-size: 15px;
            }}
            .dropdown select:hover, .dropdown select:focus {{
                border-color: #00ffcc;
                box-shadow: 0 0 25px rgba(0, 255, 204, 0.2);
            }}
            .dropdown select option {{
                background: #0a1a1a;
                color: #88ffdd;
                padding: 10px;
            }}

            .footer {{
                text-align: center;
                padding: 40px 0 20px;
                margin-top: 60px;
                border-top: 1px solid rgba(0, 255, 204, 0.2);
                font-family: 'Grotesk', sans-serif;
                color: #88ddff;
                opacity: 0.7;
                font-size: 0.9rem;
            }}
            .footer .neon-text {{
                font-family: 'Orbitron', monospace;
                color: #00ffcc;
                opacity: 1;
                font-size: 1rem;
                text-shadow: 0 0 15px rgba(0, 255, 204, 0.2);
            }}

            @media (max-width: 768px) {{
                .header h1 {{ font-size: 2.2rem; }}
                .events-grid {{ grid-template-columns: 1fr; }}
                .container {{ padding: 15px; }}
                .event-card {{ padding: 18px; }}
            }}
        </style>
    </head>
    <body>
        <div class="matrix-bg">
            <div class="glow g1"></div>
            <div class="glow g2"></div>
        </div>

        <div class="container">
            <header class="header">
                <h1>{escape(header)}</h1>
                <p class="subtitle">• Oggi e Prossimi Eventi •</p>
            </header>

            <div style="text-align: center;">
                <div class="event-counter">
                    🎯 <span>{len(events)}</span> eventi disponibili (Oggi: {oggi_count} | Futuri: {futuro_count})
                </div>
            </div>

            <div class="events-grid">
                {''.join(event_items)}
            </div>

            <footer class="footer">
                <p class="neon-text">{escape(footer)}</p>
                <p style="margin-top: 8px; font-size: 0.8rem;">🖥️ Aggiornato in tempo reale • Eventi da oggi in poi</p>
            </footer>
        </div>
    </body>
    </html>
    '''
    return html_content

def main():
    print("🚀 Avvio estrazione eventi da htsport.org (OGGI e FUTURI)...\n")
    
    print("📥 Recupero della pagina...")
    html = fetch_html(BASE_URL)
    if not html:
        print("❌ Impossibile recuperare la pagina")
        return
    
    print("\n🔍 Estrazione eventi...")
    events = parse_htsport_events(html, remove_past=True)
    
    if not events:
        print("\n⚠️ Nessun evento trovato per oggi o nel futuro.")
        print("📌 Controlla se ci sono eventi in programma")
        return
    
    # Raggruppa e ordina
    grouped_events = group_and_sort_events(events)
    
    oggi_count = sum(1 for e in grouped_events if e.get('is_today'))
    futuro_count = sum(1 for e in grouped_events if e.get('is_future'))
    
    print(f"\n📊 Riepilogo:")
    print(f"   • Eventi totali: {len(grouped_events)}")
    print(f"   • Eventi di oggi: {oggi_count}")
    print(f"   • Eventi futuri: {futuro_count}")
    
    total_links = sum(len(e.get('links', [])) for e in grouped_events)
    print(f"   • Link totali: {total_links}")
    
    # Mostra gli eventi
    print("\n📋 Eventi:")
    for i, event in enumerate(grouped_events):
        badge = "OGGI" if event.get('is_today') else "FUTURO" if event.get('is_future') else ""
        print(f"   {i+1}. [{badge}] {event['nome_evento']} - {event['orario']}")
        channels = [l.get('channel', 'Canale') for l in event.get('links', [])]
        print(f"      📡 Canali: {', '.join(channels)}")
    
    # Genera HTML
    html_output = generate_html(
        grouped_events,
        title="HTSport Live - Eventi OGGI e FUTURI",
        header="⚡ HTSPORT LIVE ⚡",
        footer="🔮 HTSport • Eventi da oggi in poi • 2026 • Powered by Matrix"
    )
    
    # Salva il file
    filename = "htsport_today_future.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"\n✅ HTML generato con successo: {filename}")
    print(f"📁 Apri il file {filename} nel tuo browser.")

if __name__ == "__main__":
    main()
