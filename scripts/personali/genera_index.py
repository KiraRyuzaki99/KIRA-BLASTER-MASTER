#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera index.html DENTRO la cartella output/
"""
import os
from datetime import datetime

# >>> QUI INSERISCI LA LISTA DEI FILE CHE VUOI NEL TUO INDEX <<<
FILE_DA_MOSTRARE = [
    "kira_spo.html",
    "kira_hat.html",
    "kira_ultra.html",
    "kira_liv.html",
    "Kira_Ica.html",
    "kira_hat_od.html",
    "kira_tora.html",
    "kira_ppvvt.html",
    "kira_mam.html",
    "requirements.txt",
]

OUTPUT_DIR = "output"

def generate_index():
    """Genera index.html DENTRO la cartella output/"""
    
    # Verifica quali file esistono in output/
    files_esistenti = []
    if os.path.exists(OUTPUT_DIR):
        for f in FILE_DA_MOSTRARE:
            file_path = os.path.join(OUTPUT_DIR, f)
            if os.path.exists(file_path):
                files_esistenti.append(f)
            else:
                print(f"⚠️ File non trovato: {f}")
    else:
        print(f"❌ Cartella {OUTPUT_DIR} non trovata!")
        return
    
    # Ordina
    files_esistenti.sort()
    
    # Data
    today = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    # Crea HTML
    html = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📡 KIRA-BLASTER-MASTER - Raccoglitore </title>
    <style>
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #0a0e17;
            color: #e0e0e0;
            padding: 40px 20px;
        }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #00ffcc; }}
        .file-list {{
            list-style: none;
            padding: 0;
        }}
        .file-list li {{
            padding: 10px 15px;
            margin: 5px 0;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .file-list a {{
            color: #00ffcc;
            text-decoration: none;
        }}
        .file-list a:hover {{ text-decoration: underline; }}
        .footer {{
            margin-top: 40px;
            color: #556688;
            text-align: center;
            border-top: 1px solid rgba(255,255,255,0.1);
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📡 KIRA-BLASTER-MASTER</h1>
        <p>🔄 Aggiornato: {today}</p>
        <p>📁 {len(files_esistenti)} file disponibili</p>
        <ul class="file-list">'''
    
    for f in files_esistenti:
        html += f'<li><a href="{f}">{f}</a></li>'
    
    html += f'''
        </ul>
        <div class="footer">
            <p>⚡ Generato automaticamente • {datetime.now().year}</p>
        </div>
    </div>
</body>
</html>'''
    
    # Scrivi index.html DENTRO output/
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ index.html creato in {OUTPUT_DIR}/ con {len(files_esistenti)} file!")

if __name__ == "__main__":
    generate_index()
