#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DADDYLIVE AUTO - Sistema di apprendimento automatico per le parole chiave
"""

import requests
import json
import os
import re
from datetime import datetime
from collections import defaultdict, Counter
from html import escape

# ============================================================
#  CONFIGURAZIONE
# ============================================================

ENDPOINT_BASE = "https://daddylive.li/player/"
OUTPUT_DIR = "daddy_output"
KEYWORDS_FILE = "daddy_keywords.json"  #  File di memoria

# Parole chiave di BASE (solo per avviare il sistema)
BASE_KEYWORDS = {
    "Calcio": ["soccer", "football", "serie a", "premier league", "bundesliga", "la liga", "ligue 1", "calcio", "champions league", "europa league"],
    "Tennis": ["tennis", "atp", "wta", "us open", "wimbledon", "roland garros", "australian open"],
    "Basket": ["basketball", "nba", "euroleague", "basket", "baloncesto", "liga acb"],
    "Hockey": ["hockey", "nhl", "liiga", "shl", "extraliga"],
    "Motori": ["formula", "motogp", "superbike", "rally", "f1", "nascar", "indycar"],
    "Baseball": ["baseball", "mlb", "kbo", "npb"],
    "Rugby": ["rugby", "super league", "nrl", "six nations"],
    "Voleibol": ["volleyball", "voley", "volley"],
    "Balonmano": ["handball", "balonmano"],
    "Pugilato": ["boxing", "ufc", "mma", "pugilato"],
    "Golf": ["golf", "pga"],
    "Ciclismo": ["cycling", "ciclismo", "tour de france"],
    "Altri": []
}

EXCLUDE_WORDS = [
    "advertisement", "sponsor", "promo", "bonus",
    "casino", "betting", "slot", "live chat",
    "no event", "coming soon", "off air",
    "banner", "ad", "partners", "affiliate"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': 'https://daddylive.eu/',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7'
}

# ============================================================
#  FUNZIONI PER LA GESTIONE DELLE PAROLE CHIAVE
# ============================================================

def load_keywords():
    """Carica il dizionario delle parole chiave dal file."""
    if os.path.exists(KEYWORDS_FILE):
        try:
            with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f" Caricate {len(data.get('keywords', {}))} parole chiave dal file")
                return data
        except:
            pass
    
    # Se il file non esiste, usa le parole base
    print(" Nessun file di parole chiave trovato. Uso parole base.")
    return {
        "keywords": BASE_KEYWORDS,
        "last_update": None,
        "history": []
    }

def save_keywords(keywords_data):
    """Salva il dizionario delle parole chiave nel file."""
    keywords_data["last_update"] = datetime.now().isoformat()
    with open(KEYWORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(keywords_data, f, indent=2, ensure_ascii=False)
    print(f" Parole chiave salvate ({sum(len(v) for v in keywords_data['keywords'].values())} totali)")

def extract_new_keywords(categories, current_keywords):
    """Estrae nuove parole chiave dalle categorie."""
    # Costruisci un set di tutte le parole già note
    known_words = set()
    for words in current_keywords.values():
        for w in words:
            known_words.add(w.lower())
    
    # Estrai tutte le parole dalle categorie
    all_words = set()
    for cat in categories:
        if not cat:
            continue
        # Pulisci e dividi
        clean = re.sub(r'[^\w\s]', ' ', cat.lower())
        words = set(clean.split())
        for w in words:
            if len(w) > 2 and w not in EXCLUDE_WORDS:
                all_words.add(w)
    
    # Trova le parole già associate a uno sport
    new_words = {}
    
    # Per ogni parola nuova, cerca di associarla a uno sport
    for word in all_words:
        if word in known_words:
            continue
        
        # Cerca lo sport più probabile
        best_sport = None
        best_score = 0
        
        for sport, known_list in current_keywords.items():
            for known in known_list:
                # Controlla se la parola è contenuta in una parola nota o viceversa
                if word in known or known in word:
                    score = 1 + (len(known) / 100)  # Leggero bonus per parole più lunghe
                    if score > best_score:
                        best_score = score
                        best_sport = sport
        
        if best_sport and best_score > 0.5:
            if best_sport not in new_words:
                new_words[best_sport] = []
            new_words[best_sport].append(word)
    
    return new_words

def update_keywords(keywords_data, new_words):
    """Aggiorna il dizionario con le nuove parole."""
    updated = False
    
    for sport, words in new_words.items():
        if sport not in keywords_data["keywords"]:
            keywords_data["keywords"][sport] = []
        
        for w in words:
            if w not in keywords_data["keywords"][sport]:
                keywords_data["keywords"][sport].append(w)
                updated = True
    
    if updated:
        # Registra l'aggiornamento nella storia
        keywords_data["history"].append({
            "date": datetime.now().isoformat(),
            "new_words": new_words
        })
        # Mantieni solo gli ultimi 10 aggiornamenti
        if len(keywords_data["history"]) > 10:
            keywords_data["history"] = keywords_data["history"][-10:]
    
    return updated

# ============================================================
#  FUNZIONI PRINCIPALI
# ============================================================

def fetch_json(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def extract_all_categories():
    """Estrae TUTTE le categorie da tutti i file JSON."""
    all_categories = set()
    all_events_data = []
    
    print(" Scansione macro cartelle per estrarre categorie...")
    
    for i in range(1, 10):
        filename = f"tv{i}.json"
        url = ENDPOINT_BASE + filename
        print(f"    {filename}...", end=" ")
        
        data = fetch_json(url)
        if not data:
            print("")
            continue
        
        print("")
        
        for data_corrente, contenuto in data.items():
            if isinstance(contenuto, list):
                items = [("Eventi", contenuto)]
            elif isinstance(contenuto, dict):
                items = contenuto.items()
            else:
                continue
            
            for categoria_o_chiave, eventi in items:
                blocks = eventi if isinstance(eventi, list) else ([eventi] if isinstance(eventi, dict) else [])
                
                for block in blocks:
                    if not isinstance(block, dict):
                        continue
                    
                    categoria = block.get('Category', block.get('category', categoria_o_chiave))
                    if not isinstance(categoria, str) or not categoria.strip():
                        continue
                    
                    all_categories.add(categoria.strip())
                    
                    lista_eventi = block.get('events', [])
                    if isinstance(lista_eventi, list):
                        for evento in lista_eventi:
                            if isinstance(evento, dict):
                                evento['_categoria'] = categoria.strip()
                                all_events_data.append(evento)
    
    print(f"\n    Trovate {len(all_categories)} categorie uniche")
    return list(all_categories), all_events_data

def detect_sport(category, keywords_data):
    """Rileva lo sport usando il dizionario aggiornato."""
    if not category:
        return "Altri"
    
    cat_lower = category.lower()
    
    # Escludi categorie indesiderate
    for word in EXCLUDE_WORDS:
        if word in cat_lower:
            return "Escluso"
    
    # Cerca nello sport "Altri" prima
    for word in keywords_data.get("Altri", []):
        if word in cat_lower:
            return "Altri"
    
    # Cerca in tutti gli sport
    best_sport = "Altri"
    best_score = 0
    
    for sport, keywords in keywords_data.items():
        if sport == "Altri":
            continue
        
        score = 0
        for kw in keywords:
            if kw in cat_lower:
                score += 1
            # Controlla anche se le parole sono simili
            if len(kw) > 3:
                words = set(re.findall(r'[a-zA-ZÀ-ÿ]+', cat_lower))
                for w in words:
                    if kw in w or w in kw:
                        score += 0.3
        
        if score > best_score:
            best_score = score
            best_sport = sport
    
    # Se il punteggio è troppo basso, verifica se qualche parola chiave è contenuta
    if best_score < 1:
        for sport, keywords in keywords_data.items():
            if sport == "Altri":
                continue
            for kw in keywords:
                if len(kw) > 3 and kw in cat_lower:
                    return sport
    
    return best_sport

def fetch_all_matches(keywords_data):
    """Scarica tutti gli eventi usando il dizionario."""
    all_events = []
    
    print("\n Scaricamento eventi...")
    
    for i in range(1, 10):
        filename = f"tv{i}.json"
        url = ENDPOINT_BASE + filename
        print(f"    {filename}...", end=" ")
        
        data = fetch_json(url)
        if not data:
            print("")
            continue
        
        print("")
        
        for data_corrente, contenuto in data.items():
            if isinstance(contenuto, list):
                items = [("Eventi", contenuto)]
            elif isinstance(contenuto, dict):
                items = contenuto.items()
            else:
                continue
            
            for categoria_o_chiave, eventi in items:
                blocks = eventi if isinstance(eventi, list) else ([eventi] if isinstance(eventi, dict) else [])
                
                for block in blocks:
                    if not isinstance(block, dict):
                        continue
                    
                    categoria = block.get('Category', block.get('category', categoria_o_chiave))
                    if not isinstance(categoria, str) or not categoria.strip():
                        continue
                    
                    sport = detect_sport(categoria, keywords_data["keywords"])
                    if sport == "Escluso":
                        continue
                    
                    lista_eventi = block.get('events', [])
                    if not isinstance(lista_eventi, list):
                        continue
                    
                    for evento in lista_eventi:
                        if not isinstance(evento, dict):
                            continue
                        
                        titolo = evento.get('event', 'Evento')
                        orario = evento.get('time', 'N/A')
                        canali = evento.get('channels', [])
                        
                        links = []
                        for channel in canali:
                            if not isinstance(channel, dict):
                                continue
                            
                            channel_id = channel.get('channel_id')
                            if channel_id:
                                links.append(f"https://daddylive.eu/embed/embed.php?id={channel_id}")
                            
                            for k, v in channel.items():
                                if k.startswith('embed_') and v:
                                    links.append(v)
                        
                        if not links:
                            continue
                        
                        all_events.append({
                            'title': titolo,
                            'time': orario,
                            'date': data_corrente,
                            'category': categoria,
                            'sport': sport,
                            'links': links,
                            'source': filename
                        })
    
    print(f"\n    Trovati {len(all_events)} eventi totali")
    return all_events

def group_and_generate(events):
    """Raggruppa e genera HTML per ogni sport."""
    grouped = defaultdict(list)
    for event in events:
        grouped[event['sport']].append(event)
    
    print("\n Statistiche per sport:")
    for sport, evs in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"    {sport}: {len(evs)} eventi")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    total_events = 0
    for sport, evs in grouped.items():
        evs.sort(key=lambda x: f"{x['date']}_{x['time']}")
        filename = f"KIRA_GSI_{sport}.html".replace(" ", "_")
        filepath = os.path.join(OUTPUT_DIR, filename)
        count = generate_html_for_sport(sport, evs, filepath)
        total_events += count
        print(f"    {filename} ({count} eventi)")
    
    # Tutti
    all_events = []
    for evs in grouped.values():
        all_events.extend(evs)
    generate_html_for_sport("Tutti", all_events, os.path.join(OUTPUT_DIR, "KIRA_GSI_Tutti.html"))
    print(f"    KIRA_GSI_Tutti.html ({len(all_events)} eventi)")
    
    return total_events

def generate_html_for_sport(sport, events, output_file):
    """Genera HTML con stile KIRA GSI."""
    event_items = ""
    for event in events:
        valid_links = event['links'][:5]
        
        if len(valid_links) > 1:
            options = "\n".join([f'<option value="{l}">Canale {i+1}</option>' for i, l in enumerate(valid_links)])
            links_html = f'''
            <div class="dropdown">
                <select onchange="window.open(this.value, '_blank'); this.selectedIndex=0;">
                    <option value=""> Scegli il canale...</option>
                    {options}
                </select>
            </div>
            '''
        elif len(valid_links) == 1:
            links_html = f'<a href="{valid_links[0]}" target="_blank" class="server-link"> GUARDA IN DIRETTA</a>'
        else:
            links_html = '<span class="no-link"> Link non disponibile</span>'
        
        event_items += f'''
        <div class="event-card">
            <div class="event-info">
                <h3>{escape(event['title'])}</h3>
                <p class="competition"> {escape(event['category'])}</p>
                <p class="datetime"> {escape(event['time'])} •  {escape(event['date'])}</p>
                <span class="fonte-badge"> {escape(event['sport'])}</span>
            </div>
            <div class="event-links">
                {links_html}
            </div>
        </div>
        '''
    
    if not event_items:
        event_items = '<p style="text-align:center;color:#666;">Nessun evento trovato.</p>'
    
    html = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KIRA GSI - {sport}</title>
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
        .header .subtitle {{
            font-family: 'Audiowide', cursive;
            color: #88ffdd;
            font-size: 1.2rem;
            margin-top: 10px;
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
        }}
        .event-counter span {{ font-weight: 900; font-size: 1.5rem; }}
        
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
            font-size: 1.2rem;
            color: #00ffcc;
            margin-bottom: 8px;
        }}
        .event-info .competition {{
            font-family: 'Audiowide', cursive;
            color: #88ddff;
            font-size: 0.85rem;
            background: rgba(0, 255, 204, 0.1);
            padding: 4px 12px;
            border-radius: 20px;
            display: inline-block;
            margin-bottom: 10px;
        }}
        .event-info .datetime {{
            color: #88ddff;
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        .fonte-badge {{
            display: inline-block;
            font-size: 0.7rem;
            background: rgba(0, 255, 204, 0.15);
            color: #88ffdd;
            padding: 2px 12px;
            border-radius: 12px;
            margin-top: 5px;
            border: 1px solid rgba(0, 255, 204, 0.2);
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
            text-align: center;
            width: 100%;
            transition: all 0.3s ease;
            font-size: 0.85rem;
        }}
        .server-link:hover {{
            background: #00ddbb;
            box-shadow: 0 0 40px rgba(0, 255, 204, 0.5);
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
        }}
        .no-link {{
            display: inline-block;
            font-family: 'Orbitron', monospace;
            color: #666;
            text-align: center;
            width: 100%;
            padding: 10px;
        }}
        
        .footer {{
            text-align: center;
            padding: 40px 0 20px;
            margin-top: 60px;
            border-top: 1px solid rgba(0, 255, 204, 0.2);
            color: #88ddff;
            opacity: 0.7;
        }}
        .footer .neon-text {{
            font-family: 'Orbitron', monospace;
            color: #00ffcc;
            font-size: 1rem;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 2rem; }}
            .events-grid {{ grid-template-columns: 1fr; }}
            .container {{ padding: 15px; }}
        }}
    </style>
</head>
<body>
    <div class="matrix-bg"></div>
    <div class="container">
        <header class="header">
            <h1> KIRA GSI </h1>
            <p class="subtitle">• {sport} - Eventi in Diretta •</p>
        </header>
        
        <div style="text-align: center;">
            <div class="event-counter">
                 <span>{len(events)}</span> eventi disponibili
            </div>
        </div>
        
        <div class="events-grid">
            {event_items}
        </div>
        
        <footer class="footer">
            <p class="neon-text"> KIRA GSI • Eventi in diretta • {datetime.now().year}</p>
        </footer>
    </div>
</body>
</html>'''
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    return len(events)

# ============================================================
#  MAIN
# ============================================================

def main():
    print("="*70)
    print(" KIRA GSI - DaddyLive Auto (Con apprendimento)")
    print("="*70)
    
    # FASE 1: Carica le parole chiave esistenti
    keywords_data = load_keywords()
    
    # FASE 2: Estrai tutte le categorie
    categories, all_events_data = extract_all_categories()
    
    if not categories:
        print(" Nessuna categoria trovata!")
        return
    
    # FASE 3: Estrai nuove parole chiave
    print("\n Analisi di nuove parole chiave...")
    new_words = extract_new_keywords(categories, keywords_data["keywords"])
    
    if new_words:
        print("   Nuove parole trovate:")
        for sport, words in new_words.items():
            print(f"      {sport}: {', '.join(words[:5])}")
            if len(words) > 5:
                print(f"         ... e altre {len(words)-5} parole")
    else:
        print("    Nessuna nuova parola trovata")
    
    # FASE 4: Aggiorna il dizionario se necessario
    updated = update_keywords(keywords_data, new_words)
    if updated:
        save_keywords(keywords_data)
        print("\n Dizionario aggiornato!")
    
    # Mostra il dizionario attuale
    print(f"\n Dizionario attuale ({sum(len(v) for v in keywords_data['keywords'].values())} parole):")
    for sport, words in sorted(keywords_data["keywords"].items()):
        if words:
            print(f"   {sport}: {len(words)} parole")
    
    # FASE 5: Scarica tutti gli eventi usando il dizionario
    events = fetch_all_matches(keywords_data)
    
    if not events:
        print(" Nessun evento trovato!")
        return
    
    # FASE 6: Raggruppa e genera HTML
    total = group_and_generate(events)
    
    print("\n" + "="*70)
    print(f" OPERAZIONE COMPLETATA! {total} eventi totali")
    print(f" File generati in: {OUTPUT_DIR}/")
    print(f" Dizionario salvato in: {KEYWORDS_FILE}")
    print("="*70)

if __name__ == "__main__":
    main()