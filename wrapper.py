#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WRAPPER - Esegue tutti gli script in ordine
"""

import os
import sys
import subprocess
import shutil
import glob
from datetime import datetime

OUTPUT_DIR = "output"

# Script della repo originale (nella radice)
REPO_SCRIPTS = [
    "script_lista_livetv_sx.py",
    "script_lista_livetv_sx_reproductores.py",
    "script_canales_acestream.py",
    "script_reproductor_web.py",
    "script_logo.py",
    "script_detector_deportes.py",
    "script_detector_mistral.py",
    "script_scraper_acestream_api.py",
]

# TUOI script (in ordine)
TUOI_SCRIPTS = [
    "Pydroid_Spo.py",
    "genera_spo_html.py",
    "Pydroid_Ica.py",
    "genera_ica_txt.py",
    "genera_ica_html.py",
    "HatOggi.py",
    "HatOggiDomani.py",
    "PydroidRojaStV1.py",
    "PyGenHtmlM3U.py",
    "genera_livetv.py",
    "scraper_mamahd.py",
    "Pydroid_Dad_Auto.py",        # ← SOSTITUISCE la versione interattiva
]

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def run_script(script_path: str) -> bool:
    if not os.path.exists(script_path):
        log(f"⚠️ File non trovato: {script_path}")
        return False
    
    log(f"▶️ Esecuzione: {script_path}")
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
    except Exception as e:
        log(f"   ❌ Eccezione: {e}")
        return False

def main():
    print("="*70)
    print("🚀 KIRA-BLASTER-MASTER")
    print("="*70)
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # 1. Script repo originale
    print("\n📦 FASE 1: Script repo originale")
    for script in REPO_SCRIPTS:
        run_script(script)
    
    # 2. Tuoi script
    print("\n📦 FASE 2: Tuoi script")
    for script in TUOI_SCRIPTS:
        run_script(script)
    
    # 3. Sposta file
    print("\n📦 FASE 3: Spostamento file")
    for pattern in ["*.xml", "*.m3u", "*.json", "*.html", "*.txt"]:
        for f in glob.glob(pattern):
            if os.path.isfile(f):
                shutil.move(f, os.path.join(OUTPUT_DIR, f))
                log(f"   📦 Spostato: {f}")
    
    print("\n✅ OPERAZIONE COMPLETATA!")

if __name__ == "__main__":
    main()