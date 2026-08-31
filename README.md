# 📡 KIRA-BLASTER-MASTER

**Scraper automatico per eventi sportivi** - Genera pagine HTML e playlist M3U da multiple fonti.

![Workflow Status](https://github.com/KiraRyuzaki99/KIRA-BLASTER-MASTER/actions/workflows/update.yml/badge.svg)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Caratteristiche

- 🔄 **Aggiornamento automatico** ogni 2 ore via GitHub Actions
- 📊 **Multiple fonti** di eventi sportivi
- 🏆 **Multi-sport**: Calcio, Tennis, Basket, Baseball, Motori, Surf, Nuoto e altri
- 📱 **Output in HTML e M3U** per visualizzare su browser o lettori IPTV
- 🎨 **Stile cyberpunk** uniforme per tutti i file
- 📁 **Organizzazione** automatica in cartelle dedicate

---

## 📦 Fonti attive

| Fonte | Output | Sport |
|-------|--------|-------|
| **HTSport** | `htsport_today.html` | Calcio |
| **HTSport Futuri** | `htsport_today_future.html` | Calcio |
| **Rojadirecta** | `Agenda Sportiva.html` | Multi |
| **StreamX** | `streamx_events.html` | Multi |
| **MamaHD** | `Kira_MamaHD.html` | Multi |
| **DaddyLive** | `KIRA_GSI_*.html` | Multi |
| **LiveTV** | `Kira_LiveTV.html` | Multi |
| **Sportsonline** | `Kira_Spo.html` | Calcio |
| **Icastresana** | `Kira_Ica.html` | Multi |

---

## 📁 Output generati

Tutti i file generati sono disponibili nelle cartelle:

| Cartella | Contenuto |
|----------|-----------|
| `output/` | Catalogo completo e file da altre fonti |

### Link diretto al Catalogo 
https://raw.githubusercontent.com/KiraRyuzaki99/KIRA-BLASTER-MASTER/main/output/index.html

---

## 🔧 Installazione locale

```bash
# 1. Clona la repository
git clone https://github.com/KiraRyuzaki99/KIRA-BLASTER-MASTER.git
cd KIRA-BLASTER-MASTER

# 2. Installa le dipendenze
pip install -r requirements.txt

# 3. Esegui tutti gli scraper
python wrapper.py

https://raw.githubusercontent.com/KiraRyuzaki99/KIRA-BLASTER-MASTER/main/output/Kira_Spo.html
https://raw.githubusercontent.com/KiraRyuzaki99/KIRA-BLASTER-MASTER/main/output/Kira_Ica.html

📁 KIRA-BLASTER-MASTER/
├── .github/workflows/          # Automazione
│   └── update.yml
├── output/                     # File generati (fonti multiple)
├── daddy_output/               # File generati da DaddyLive
├── scripts/                    # Script Python
│   ├── repo/                   # Script da altre repo
│   └── personali/              # Script personali
├── wrapper.py                  # Esecutore principale
├── requirements.txt            # Dipendenze
└── README.md                   # Questo file


---

## 📝 2. Creare `.gitignore`

Vai su `https://github.com/KiraRyuzaki99/KIRA-BLASTER-MASTER` → clicca su **"Add file"** → **"Create new file"**

**Nome:** `.gitignore`

**Contenuto:**

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# Temporanei
*.tmp
*.bak
*.old
*.backup

# Output (se non vuoi versionare i file generati - commenta se li vuoi tenere)
# output/
# daddy_output/

# File di debug
debug_*.py
test_*.py



