#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERATORE ICA TXT - Trasforma lista_icastresana.m3u in file intermedio
"""

import re
import os

INPUT_FILE = "lista_icastresana.m3u"
OUTPUT_FILE = "lista_icastresana_intermedia.txt"

def parse_m3u_to_txt():
    """Legge il file M3U e lo trasforma in formato TXT."""
    if not os.path.exists(INPUT_FILE):
        print(f"❌ File {INPUT_FILE} non trovato!")
        return
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    output_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Cerca le righe #EXTINF:
        if line.startswith('#EXTINF:'):
            # Estrai il nome del canale/evento
            match = re.search(r',(.+)$', line)
            if match:
                event_name = match.group(1).strip()
            else:
                event_name = "Evento"
            
            # La riga successiva dovrebbe essere l'URL
            i += 1
            if i < len(lines):
                url = lines[i].strip()
                # Converti Acestream se presente
                if 'acestream://' in url:
                    acestream_id = url.split('acestream://')[1]
                    url = f"http://127.0.0.1:6878/ace/getstream?id={acestream_id}"
                output_lines.append(f"{event_name} | {url}")
        i += 1
    
    # Salva il file TXT
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"✅ File generato: {OUTPUT_FILE} ({len(output_lines)} righe)")

if __name__ == "__main__":
    parse_m3u_to_txt()