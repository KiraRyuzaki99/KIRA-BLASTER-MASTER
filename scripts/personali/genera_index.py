#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera index.html dinamico dalla cartella output/
"""
import os
from datetime import datetime

OUTPUT_DIR = "output"
INDEX_FILE = "index.html"

def get_file_icon(extension):
    """Restituisce un'icona in base all'estensione."""
    icons = {
        '.html': '🌐',
        '.m3u': '📺',
        '.xml': '📄',
        '.json': '📊',
        '.txt': '📝',
        '.csv': '📋',
        '.png': '🖼️',
        '.jpg': '🖼️',
        '.jpeg': '🖼️',
        '.gif': '🖼️',
        '.py': '🐍',
        '.md': '📝',
    }
    return icons.get(extension.lower(), '📁')

def generate_index():
    """Genera index.html nella root con link ai file in output/"""
    
    # Scansiona i file in output/
    files = []
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            file_path = os.path.join(OUTPUT_DIR, f)
            if os.path.isfile(file_path):
                name, ext = os.path.splitext(f)
                # Salta index.html se esiste già in output
                if f == "index.html":
                    continue
                files.append({
                    'name': f,
                    'ext': ext,
                    'icon': get_file_icon(ext),
                    'path': f"{OUTPUT_DIR}/{f}"
                })
    
    # Ordina per nome
    files.sort(key=lambda x: x['name'].lower())
    
    # Statistiche
    total_files = len(files)
    html_count = sum(1 for f in files if f['ext'] == '.html')
    m3u_count = sum(1 for f in files if f['ext'] == '.m3u')
    xml_count = sum(1 for f in files if f['ext'] == '.xml')
    txt_count = sum(1 for f in files if f['ext'] == '.txt')
    json_count = sum(1 for f in files if f['ext'] == '.json')
    
    # Genera HTML
    today = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    files_html = ""
    if files:
        for f in files:
            files_html += f'''
        <div class="file-item">
            <span class="icon">{f['icon']}</span>
            <a href="{f['path']}" target="_blank">{f['name']}</a>
            <span class="ext">{f['ext']}</span>
        </div>
        '''
    else:
        files_html = '''
        <div class="file-item" style="justify-content: center; color: #556688;">
            <span>📂 Nessun file trovato nella cartella output/</span>
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
            <p class="update-time">🔄 Aggiornato: {today}</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div class="num">{total_files}</div>
                <div class="label">File Generati</div>
            </div>
            <div class="stat-card">
                <div class="num">{html_count}</div>
                <div class="label">HTML</div>
            </div>
            <div class="stat-card">
                <div class="num">{m3u_count}</div>
                <div class="label">Playlist M3U</div>
            </div>
            <div class="stat-card">
                <div class="num">{xml_count}</div>
                <div class="label">XML</div>
            </div>
        </div>

        <div class="files-grid">
            {files_html}
        </div>

        <footer class="footer">
            <p>⚡ Generato automaticamente da <span class="highlight">KIRA-BLASTER-MASTER</span> • {datetime.now().year}</p>
        </footer>
    </div>
</body>
</html>'''
    
    # Scrivi index.html nella ROOT
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ index.html generato nella root con {total_files} file da {OUTPUT_DIR}/")

if __name__ == "__main__":
    generate_index()