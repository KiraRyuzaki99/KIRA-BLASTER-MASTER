#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera index.html DENTRO la cartella output/ con lo stile Matrix (Index mod.html)
"""
import os
from datetime import datetime

# >>> QUI INSERISCI LA LISTA DEI FILE CHE VUOI NEL TUO INDEX <<<
FILE_DA_MOSTRARE = [
    "Eventi della Settimana.html",
    "kira_asi.html",
    "kira_hat.html",
    "kira_mam.html",
    "kira_ppvvt.html",
    "kira_spo.html",
    "kira_ultra.html",
]

OUTPUT_DIR = "output"

def generate_index():
    """Genera index.html DENTRO la cartella output/"""
    
    # 1. Verifica quali file esistono in output/
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
    
    # 2. Ordina alfabeticamente (opzionale, puoi toglierlo se vuoi l'ordine della lista sopra)
    files_esistenti.sort()
    
    # 3. Data
    today = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    # 4. Costruiamo i tag <li> per la lista HTML in modo dinamico
    lista_li = ""
    contatore_cyber = 1  # Partiamo da 1 per i file KIRA CYBER

    for f in files_esistenti:
        # Controlliamo se è il file degli eventi
        if "Eventi della Settimana" in f:
            # Nome speciale e classe CSS dedicata
            nome_visualizzato = "🔥 PALINSESTO: EVENTI DELLA SETTIMANA 🔥"
            classe_li = 'class="palinsesto"'
        else:
            # Nome standard per gli altri file usando il nostro contatore
            nome_visualizzato = f"KIRA CYBER {contatore_cyber}"
            classe_li = ""
            contatore_cyber += 1  # Incrementiamo il contatore SOLO per i file Kira
        
        # Aggiunge il pulsante alla lista
        lista_li += f'            <li {classe_li}><a href="{f}">📁 {nome_visualizzato}</a></li>\n'
    
    # 5. Creazione del file HTML (usando le doppie graffe {{ }} per il CSS/JS)
    # NOTA: Questo blocco è ora FUORI dal ciclo for, quindi viene eseguito una volta sola!
    html = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KIRA GSI DATA</title>
    
    <!-- Font da Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Audiowide&family=Space+Grotesk:wght@300;400;700&display=swap" rel="stylesheet">
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Space Grotesk', sans-serif;
            background-color: #000;
            color: #0f0;
            overflow-x: hidden;
            min-height: 100vh;
        }}
        
        /* Canvas per effetto Matrix */
        #matrix-canvas {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
        }}
        
        /* Contenuto principale */
        .container {{
            position: relative;
            z-index: 2;
            max-width: 900px;
            margin: 0 auto;
            padding: 60px 20px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        
        h1 {{
            font-family: 'Audiowide', sans-serif;
            font-size: 3em;
            text-align: center;
            color: #00ffff;
            text-shadow: 0 0 10px #0f0, 0 0 20px #0f0, 0 0 30px #0f0;
            margin-bottom: 20px;
            letter-spacing: 3px;
        }}
        
        .subtitle {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.3em;
            text-align: center;
            color: #00ffff;
            margin-bottom: 30px;
            text-shadow: 0 0 10px #0f0, 0 0 20px #0f0, 0 0 30px #0f0;
        }}
        
        /* Immagine centrale */
        .image-container {{
            text-align: center;
            margin: 40px 0;
        }}
        
        .center-image {{
            max-width: 400px;
            width: 80%;
            height: auto;
            border: 3px solid #0f0;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.5), 0 0 40px rgba(0, 255, 0, 0.3);
            transition: all 0.3s ease;
            display: inline-block;
        }}
        
        .center-image:hover {{
            box-shadow: 0 0 30px rgba(0, 255, 0, 0.8), 0 0 60px rgba(0, 255, 0, 0.5);
            transform: scale(1.05);
        }}
        
        ul {{
            list-style-type: none;
            padding: 0;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        li {{
            margin: 20px 0;
            opacity: 0;
            animation: fadeIn 0.5s ease-in forwards;
        }}
        
        /* Animazione di comparsa progressiva per i primi 15 file */
        li:nth-child(1) {{ animation-delay: 0.1s; }}
        li:nth-child(2) {{ animation-delay: 0.2s; }}
        li:nth-child(3) {{ animation-delay: 0.3s; }}
        li:nth-child(4) {{ animation-delay: 0.4s; }}
        li:nth-child(5) {{ animation-delay: 0.5s; }}
        li:nth-child(6) {{ animation-delay: 0.6s; }}
        li:nth-child(7) {{ animation-delay: 0.7s; }}
        li:nth-child(8) {{ animation-delay: 0.8s; }}
        li:nth-child(9) {{ animation-delay: 0.9s; }}
        li:nth-child(10) {{ animation-delay: 1.0s; }}
        li:nth-child(11) {{ animation-delay: 1.1s; }}
        li:nth-child(12) {{ animation-delay: 1.2s; }}
        
        @keyframes fadeIn {{
            to {{ opacity: 1; }}
        }}
        
        a {{
            display: block;
            padding: 20px 25px;
            background-color: rgba(0, 20, 0, 0.8);
            color: #00ffff;
            text-decoration: none;
            border: 2px solid #0f0;
            border-radius: 5px;
            font-family: 'Audiowide', sans-serif;
            font-size: 1.1em;
            transition: all 0.3s ease;
            text-shadow: 0 0 90px #00ffff;
            box-shadow: 0 0 35px rgba(0, 255, 0, 0.3);
        }}
        
        a:hover {{
            background-color: #0f0;
            color: #000;
            box-shadow: 0 0 20px #0f0, 0 0 30px #0f0;
            transform: scale(1.02);
        }}
        
        /* Stile speciale per il Palinsesto */
        .palinsesto a {{
            color: #ff0055; /* Colore fucsia/rosso acceso per distinguerlo */
            border: 2px solid #ff0055;
            text-shadow: 0 0 15px #ff0055, 0 0 30px #ff0055;
            box-shadow: 0 0 20px rgba(255, 0, 85, 0.5);
            font-size: 1.3em; /* Testo leggermente più grande */
        }}
        
        .palinsesto a:hover {{
            background-color: #ff0055;
            color: #000;
            box-shadow: 0 0 30px #ff0055, 0 0 60px #ff0055;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 60px;
            font-size: 0.9em;
            font-family: 'Space Grotesk', sans-serif;
            color: #00ffff;
            text-shadow: 0 0 5px #00ffff;
        }}
        
        /* Effetto glitch sul titolo */
        .glitch {{
            position: relative;
        }}
        
        .glitch::before,
        .glitch::after {{
            content: attr(data-text);
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }}
        
        .glitch::before {{
            animation: glitch-1 0.3s infinite;
            clip: rect(0, 900px, 0, 0);
            color: #0ff;
            z-index: -1;
        }}
        
        .glitch::after {{
            animation: glitch-2 0.3s infinite;
            clip: rect(0, 900px, 0, 0);
            color: #f0f;
            z-index: -2;
        }}
        
        @keyframes glitch-1 {{
            0% {{ transform: translate(0); }}
            20% {{ transform: translate(-2px, 2px); }}
            40% {{ transform: translate(-2px, -2px); }}
            60% {{ transform: translate(2px, 2px); }}
            80% {{ transform: translate(2px, -2px); }}
            100% {{ transform: translate(0); }}
        }}
        
        @keyframes glitch-2 {{
            0% {{ transform: translate(0); }}
            20% {{ transform: translate(2px, -2px); }}
            40% {{ transform: translate(2px, 2px); }}
            60% {{ transform: translate(-2px, -2px); }}
            80% {{ transform: translate(-2px, 2px); }}
            100% {{ transform: translate(0); }}
        }}
        
        /* Responsive */
        @media (max-width: 600px) {{
            h1 {{ font-size: 2em; }}
            .subtitle {{ font-size: 1em; }}
            a {{ font-size: 1em; padding: 15px 20px; }}
            .center-image {{ max-width: 90%; }}
        }}
    </style>
</head>
<body>
    <!-- Canvas per effetto Matrix -->
    <canvas id="matrix-canvas"></canvas>
    
    <!-- Contenuto principale -->
    <div class="container">
        <h1 class="glitch" data-text="ACCESSO AI FILE">KIRA GSI DATA</h1>
        <p class="subtitle">Benvenuto in Kira, Scegli la tua categoria di Eventi...</p>
        <p class="subtitle">ATTACCA IL PIANETA !!!</p>
        
        <!-- IMMAGINE CENTRALE -->
        <div class="image-container">
            <!-- Assicurati che logo.jpg sia presente nella cartella output/ -->
            <img src="logo.jpg" alt="Banner" class="center-image">
        </div>
        
        <ul>
{lista_li}        </ul>
        
        <div class="footer">
            <p>SYSTEM ACTIVATED // DATA DEPLOYED</p>
            <p style="margin-top: 5px; font-size: 0.8em;">Ultimo aggiornamento: {today}</p>
        </div>
    </div>
    
    <script>
        // Effetto Matrix
        const canvas = document.getElementById('matrix-canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        const katakana = 'アァカサタナハマヤャラワガザダバパイィキシチニヒミリヂビピウゥクスツヌフムユュルグズブヅプエェケセテネヘメレゲゼデベペオォコソトノホモヨョロヲゴゾドボポヴッン';
        const latin = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        const nums = '0123456789';
        const alphabet = katakana + latin + nums;
        
        const fontSize = 16;
        const columns = canvas.width / fontSize;
        
        const rainDrops = [];
        
        for (let x = 0; x < columns; x++) {{
            rainDrops[x] = 1;
        }}
        
        const draw = () => {{
            ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            ctx.fillStyle = '#0f0';
            ctx.font = fontSize + 'px monospace';
            
            for (let i = 0; i < rainDrops.length; i++) {{
                const text = alphabet.charAt(Math.floor(Math.random() * alphabet.length));
                ctx.fillText(text, i * fontSize, rainDrops[i] * fontSize);
                
                if (rainDrops[i] * fontSize > canvas.height && Math.random() > 0.975) {{
                    rainDrops[i] = 0;
                }}
                rainDrops[i]++;
            }}
        }};
        
        setInterval(draw, 30);
        
        window.addEventListener('resize', () => {{
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }});
    </script>
</body>
</html>'''
    
    # 6. Scrive il file finale
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ index.html (stile Matrix) creato in {OUTPUT_DIR}/ con {len(files_esistenti)} file!")

if __name__ == "__main__":
    generate_index()
