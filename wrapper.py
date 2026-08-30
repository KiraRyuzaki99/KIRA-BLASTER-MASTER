#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WRAPPER - Esegue tutti gli script in ordine e genera la pagina index.html
"""

import os
import sys
import subprocess
import shutil
import glob
from datetime import datetime
from html import escape

# ============================================================
#  CONFIGURAZIONE
# ============================================================

OUTPUT_DIR = "output"

# Script della repo originale (da eseguire per primi)
REPO_SCRIPTS = [
    "src/repo_scripts/script_lista_livetv_sx.py",
    "src/repo_scripts/script_lista_livetv_sx_reproductores.py",
    "src/repo_scripts/script_canales_acestream.py",
    "src/repo_scripts/script_reproductor_web.py",
    "src/repo_scripts/script_logo.py",
    "src/repo_scripts/script_detector_deportes.py",
    "src/repo_scripts/script_detector_mistral.py",
    "src/repo_scripts/script_scraper_acestream_api.py",
]

# TUOI script (in ordine di esecuzione)
TUOI_SCRIPTS = [
    "Pydroid_Spo.py",          # Genera XML
    "genera_spo_html.py",      # Trasforma XML in HTML
    "Pydroid_Ica.py",          # Genera M3U
    "genera_ica_txt.py",       # Trasforma M3U in TXT
    "genera_ica_html.py",      # Trasforma TXT in HTML
    "HatOggi.py",              # Genera HTML
    "HatOggiDomani.py",        # Genera HTML
    "PydroidRojaStV1.py",      # Genera HTML
    "PyGenHtmlM3U.py",         # Genera HTML + M3U
]

# ============================================================
#  FUNZIONI
# ============================================================

def create_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def run_script(script_path: str) -> bool:
    """Esegue uno script Python e restituisce True se ha successo."""
    if not os.path.exists(script_path):
        log(f"❌ File non trovato: {script_path}")
        return False
    
    log(f"▶️  Esecuzione: {script_path}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.stdout:
            for line in result.stdout.splitlines():
                print(f"   {line}")
        
        if result.stderr:
            for line in result.stderr.splitlines():
                print(f"   ⚠️ {line}")
        
        if result.returncode == 0:
            log(f"   ✅ Completato")
            return True
        else:
            log(f"   ❌ Errore (codice: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        log(f"   ❌ Timeout dopo 120 secondi")
        return False
    except Exception as e:
        log(f"   ❌ Eccezione: {e}")
        return False

def move_files_to_output(patterns: list):
    """Sposta i file generati nella cartella output."""
    for pattern in patterns:
        for f in glob.glob(pattern):
            if os.path.isfile(f):
                dest = os.path.join(OUTPUT_DIR, f)
                try:
                    shutil.move(f, dest)
                    log(f"   📦 Spostato: {f} -> {dest}")
                except Exception as e:
                    log(f"   ⚠️ Errore spostamento {f}: {e}")

def generate_index_html():
    """Genera una pagina index.html con tutti i file generati."""
    files = [f for f in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, f))]
    
    items_html = ""
    for f in sorted(files):
        ext = os.path.splitext(f)[1].lower()
        icons = {'.html': '🌐', '.m3u': '📺', '.xml': '📄', '.json': '📊', '.txt': '📝'}
        icon = icons.get(ext, '📎')
        
        items_html += f'''
        <div class="file-item">
            <span class="icon">{icon}</span>
            <a href="{f}" target="_blank">{escape(f)}</a>
            <span class="ext">{ext or 'file'}</span>
        </div>
        '''
    
    html_content = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📡 KIRA-BLASTER-MASTER - Output</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #0a0e17;
            color: #e0e0e0;
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 2px solid #00ffcc;
            margin-bottom: 40px;
        }}
        .header h1 {{
            font-size: 2.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #00ffcc, #00aaff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 2px;
        }}
        .header .subtitle {{
            color: #8899bb;
            font-size: 1.1rem;
            margin-top: 10px;
        }}
        .header .update-time {{
            color: #556688;
            font-size: 0.85rem;
            margin-top: 15px;
            font-family: 'Courier New', monospace;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: rgba(0, 255, 204, 0.05);
            border: 1px solid rgba(0, 255, 204, 0.15);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        .stat-card .num {{
            font-size: 2.2rem;
            font-weight: 700;
            color: #00ffcc;
        }}
        .stat-card .label {{
            font-size: 0.75rem;
            color: #8899bb;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 5px;
        }}
        .files-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 8px;
        }}
        .file-item {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 14px 20px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            transition: all 0.3s ease;
        }}
        .file-item:hover {{
            background: rgba(0, 255, 204, 0.06);
            border-color: rgba(0, 255, 204, 0.2);
            transform: translateX(5px);
        }}
        .file-item .icon {{ font-size: 1.5rem; width: 40px; text-align: center; }}
        .file-item a {{
            color: #00ffcc;
            text-decoration: none;
            font-size: 1rem;
            font-weight: 500;
            flex: 1;
            word-break: break-all;
        }}
        .file-item a:hover {{ text-decoration: underline; }}
        .file-item .ext {{
            font-size: 0.7rem;
            color: #556688;
            background: rgba(255,255,255,0.05);
            padding: 2px 12px;
            border-radius: 20px;
            text-transform: uppercase;
        }}
        .footer {{
            text-align: center;
            padding: 40px 0 20px;
            margin-top: 40px;
            border-top: 1px solid rgba(255,255,255,0.05);
            color: #556688;
            font-size: 0.85rem;
        }}
        .footer .highlight {{ color: #00ffcc; }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>📡 KIRA-BLASTER-MASTER</h1>
            <p class="subtitle">• Tutti i file generati dagli scraper •</p>
            <p class="update-time">🔄 Aggiornato: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div class="num">{len(files)}</div>
                <div class="label">File Generati</div>
            </div>
            <div class="stat-card">
                <div class="num">{len([f for f in files if f.endswith('.html')])}</div>
                <div class="label">HTML</div>
            </div>
            <div class="stat-card">
                <div class="num">{len([f for f in files if f.endswith('.m3u')])}</div>
                <div class="label">Playlist M3U</div>
            </div>
            <div class="stat-card">
                <div class="num">{len([f for f in files if f.endswith('.xml')])}</div>
                <div class="label">XML</div>
            </div>
        </div>

        <div class="files-grid">
            {items_html}
        </div>

        <footer class="footer">
            <p>⚡ Generato automaticamente da <span class="highlight">KIRA-BLASTER-MASTER</span> • {datetime.now().year}</p>
        </footer>
    </div>
</body>
</html>'''
    
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    log(f"✅ index.html generata")

# ============================================================
#  MAIN
# ============================================================

def main():
    print("="*70)
    print("🚀 KIRA-BLASTER-MASTER - Esecuzione automatica")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*70)
    
    create_output_dir()
    
    # 1. Script della repo originale
    print("\n📦 FASE 1: Script dalla repo originale")
    print("-"*50)
    for script in REPO_SCRIPTS:
        run_script(script)
    
    # 2. Tuoi script
    print("\n📦 FASE 2: I tuoi script")
    print("-"*50)
    for script in TUOI_SCRIPTS:
        run_script(script)
    
    # 3. Sposta i file generati in output/
    print("\n📦 FASE 3: Spostamento file in output/")
    print("-"*50)
    move_files_to_output(["*.xml", "*.m3u", "*.json", "*.html", "*.txt"])
    
    # 4. Genera index.html
    print("\n📦 FASE 4: Generazione index.html")
    print("-"*50)
    generate_index_html()
    
    print("\n" + "="*70)
    print("✅ OPERAZIONE COMPLETATA!")
    print(f"📁 Tutti i file sono nella cartella: {OUTPUT_DIR}/")
    print("="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrotto dall'utente")
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")