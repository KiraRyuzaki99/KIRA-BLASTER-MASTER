#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from datetime import datetime

def generate_index():
    """Genera index.html nella root"""
    
    print("🔍 Cerco file in output/...")
    
    # Legge i file in output/
    files = []
    if os.path.exists("output"):
        for f in os.listdir("output"):
            if os.path.isfile(os.path.join("output", f)):
                files.append(f)
                print(f"   Trovato: {f}")
    else:
        print("❌ Cartella output/ non trovata!")
    
    print(f"📊 Trovati {len(files)} file")
    
    # Crea l'HTML
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>KIRA Output</title></head>
<body>
<h1>📡 KIRA-BLASTER-MASTER</h1>
<p>Aggiornato: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
<h2>File in output/ ({len(files)})</h2>
<ul>"""
    
    for f in sorted(files):
        html += f'<li><a href="output/{f}">{f}</a></li>'
    
    html += """</ul></body></html>"""
    
    # SCRIVE IL FILE - USA PERCORSO ASSOLUTO
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ index.html creato nella root!")
        
        # Verifica che esista
        if os.path.exists("index.html"):
            print("✅ CONFERMATO: index.html esiste!")
            print(f"   Dimensione: {os.path.getsize('index.html')} byte")
        else:
            print("❌ FALLITO: index.html non esiste dopo la scrittura!")
            
    except Exception as e:
        print(f"❌ ERRORE durante la scrittura: {e}")

if __name__ == "__main__":
    generate_index()