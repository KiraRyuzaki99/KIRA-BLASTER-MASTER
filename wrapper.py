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
    
    # 3. Sposta file (escludi index.html) - FATTO PRIMA di genera_index
    print("\n📦 FASE 3: Spostamento file in output/")
    for pattern in ["*.xml", "*.m3u", "*.json", "*.html", "*.txt"]:
        for f in glob.glob(pattern):
            if os.path.isfile(f) and f != "index.html":
                shutil.move(f, os.path.join(OUTPUT_DIR, f))
                log(f"   📦 Spostato: {f}")
    
    # 4. Ora genera index.html (dopo che i file sono in output/)
    print("\n📦 FASE 4: Generazione index.html")
    # Esegui genera_index.py come script separato
    if os.path.exists("scripts/personali/genera_index.py"):
        run_script("scripts/personali/genera_index.py")
    else:
        log("⚠️ genera_index.py non trovato")
    
    print("\n✅ OPERAZIONE COMPLETATA!")