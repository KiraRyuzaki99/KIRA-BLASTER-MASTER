#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StreamX Universal Parser - Genera HTML e Playlist M3U
"""

import json
import re
import socket
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from datetime import datetime, timedelta
from html import escape
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict

# ============================================================
#  CONFIGURAZIONE
# ============================================================

CONFIG = {
    # Domini noti che funzionano
    "known_domains": [
        "streamxhd.com",
        "streamx061.sbs",
        "streamx062.sbs",
        "streamx063.sbs",
        "streamx064.sbs",
        "streamx065.sbs",
        "streamxhd.sbs",
    ],
    
    # Pattern per generare nuovi domini
    "domain_patterns": [
        "streamx{}.sbs",
        "streamx{}.com",
        "streamx{}.live",
        "streamx{}.tv",
        "stream{}.sbs",
        "sportstream{}.sbs",
        "streamxhd{}.sbs",
    ],
    
    # Suffissi/numeri da provare
    "domain_suffixes": [
        "", "hd", "061", "062", "063", "064", "065", 
        "hd1", "hd2", "hd3", "live", "pro", "plus",
        "01", "02", "03", "04", "05"
    ],
    
    # Endpoint da testare (in ordine di priorità)
    "endpoints": [
        "/json/agenda550.json",
        "/eventos.json",
        "/api/eventos.json",
        "/streams.json",
        "/json/events.json",
        "/data/events.json",
        "/api/agenda.json",
        "/events.json",
    ],
    
    # Timeout per le richieste (secondi)
    "timeout": 5,
    
    # Numero massimo di domini da testare
    "max_domains_to_test": 50,
    
    # Info playlist
    "playlist_info": {
        "name": "StreamX Live Sports",
        "author": "StreamX Parser",
        "description": "Playlist eventi sportivi in diretta da StreamX"
    }
}

# ============================================================
#  FUNZIONI DI RETE
# ============================================================

def fetch_content(url: str, timeout: int = 15) -> Optional[str]:
    """Recupera il contenuto di un URL."""
    try:
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html'
        })
        with urlopen(req, timeout=timeout) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def fetch_json(url: str, timeout: int = 15) -> Optional[dict]:
    """Recupera e parsifica JSON da un URL."""
    content = fetch_content(url, timeout)
    if not content:
        return None
    try:
        return json.loads(content)
    except:
        return None

def check_domain_endpoint(domain: str, endpoint: str, timeout: int = 5) -> Tuple[bool, Optional[str], Optional[dict]]:
    """Verifica se un dominio risponde con l'endpoint JSON."""
    url = f"https://{domain}{endpoint}"
    
    try:
        socket.gethostbyname(domain)
        json_data = fetch_json(url, timeout)
        if json_data is not None:
            return True, url, json_data
    except (socket.gaierror, URLError, HTTPError, TimeoutError, Exception):
        pass
    
    return False, None, None

def find_endpoint_from_html(domain: str) -> Optional[str]:
    """Scarica l'HTML della pagina e cerca l'endpoint JSON nel codice."""
    try:
        url = f"https://{domain}"
        html = fetch_content(url, timeout=10)
        if not html:
            return None
        
        patterns = [
            r'fetch\(["\']([^"\']+\.json)["\']',
            r'loadEvents.*?fetch\(["\']([^"\']+)["\']',
            r'src=["\']([^"\']+\.json)["\']',
            r'url\s*[:=]\s*["\']([^"\']+\.json)["\']',
            r'endpoint\s*[:=]\s*["\']([^"\']+\.json)["\']',
            r'["\'](/json/[^"\']+\.json)["\']',
            r'["\'](/api/[^"\']+\.json)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if match.startswith('/'):
                    return match
                elif match.startswith('http'):
                    match = match.replace(f"https://{domain}", "").replace(f"http://{domain}", "")
                    return match
    except:
        pass
    
    return None

# ============================================================
#  RICERCA DOMINI
# ============================================================

def generate_domains() -> List[str]:
    """Genera una lista di possibili domini basati sui pattern configurati."""
    domains = []
    
    domains.extend(CONFIG["known_domains"])
    
    for pattern in CONFIG["domain_patterns"]:
        for suffix in CONFIG["domain_suffixes"]:
            domain = pattern.format(suffix)
            if domain not in domains:
                domains.append(domain)
    
    base_domains = ["streamx", "stream", "sportstream", "livex"]
    tlds = [".sbs", ".com", ".live", ".tv", ".me", ".cc"]
    
    for base in base_domains:
        for tld in tlds:
            domain = f"{base}{tld}"
            if domain not in domains:
                domains.append(domain)
            for num in ["1", "2", "3", "4", "5", "hd"]:
                domain = f"{base}{num}{tld}"
                if domain not in domains:
                    domains.append(domain)
    
    return domains

def find_active_domain() -> Tuple[Optional[str], Optional[str], Optional[dict]]:
    """Cerca automaticamente un dominio attivo tra quelli possibili."""
    print("🔍 Ricerca dominio StreamX attivo...")
    
    domains = generate_domains()
    total = min(len(domains), CONFIG["max_domains_to_test"])
    print(f"   Testo {total} domini...")
    
    for i, domain in enumerate(domains[:total], 1):
        for endpoint in CONFIG["endpoints"]:
            success, url, json_data = check_domain_endpoint(domain, endpoint, CONFIG["timeout"])
            if success:
                print(f"   ✅ Dominio trovato: {domain}")
                print(f"   📡 Endpoint: {endpoint}")
                return domain, endpoint, json_data
        
        endpoint = find_endpoint_from_html(domain)
        if endpoint:
            success, url, json_data = check_domain_endpoint(domain, endpoint, CONFIG["timeout"])
            if success:
                print(f"   ✅ Dominio trovato: {domain} (da HTML)")
                print(f"   📡 Endpoint: {endpoint}")
                return domain, endpoint, json_data
        
        if i % 10 == 0:
            print(f"   ... testati {i} domini")
    
    print("   ❌ Nessun dominio attivo trovato")
    return None, None, None

# ============================================================
#  PARSER EVENTI
# ============================================================

def parse_single_event_agenda(event: dict, source_name: str) -> Optional[dict]:
    """Parsing per il formato agenda550.json."""
    if not event:
        return None
    
    title = event.get('title', '')
    if not title:
        return None
    
    date_str = event.get('date', '')
    time_str = event.get('time', '00:00')
    
    try:
        if date_str and time_str:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            dt = dt + timedelta(hours=7)
        else:
            dt = datetime.now()
    except:
        dt = datetime.now()
    
    link = event.get('link', '')
    if not link or not link.startswith('http'):
        for key in ['url', 'stream', 'iframe']:
            if key in event and event[key] and str(event[key]).startswith('http'):
                link = event[key]
                break
    
    competition = event.get('category', 'Sconosciuta')
    
    # Pulisci il nome della competizione
    competition = re.sub(r'\s*\[.*?\]\s*$', '', competition)
    competition = competition.strip()
    
    language = event.get('language', '')
    if language:
        if isinstance(language, list):
            language = ', '.join(language)
    
    now = datetime.now()
    status = 'prossimo'
    if dt < now:
        status = 'in corso' if (now - dt).seconds < 7200 else 'terminato'
    
    return {
        'nome_evento': title,
        'competizione': competition,
        'orario': dt.strftime('%H:%M'),
        'giorno': dt.strftime('%A, %d %B %Y'),
        'data_ordine': dt.strftime('%Y-%m-%d %H:%M'),
        'datetime': dt,
        'links': [link] if link and link.startswith('http') else ['#'],
        'fonte': source_name,
        'status': status,
        'language': language
    }

def parse_single_event(event: dict, source_name: str) -> Optional[dict]:
    """Parsing per il formato eventos.json (originale)."""
    if not event:
        return None
    
    title = event.get('title') or event.get('name') or ''
    if not title:
        home = event.get('homeTeam', '')
        away = event.get('awayTeam', '')
        if home and away:
            title = f"{home} VS {away}"
        else:
            return None
    
    competition = event.get('league_name') or event.get('competition') or event.get('league') or 'Sconosciuta'
    competition = competition.strip()
    
    raw_time = str(event.get('time') or event.get('datetime') or event.get('date') or '00:00')
    hour, minute = 0, 0
    
    time_match = re.search(r'(\d{2}):(\d{2})', raw_time)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
    elif 'T' in raw_time:
        parts = raw_time.split('T')
        if len(parts) > 1:
            t_parts = parts[1].split(':')
            if len(t_parts) >= 2:
                hour = int(t_parts[0])
                minute = int(t_parts[1])

    dt = datetime.now()
    date_str = event.get('date') or event.get('datetime') or ''
    if date_str and len(str(date_str)) >= 10:
        try:
            dt = datetime.strptime(str(date_str)[:10], '%Y-%m-%d')
        except:
            pass
        
    event_dt = dt.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(hours=7)
    
    links = []
    servers = event.get('servers', [])
    if isinstance(servers, list):
        for server in servers:
            url = server.get('url', '')
            if url and url.startswith('http'):
                links.append(url)
    
    if not links:
        for key in ['url', 'stream', 'link', 'iframe']:
            if key in event and event[key] and str(event[key]).startswith('http'):
                links.append(event[key])
    
    links = list(dict.fromkeys(links))
    
    now = datetime.now()
    status = 'prossimo'
    if event_dt < now:
        status = 'in corso' if (now - event_dt).seconds < 7200 else 'terminato'
    
    return {
        'nome_evento': title,
        'competizione': competition,
        'orario': event_dt.strftime('%H:%M'),
        'giorno': event_dt.strftime('%A, %d %B %Y'),
        'data_ordine': event_dt.strftime('%Y-%m-%d %H:%M'),
        'datetime': event_dt,
        'links': links if links else ['#'],
        'fonte': source_name,
        'status': status,
        'language': ''
    }

def parse_streamx_events(json_data: Any, source_name: str) -> List[dict]:
    """Estrae eventi dal formato JSON di StreamX (sia agenda550 che eventos)."""
    events = []
    if not json_data:
        return events
    
    if isinstance(json_data, list):
        for event in json_data:
            parsed = parse_single_event_agenda(event, source_name)
            if parsed:
                events.append(parsed)
    elif isinstance(json_data, dict):
        if 'sports' in json_data:
            for sport in json_data['sports']:
                for league in sport.get('leagues', []):
                    l_name = league.get('name', 'Sconosciuta')
                    for event in league.get('events', []):
                        event['league_name'] = l_name
                        parsed = parse_single_event(event, source_name)
                        if parsed:
                            events.append(parsed)
        elif 'events' in json_data:
            for event in json_data['events']:
                parsed = parse_single_event(event, source_name)
                if parsed:
                    events.append(parsed)
        else:
            parsed = parse_single_event(json_data, source_name)
            if parsed:
                events.append(parsed)
    
    return events

# ============================================================
#  GENERAZIONE M3U (VERSIONE CORRETTA)
# ============================================================

def generate_m3u(events: List[dict]) -> str:
    """
    Versione DEFINITIVA per WisePlay.
    Tutte le info nel titolo dell'evento.
    """
    if not events:
        return "#EXTM3U\n"
    
    # Filtra eventi con link validi
    valid_events = [e for e in events if e.get('links') and e['links'][0] != '#']
    
    if not valid_events:
        return "#EXTM3U\n"
    
    # Raggruppa per competizione
    by_comp = defaultdict(list)
    for event in valid_events:
        comp = event['competizione']
        by_comp[comp].append(event)
    
    # Ordina le competizioni alfabeticamente
    sorted_comps = sorted(by_comp.keys())
    
    # Mappatura icone stato (testo invece di emoji per WisePlay)
    status_text = {
        'in corso': '🔴LIVE',
        'prossimo': '⏳NEXT',
        'terminato': '✅END'
    }
    
    m3u_lines = ['#EXTM3U']
    
    for comp in sorted_comps:
        comp_events = by_comp[comp]
        
        # Ordina gli eventi per orario
        comp_events.sort(key=lambda x: x['datetime'])
        
        # GRUPPO
        m3u_lines.append(f'#EXTGRP:{comp}')
        
        for event in comp_events:
            link = event['links'][0] if event['links'] else '#'
            
            if link == '#':
                continue
            
            # Formatta data e ora
            day_short = event['datetime'].strftime('%d/%m')
            time = event['orario']
            name = event['nome_evento']
            status = event.get('status', 'prossimo')
            status_icon = status_text.get(status, '⏳NEXT')
            
            # TUTTO nel titolo: [STATO] DATA ORA - NOME
            title = f"{status_icon} {day_short} {time} - {name}"
            
            # Aggiungi group-title per WisePlay
            m3u_lines.append(f'#EXTINF:-1 group-title="{comp}",{title}')
            m3u_lines.append(link)
    
    return '\n'.join(m3u_lines)

def group_and_sort_events(events: List[dict]) -> List[dict]:
    """
    Raggruppa e ordina gli eventi per l'HTML.
    FILTRA: mantiene solo eventi di oggi e domani.
    """
    # Filtra eventi: mantieni solo quelli di oggi e domani
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = tomorrow + timedelta(days=1)
    
    filtered_events = []
    for event in events:
        event_date = event.get('datetime')
        if event_date:
            # Mantieni solo eventi di oggi e domani
            if today <= event_date < day_after_tomorrow:
                filtered_events.append(event)
        else:
            # Se non ha data, lo mantieni (fallback)
            filtered_events.append(event)
    
    # Raggruppa gli eventi filtrati
    grouped = {}
    for event in filtered_events:
        key = f"{event['nome_evento']}_{event['giorno']}"
        if key not in grouped:
            grouped[key] = {
                'nome_evento': event['nome_evento'],
                'competizione': event['competizione'],
                'orario': event['orario'],
                'giorno': event['giorno'],
                'data_ordine': event.get('data_ordine', ''),
                'datetime': event.get('datetime', datetime.now()),
                'links': [],
                'fonte': event.get('fonte', 'Sconosciuta'),
                'status': event.get('status', 'prossimo'),
                'language': event.get('language', '')
            }
        for link in event['links']:
            if link not in grouped[key]['links'] and link != '#':
                grouped[key]['links'].append(link)
        if not grouped[key]['links']:
            grouped[key]['links'] = ['#']
            
    result = list(grouped.values())
    result.sort(key=lambda x: x.get('data_ordine', '9999-99-99 99:99'))
    return result

# ============================================================
#  GENERAZIONE HTML
# ============================================================

def generate_html(events: List[dict], title: str = "Eventi Sportivi in Diretta", 
                  header: str = "StreamX Eventi", footer: str = "© 2026 StreamX - Tutti i diritti riservati") -> str:
    """Genera l'HTML con gli eventi."""
    event_items = []
    for event in events:
        links_html = ""
        valid_links = [link for link in event['links'] if link != '#']
        
        status_badge = {
            'in corso': '<span class="status-live">🔴 LIVE</span>',
            'prossimo': '<span class="status-next">⏳ PROSSIMO</span>',
            'terminato': '<span class="status-finished">✅ TERMINATO</span>'
        }.get(event.get('status', 'prossimo'), '')
        
        fonte_badge = f'<span class="fonte-badge">📡 {event.get("fonte", "StreamX")}</span>'
        
        if len(valid_links) > 1:
            options = "\n".join([f'<option value="{link}">{link.split("/")[-1]}</option>' for link in valid_links])
            links_html = f'''
            <div class="dropdown">
                <select onchange="window.open(this.value, '_blank'); this.selectedIndex=0;">
                    <option value="">📡 Scegli il server...</option>
                    {options}
                </select>
            </div>
            '''
        elif len(valid_links) == 1:
            link = valid_links[0]
            links_html = f'<a href="{link}" target="_blank" class="server-link">▶ GUARDA IN DIRETTA</a>'
        else:
            links_html = '<span class="no-link">🔗 Link non disponibile</span>'

        # Aggiungi lingua se disponibile
        language_info = f'<span class="language-badge">🌐 {event.get("language", "")}</span>' if event.get('language') else ''

        event_items.append(f'''
        <div class="event-card">
            <div class="event-info">
                <h3>{escape(event['nome_evento'])} {status_badge}</h3>
                <p class="competition">🏆 {escape(event['competizione'])}</p>
                <p class="datetime">🕒 {escape(event['orario'])} • 📅 {escape(event['giorno'])}</p>
                {fonte_badge}
                {language_info}
            </div>
            <div class="event-links">
                {links_html}
            </div>
        </div>
        ''')

    return f'''
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
            .language-badge {{
                display: inline-block; font-size: 0.75rem; background: rgba(0, 255, 204, 0.1);
                color: #88ffdd; padding: 2px 12px; border-radius: 12px; margin-top: 5px; margin-left: 5px;
                border: 1px solid rgba(0, 255, 204, 0.15);
            }}
            .status-live {{
                display: inline-block; font-size: 0.7rem; background: rgba(255, 0, 0, 0.3);
                color: #ff4444; padding: 2px 10px; border-radius: 12px; margin-left: 8px;
                animation: pulse 1.5s ease-in-out infinite;
            }}
            .status-next {{
                display: inline-block; font-size: 0.7rem; background: rgba(0, 100, 255, 0.3);
                color: #4488ff; padding: 2px 10px; border-radius: 12px; margin-left: 8px;
            }}
            .status-finished {{
                display: inline-block; font-size: 0.7rem; background: rgba(100, 100, 100, 0.3);
                color: #888888; padding: 2px 10px; border-radius: 12px; margin-left: 8px;
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
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
            .no-link {{
                display: inline-block; font-family: 'Orbitron', monospace; color: #666;
                text-align: center; width: 100%; padding: 10px;
            }}
            .footer {{ text-align: center; padding: 40px 0 20px; margin-top: 60px; border-top: 1px solid rgba(0, 255, 204, 0.2); color: #88ddff; opacity: 0.7; }}
            .footer .neon-text {{ font-family: 'Orbitron', monospace; color: #00ffcc; font-size: 1rem; }}
        </style>
    </head>
    <body>
        <div class="matrix-bg"></div>
        <div class="container">
            <header class="header">
                <h1>{escape(header)}</h1>
                <p class="subtitle">• Embedded Live Sports •</p>
            </header>
            <div style="text-align: center;">
                <div class="event-counter">
                    🎯 <span>{len(events)}</span> eventi disponibili
                </div>
            </div>
            <div class="events-grid">
                {''.join(event_items)}
            </div>
            <footer class="footer">
                <p class="neon-text">{escape(footer)}</p>
            </footer>
        </div>
    </body>
    </html>
    '''

# ============================================================
#  MAIN
# ============================================================

def main():
    """Funzione principale."""
    print("="*60)
    print("🚀 STREAMX UNIVERSAL PARSER - HTML + M3U")
    print("="*60)
    print()
    
    all_events = []
    sources_found = []
    
    # 1. TENTA I DOMINI NOTI (veloce)
    print("📡 FASE 1: Domini noti")
    print("-"*40)
    
    for domain in CONFIG["known_domains"]:
        print(f"   Testo: {domain}")
        
        for endpoint in CONFIG["endpoints"][:3]:
            success, url, json_data = check_domain_endpoint(domain, endpoint, CONFIG["timeout"])
            if success and json_data:
                events = parse_streamx_events(json_data, source_name=f"{domain}")
                if events:
                    all_events.extend(events)
                    sources_found.append(domain)
                    print(f"   ✅ Trovati {len(events)} eventi da {domain} ({endpoint})")
                    break
        time.sleep(0.2)
    
    # 2. SE NON TROVATO, RICERCA ESTESA
    if not sources_found:
        print("\n📡 FASE 2: Ricerca estesa")
        print("-"*40)
        
        domain, endpoint, json_data = find_active_domain()
        if domain and json_data:
            events = parse_streamx_events(json_data, source_name=f"{domain}")
            if events:
                all_events.extend(events)
                sources_found.append(domain)
                print(f"   ✅ Trovati {len(events)} eventi da {domain} ({endpoint})")
    
    # 3. SE ANCORA NIENTE, RICERCA HTML
    if not sources_found:
        print("\n📡 FASE 3: Ricerca HTML")
        print("-"*40)
        
        for domain in generate_domains()[:30]:
            try:
                socket.gethostbyname(domain)
                endpoint = find_endpoint_from_html(domain)
                if endpoint:
                    success, url, json_data = check_domain_endpoint(domain, endpoint, CONFIG["timeout"])
                    if success and json_data:
                        events = parse_streamx_events(json_data, source_name=f"{domain}")
                        if events:
                            all_events.extend(events)
                            sources_found.append(domain)
                            print(f"   ✅ Trovati {len(events)} eventi da {domain} (da HTML)")
                            break
            except:
                continue
    
    # 4. CERCA ALTRI DOMINI PER AGGIUNGERE EVENTI
    if sources_found:
        print("\n📡 FASE 4: Ricerca domini aggiuntivi")
        print("-"*40)
        
        domains_tested = set()
        for domain in generate_domains()[:30]:
            if domain in domains_tested or domain in sources_found:
                continue
            domains_tested.add(domain)
            
            try:
                socket.gethostbyname(domain)
                for endpoint in CONFIG["endpoints"][:2]:
                    success, url, json_data = check_domain_endpoint(domain, endpoint, CONFIG["timeout"])
                    if success and json_data:
                        events = parse_streamx_events(json_data, source_name=f"{domain}")
                        if events:
                            new_events = [e for e in events if e['nome_evento'] not in 
                                        [ex['nome_evento'] for ex in all_events]]
                            if new_events:
                                all_events.extend(new_events)
                                print(f"   ✅ Trovati {len(new_events)} nuovi eventi da {domain}")
                            break
            except:
                continue
    
    # RIEPILOGO
    print("\n" + "="*60)
    print("📊 RIEPILOGO")
    print("="*60)
    
    if not all_events:
        print("⚠️ Nessun evento trovato da nessuna fonte.")
        return
    
    print(f"   Fonti trovate: {len(sources_found)}")
    print(f"   Eventi totali: {len(all_events)}")
    
    grouped_events = group_and_sort_events(all_events)
    print(f"   Eventi unici:  {len(grouped_events)}")
    
    # GENERA HTML
    print("\n📄 Generazione HTML...")
    html_output = generate_html(
        grouped_events,
        title="CYBER GATE ACCESS",
        header="KIRA GATE ACCESS",
        footer="KIRA GSI SPORT • Eventi in Diretta • 2026 • Developed by KIRA GSI GROUP"
    )
    
    html_filename = "streamx_events.html"
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"   ✅ HTML generato: {html_filename}")
    
    # GENERA M3U
    print("\n📄 Generazione Playlist M3U...")
    m3u_content = generate_m3u(all_events)
    
    m3u_filename = "streamx_playlist.m3u"
    with open(m3u_filename, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"   ✅ Playlist M3U generata: {m3u_filename}")
    
    # SALVA CONFIGURAZIONE
    if sources_found:
        config_data = {
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "active_domains": sources_found,
            "total_events": len(grouped_events),
            "files": {
                "html": html_filename,
                "m3u": m3u_filename
            }
        }
        with open("streamx_sources.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Configurazione salvata: streamx_sources.json")
    
    print("\n" + "="*60)
    print("✅ OPERAZIONE COMPLETATA!")
    print("="*60)
    print()
    print(f"📁 File generati:")
    print(f"   • {html_filename} - Visualizza gli eventi nel browser")
    print(f"   • {m3u_filename} - Playlist per VLC/WisePlay")
    print(f"   • streamx_sources.json - Configurazione trovata")
    print()

if __name__ == "__main__":
    main()