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

# TUOI script (in ordine)
TUOI_SCRIPTS = [
    "scripts/personali/Pydroid_Spo.py",
    "scripts/personali/kira_spo_html_m3u.py",
    "scripts/personali/Pydroid_Ica.py",
    "scripts/personali/genera_ica_txt.py",
    "scripts/personali/genera_ica_html.py",
    "scripts/personali/kiraht.py",
    "scripts/personali/kiraht_od.py",
    "scripts/personali/PyGenHtmlM3U.py",
    "scripts/personali/mamahdday.py",
    "scripts/personali/sportora.py",
    "scripts/personali/ppvvt.py",
    "scripts/personali/kira_foo.py",
    "scripts/personali/kira_xust.py",
    "scripts/personali/kira_asi.py",
    "scripts/personali/kira_asi_sett.py",
    "scripts/personali/kira_asi_palin.py",
    "scripts/personali/genera_index.py",
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
    
    # 1. Tuoi script
    print("\n📦 FASE 2: Tuoi script")
    for script in TUOI_SCRIPTS:
        run_script(script)
    
    # 2. Sposta file (escludi index.html)
    print("\n📦 FASE 3: Spostamento file")
    for pattern in ["*.xml", "*.m3u", "*.json", "*.html", "*.txt"]:
        for f in glob.glob(pattern):
            if os.path.isfile(f) and f != "index.html":  # ← ESCLUDI index.html
                shutil.move(f, os.path.join(OUTPUT_DIR, f))
                log(f"   📦 Spostato: {f}")
    
    print("\n✅ OPERAZIONE COMPLETATA!")

if __name__ == "__main__":
    main()
