import re
from urllib.request import urlopen, Request
from datetime import datetime, timezone, timedelta
from html import escape
from bs4 import BeautifulSoup

BASE_URL = "https://www.htsport.org/"


def get_italy_tz():
    """Fuso orario italiano (CET/CEST) senza dipendere da tzdata."""
    now_utc = datetime.now(timezone.utc)
    year = now_utc.year

    march_last = datetime(year, 3, 31, tzinfo=timezone.utc)
    march_last -= timedelta(days=(march_last.weekday() + 1) % 7)
    oct_last = datetime(year, 10, 31, tzinfo=timezone.utc)
    oct_last -= timedelta(days=(oct_last.weekday() + 1) % 7)

    dst_start = march_last.replace(hour=1)
    dst_end = oct_last.replace(hour=1)

    if dst_start <= now_utc < dst_end:
        return timezone(timedelta(hours=2), name="CEST")
    return timezone(timedelta(hours=1), name="CET")


TZ_ROMA = get_italy_tz()

MESI_IT = {
    'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
    'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
    'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12,
}


def fetch_html(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        req = Request(url, headers=headers)
        with urlopen(req, timeout=20) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"⚠️ Errore nel recupero di {url}: {e}")
        return None


def parse_italian_date(text, today):
    """Parsa 'VENERDÌ 11 SETTEMBRE' → datetime.date."""
    if not text:
        return None
    t = text.lower().strip()
    m = re.search(
        r'(\d{1,2})\s+(' + '|'.join(MESI_IT.keys()) + r')(?:\s+(\d{4}))?',
        t
    )
    if not m:
        return None
    day = int(m.group(1))
    month = MESI_IT[m.group(2)]
    year = int(m.group(3)) if m.group(3) else today.year
    try:
        d = datetime(year, month, day).date()
        if (today - d).days > 180:
            d = datetime(year + 1, month, day).date()
        return d
    except ValueError:
        return None


def classify_sport(haystack):
    """Classifica lo sport dalle keyword."""
    h = haystack.lower()
    sport_keywords = {
        'Formula 1': ['formula 1', 'formula1', ' f1 ', 'f1-', 'f1 ',
                      'gran premio', 'gp ', 'gp-', 'gp.'],
        'MotoGP': ['motogp', 'moto2', 'moto3', 'moto 2', 'moto 3', 'superbike'],
        'Tennis': ['atp', 'wta', 'tennis', 'grand slam', 'roland garros',
                   'wimbledon', 'us open', 'australian open'],
        'Basket': ['nba', 'eurolega', 'euroleague', 'basket', 'lega a'],
        'Ciclismo': ['tour de france', "giro d'italia", 'vuelta', 'ciclismo'],
        'Rugby': ['rugby', 'six nations'],
        'Pallavolo': ['pallavolo', 'volley', 'superlega'],
        'Boxe': ['boxe', 'pugilato', 'wbc', 'wba', 'wbo', 'ibf'],
        'MMA': ['mma', 'ufc'],
        'Calcio': ['calcio', 'serie a', 'serie b', 'champions',
                   'europa league', 'conference league', 'premier league',
                   'la liga', 'liga', 'bundesliga', 'ligue 1', 'ligue 2',
                   'coppa italia', 'coppa del re', 'fa cup', 'carabao',
                   'libertadores', 'sudamericana', 'mls', 'eredivisie',
                   'primeira liga'],
    }
    for sport, keywords in sport_keywords.items():
        if any(kw in h for kw in keywords):
            return sport
    return "Altro"


def clean_channel_name(name):
    """Rimuove emoji bandiera e spazi doppi."""
    name = re.sub(
        r'[\U0001F1E6-\U0001F1FF\U0001F3F4\U000E0067-\U000E007F]',
        '', name
    )
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def parse_htsport_events(html, only_today=True):
    events = []
    if not html:
        return events

    soup = BeautifulSoup(html, 'html.parser')
    today = datetime.now(TZ_ROMA).date()

    print(f"📅 Data corrente (Italia): {today.strftime('%A, %d %B %Y')}")
    print(f"📅 Filtro: {'Solo oggi' if only_today else 'Oggi e futuri'}")

    # Regex per gli header di giorno
    day_header_re = re.compile(
        r'(luned|marted|mercoled|gioved|venerd|sabato|domenica|'
        r'lun|mar|mer|gio|ven|sab|dom)[ìi]?\s+\d{1,2}\s+'
        + r'(?:' + '|'.join(MESI_IT.keys()) + r')',
        re.IGNORECASE
    )

    # Regex per category label
    category_re = re.compile(
        r'^(CALCIO|BASKET|TENNIS|F1|FORMULA\s*1|MOTOGP|CICLISMO|RUGBY|'
        r'PALLAVOLO|BOXE|MMA|SPORT)\s*[-–]',
        re.IGNORECASE
    )

    # Ordine documento
    all_elements = soup.find_all(['div', 'h1', 'h2', 'h3', 'span', 'p'])

    current_date = None
    current_competition = "Sconosciuta"
    current_category_raw = ""

    stats = {'no_ts': 0, 'not_today': 0, 'no_name': 0, 'ok': 0}
    total_cards = 0

    for el in all_elements:
        # --- MATCH CARD ---
        if el.name == 'div' and 'match-card' in (el.get('class') or []):
            total_cards += 1
            try:
                # Data
                event_date = current_date if current_date is not None else today

                # Filtro solo oggi
                if only_today and event_date != today:
                    stats['not_today'] += 1
                    continue

                # Orario
                time_box = el.find('div', class_='time-box')
                orario = "N/D"
                if time_box:
                    strong = time_box.find('strong')
                    if strong:
                        orario = strong.get_text(strip=True)
                    else:
                        # A volte l'ora è senza <strong>
                        m = re.search(r'\b(\d{1,2}[:\.]\d{2})\b',
                                      time_box.get_text())
                        if m:
                            orario = m.group(1)

                # Nome evento dal testo visibile della teams-box
                teams_box = el.find('div', class_='teams-box')
                if not teams_box:
                    stats['no_name'] += 1
                    continue

                vs_span = teams_box.find('span', class_='vs-txt')
                if vs_span:
                    vs_span.decompose()

                visible = teams_box.get_text(separator=' ', strip=True).strip()

                PLACEHOLDERS = {'francia', 'spagna', 'live', 'multicast',
                                'elenco canali', 'vs', ''}

                if visible and visible.lower() not in PLACEHOLDERS:
                    event_name = visible
                else:
                    sq1 = (teams_box.get('data-sq1') or '').strip()
                    sq2 = (teams_box.get('data-sq2') or '').strip()
                    if (sq1 and sq1.lower() not in PLACEHOLDERS
                            and sq2 and sq2.lower() not in PLACEHOLDERS):
                        event_name = f"{sq1} VS {sq2}"
                    elif sq1 and sq1.lower() not in PLACEHOLDERS:
                        event_name = sq1
                    else:
                        stats['no_name'] += 1
                        continue

                # Sport dalla categoria
                sport_type = classify_sport(
                    current_category_raw + " " + event_name
                )

                # Data/ora completa
                try:
                    h, mn = map(int, re.split(r'[:\.]', orario))
                    event_dt = datetime.combine(
                        event_date,
                        datetime.min.time().replace(hour=h, minute=mn),
                        tzinfo=TZ_ROMA
                    )
                except Exception:
                    event_dt = datetime.combine(
                        event_date,
                        datetime.min.time(),
                        tzinfo=TZ_ROMA
                    )

                # Link
                links = []
                btn_group = el.find('div', class_='btn-group')
                if btn_group:
                    for a in btn_group.find_all('a', href=True):
                        href = a['href']
                        if href.startswith('http'):
                            full_url = href
                        elif href.startswith('/'):
                            full_url = f"https://www.htsport.org{href}"
                        else:
                            full_url = f"https://www.htsport.org/{href}"
                        channel_name = clean_channel_name(
                            a.get_text(strip=True)
                        )
                        links.append({'url': full_url, 'channel': channel_name})

                giorno = event_dt.strftime('%A, %d %B %Y')
                data_ordine = event_dt.strftime('%Y-%m-%d %H:%M')

                events.append({
                    'nome_evento': event_name,
                    'competizione': current_competition,
                    'orario': orario,
                    'giorno': giorno,
                    'data_ordine': data_ordine,
                    'links': links,
                    'source': 'htsport',
                    'sport': sport_type,
                    'is_today': event_date == today,
                    'is_future': event_date > today,
                })
                stats['ok'] += 1
                print(f"   ✅ [{sport_type}] {event_name} "
                      f"({orario}, {event_date}) - {len(links)} canali")

            except Exception as e:
                print(f"   ⚠️ Errore card: {e}")
                continue

            continue

        # --- HEADER GIORNO o CATEGORY? ---
        txt = el.get_text(strip=True)
        if not txt or len(txt) > 120:
            continue

        # Header giorno
        if day_header_re.search(txt) and len(txt) < 40:
            parsed = parse_italian_date(txt, today)
            if parsed:
                current_date = parsed
                print(f"   📆 Header: '{txt}' → {parsed}")
                continue

        # Category label
        cls = el.get('class') or []
        if 'category-label' in cls or category_re.match(txt):
            # Evita di prendere per sbaglio il testo delle card
            if el.find('div', class_='match-card') is None and \
               'match-card' not in cls:
                current_category_raw = txt
                current_competition = txt
                print(f"   🏷️  Categoria: '{txt}'")

    print(f"\n📊 Statistiche parsing:")
    print(f"   • Card totali: {total_cards}")
    print(f"   • Eventi validi: {stats['ok']}")
    print(f"   • Saltati (non oggi): {stats['not_today']}")
    print(f"   • Saltati (no nome): {stats['no_name']}")

    return events


def group_and_sort_events(events):
    grouped = {}
    for event in events:
        key = f"{event['nome_evento']}_{event['data_ordine']}"
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
                'sport': event.get('sport', 'Altro'),
                'is_today': event.get('is_today', False),
                'is_future': event.get('is_future', False),
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


def generate_html(events, title="Eventi Sportivi in Diretta",
                  header="HTSport Events",
                  footer="© 2026 HTSport"):
    sports_groups = {}
    for event in events:
        sport = event.get('sport', 'Altro')
        sports_groups.setdefault(sport, []).append(event)

    event_items = []
    sport_order = ['Calcio', 'Formula 1', 'MotoGP', 'Tennis', 'Basket',
                   'Ciclismo', 'Rugby', 'Pallavolo', 'Boxe', 'MMA', 'Altro']

    for sport in sport_order:
        if sport not in sports_groups:
            continue
        sport_events = sports_groups[sport]
        event_items.append(f'''
        <div class="sport-header">
            <h2 class="sport-title">🏆 {sport}</h2>
            <span class="sport-count">{len(sport_events)} eventi</span>
        </div>
        ''')
        for event in sport_events:
            valid_links = event.get('links', [])
            sources_text = f" ({', '.join(event['sources'])})" if event.get('sources') else ""

            if len(valid_links) > 1:
                options = "\n".join(
                    [f'<option value="{escape(l["url"])}">{escape(l["channel"])}</option>'
                     for l in valid_links]
                )
                links_html = f'''
                <div class="dropdown">
                    <select onchange="window.open(this.value, '_blank'); this.selectedIndex=0;">
                        <option value="">📡 Scegli il canale ({len(valid_links)})...</option>
                        {options}
                    </select>
                    <div class="source-info">Fonte{sources_text}</div>
                </div>
                '''
            elif len(valid_links) == 1:
                link = valid_links[0]
                links_html = f'''
                <a href="{escape(link["url"])}" target="_blank" class="server-link">{escape(link['channel'])}</a>
                <div class="source-info">Fonte{sources_text}</div>
                '''
            else:
                links_html = f'''
                <span class="no-link">🔗 Link non disponibile</span>
                <div class="source-info">Fonte{sources_text}</div>
                '''

            badge = '<span class="today-badge">OGGI</span>' if event.get('is_today') else ''
            event_items.append(f'''
            <div class="event-card">
                <div class="event-info">
                    <h3>{escape(event['nome_evento'])}{badge}</h3>
                    <p class="competition">🏆 {escape(event['competizione'])}</p>
                    <p class="datetime">🕒 {escape(event['orario'])} • 📅 {escape(event['giorno'])}</p>
                </div>
                <div class="event-links">{links_html}</div>
            </div>
            ''')

    html_content = f'''<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>{escape(title)}</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Audiowide&family=Grotesk:wght@400;700&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Grotesk', sans-serif; background: #0a0a0a; color: #00ffcc; min-height: 100vh; overflow-x: hidden; }}
.matrix-bg {{ position: fixed; top:0; left:0; width:100%; height:100%; z-index:-1; background:#0a0a0a; overflow:hidden; }}
.matrix-bg::before {{ content:''; position:absolute; top:0; left:0; width:100%; height:100%;
    background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,204,0.03) 2px, rgba(0,255,204,0.03) 4px);
    animation: matrixScroll 15s linear infinite; }}
@keyframes matrixScroll {{ 0%{{transform:translateY(0)}} 100%{{transform:translateY(100%)}} }}
.matrix-bg::after {{ content:'0100101101001001010010001001001010010110100101101001011010010110';
    position:absolute; top:0; left:0; width:100%; height:100%; color:rgba(0,255,204,0.04);
    font-family:'Orbitron',monospace; font-size:14px; line-height:1.8; word-break:break-all;
    animation: matrixText 30s linear infinite; }}
@keyframes matrixText {{ 0%{{transform:translateY(0);opacity:0.5}} 50%{{opacity:1}} 100%{{transform:translateY(-50%);opacity:0.5}} }}
.matrix-bg .glow {{ position:absolute; width:300px; height:300px; border-radius:50%; filter:blur(100px); opacity:0.15; }}
.matrix-bg .glow.g1 {{ background:#00ffcc; top:-50px; left:-100px; animation: floatGlow 20s ease-in-out infinite; }}
.matrix-bg .glow.g2 {{ background:#ff00cc; bottom:-50px; right:-100px; animation: floatGlow 25s ease-in-out infinite reverse; }}
@keyframes floatGlow {{ 0%,100%{{transform:translate(0,0) scale(1)}} 50%{{transform:translate(50px,-30px) scale(1.2)}} }}
.container {{ max-width:1200px; margin:0 auto; padding:20px; position:relative; z-index:1; backdrop-filter:blur(2px); }}
.header {{ text-align:center; padding:30px 0 40px; border-bottom:2px solid rgba(0,255,204,0.3); margin-bottom:40px; }}
.header h1 {{ font-family:'Orbitron',sans-serif; font-weight:900; font-size:3.5rem;
    text-shadow: 0 0 20px rgba(0,255,204,0.5), 0 0 40px rgba(0,255,204,0.2);
    background: linear-gradient(135deg, #00ffcc, #00ccff); -webkit-background-clip:text;
    -webkit-text-fill-color:transparent; letter-spacing:4px; }}
.header .subtitle {{ font-family:'Audiowide',cursive; color:#88ffdd; font-size:1.2rem;
    margin-top:10px; opacity:0.9; text-shadow: 0 0 15px rgba(0,255,204,0.3); }}
.event-counter {{ text-align:center; font-family:'Orbitron',monospace; font-size:1.2rem;
    color:#00ffcc; background: rgba(0,255,204,0.08); border:1px solid rgba(0,255,204,0.2);
    padding:12px 20px; border-radius:30px; display:inline-block; margin:0 auto 30px; backdrop-filter:blur(10px); }}
.event-counter span {{ font-weight:900; font-size:1.5rem; }}
.sport-header {{ grid-column:1/-1; display:flex; justify-content:space-between; align-items:center;
    padding:15px 20px; background: rgba(0,255,204,0.05); border-left:4px solid #00ffcc;
    border-radius:10px; margin:20px 0 10px 0; }}
.sport-title {{ font-family:'Orbitron',sans-serif; font-weight:700; font-size:1.5rem;
    color:#00ffcc; text-shadow: 0 0 20px rgba(0,255,204,0.3); }}
.sport-count {{ font-family:'Grotesk',sans-serif; color:#88ddff; background: rgba(0,255,204,0.1);
    padding:4px 15px; border-radius:20px; font-size:0.9rem; }}
.events-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(350px, 1fr));
    gap:25px; margin-top:10px; }}
.event-card {{ background: rgba(0,30,30,0.7); backdrop-filter:blur(10px);
    border:1px solid rgba(0,255,204,0.2); border-radius:15px; padding:25px;
    transition: all 0.3s ease; box-shadow: 0 0 30px rgba(0,255,204,0.05);
    display:flex; flex-direction:column; }}
.event-card:hover {{ transform:translateY(-5px); border-color: rgba(0,255,204,0.6);
    box-shadow: 0 0 40px rgba(0,255,204,0.15); }}
.event-info h3 {{ font-family:'Orbitron',sans-serif; font-weight:700; font-size:1.1rem;
    color:#00ffcc; margin-bottom:8px; text-shadow: 0 0 10px rgba(0,255,204,0.2);
    display:flex; align-items:center; flex-wrap:wrap; gap:8px; }}
.today-badge {{ background:#00ffcc; color:#0a0a0a; padding:2px 10px; border-radius:12px;
    font-size:0.6rem; font-weight:bold; }}
.future-badge {{ background:#ff00cc; padding:2px 10px; border-radius:12px;
    font-size:0.6rem; font-weight:bold; color:#fff; }}
.event-info .competition {{ font-family:'Audiowide',cursive; color:#88ddff; font-size:0.85rem;
    background: rgba(0,255,204,0.1); padding:4px 12px; border-radius:20px;
    display:inline-block; margin-bottom:10px; letter-spacing:1px; }}
.event-info .datetime {{ font-family:'Grotesk',sans-serif; color:#88ddff; font-size:0.9rem; opacity:0.8; }}
.event-links {{ margin-top:15px; padding-top:15px; border-top:1px solid rgba(0,255,204,0.15); }}
.server-link {{ display:inline-block; font-family:'Orbitron',monospace; font-weight:700;
    color:#0a0a0a; background:#00ffcc; padding:12px 24px; border-radius:8px;
    text-decoration:none; transition: all 0.3s ease; font-size:0.85rem; letter-spacing:1px;
    box-shadow: 0 0 20px rgba(0,255,204,0.3); width:100%; text-align:center; }}
.server-link:hover {{ background:#00ddbb; box-shadow: 0 0 40px rgba(0,255,204,0.5); transform:scale(1.02); }}
.no-link {{ color:#ff6688; font-size:0.9rem; text-align:center; display:block; }}
.source-info {{ font-size:0.7rem; color:#88ddff; opacity:0.6; text-align:center; margin-top:5px; }}
.dropdown select {{ width:100%; padding:12px 15px; background: rgba(0,20,20,0.9);
    color:#00ffcc; border:1px solid rgba(0,255,204,0.4); border-radius:10px;
    font-family:'Orbitron',monospace; font-size:0.85rem; cursor:pointer; outline:none;
    transition: all 0.3s ease; appearance:none;
    background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2300ffcc' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
    background-repeat:no-repeat; background-position:right 15px center; background-size:15px; }}
.dropdown select option {{ background:#0a1a1a; color:#88ffdd; padding:10px; }}
.footer {{ text-align:center; padding:40px 0 20px; margin-top:60px;
    border-top:1px solid rgba(0,255,204,0.2); font-family:'Grotesk',sans-serif;
    color:#88ddff; opacity:0.7; font-size:0.9rem; }}
.footer .neon-text {{ font-family:'Orbitron',monospace; color:#00ffcc; opacity:1;
    font-size:1rem; text-shadow: 0 0 15px rgba(0,255,204,0.2); }}
@media (max-width:768px) {{
    .header h1 {{ font-size:2.2rem; }}
    .events-grid {{ grid-template-columns:1fr; }}
    .container {{ padding:15px; }}
    .event-card {{ padding:18px; }}
    .sport-header {{ flex-direction:column; gap:8px; text-align:center; }}
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
        <p class="subtitle">• TUTTI gli sport in diretta •</p>
    </header>
    <div style="text-align:center;">
        <div class="event-counter">
            🎯 <span>{len(events)}</span> eventi di oggi
        </div>
    </div>
    <div class="events-grid">
        {''.join(event_items)}
    </div>
    <footer class="footer">
        <p class="neon-text">{escape(footer)}</p>
        <p style="margin-top:8px; font-size:0.8rem;">🖥️ Aggiornato in tempo reale • Tutti gli sport disponibili</p>
    </footer>
</div>
</body>
</html>'''
    return html_content


def main():
    print("🚀 Avvio estrazione eventi da htsport.org (TUTTI GLI SPORT - SOLO OGGI)...\n")
    print(f"🕐 Fuso orario: {TZ_ROMA.tzname(None)}")
    print("📥 Recupero della pagina...")
    html = fetch_html(BASE_URL)
    if not html:
        print("❌ Impossibile recuperare la pagina")
        return

    print("\n🔍 Estrazione eventi di oggi...")
    events = parse_htsport_events(html, only_today=True)

    if not events:
        print("\n⚠️ Nessun evento trovato per oggi.")
        return

    grouped_events = group_and_sort_events(events)

    sports_count = {}
    for e in grouped_events:
        sport = e.get('sport', 'Altro')
        sports_count[sport] = sports_count.get(sport, 0) + 1

    print(f"\n📊 Riepilogo:")
    print(f"   • Eventi di oggi: {len(grouped_events)}")
    for sport, count in sorted(sports_count.items()):
        print(f"      - {sport}: {count}")
    total_links = sum(len(e.get('links', [])) for e in grouped_events)
    print(f"   • Link totali: {total_links}")

    print("\n📋 Eventi di oggi:")
    for i, event in enumerate(grouped_events):
        print(f"   {i+1}. [{event['sport']}] {event['nome_evento']} - {event['orario']}")
        channels = [l.get('channel', 'Canale') for l in event.get('links', [])]
        if channels:
            print(f"      📡 Canali: {', '.join(channels[:5])}{'...' if len(channels) > 5 else ''}")

    html_output = generate_html(
        grouped_events,
        title="CYBER GATE ACCESS - Tutti gli Sport",
        header="KIRA GATE ACCESS",
        footer="KIRA GSI SPORT • Tutti gli Sport in Diretta • 2026 • Developed by KIRA GSI GROUP"
    )

    filename = "kira_hat.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"\n✅ HTML generato con successo: {filename}")


if __name__ == "__main__":
    main()