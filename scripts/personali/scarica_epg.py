#!/usr/bin/env python3
"""
Scarica l'EPG italiano da iptv-epg.org e lo salva in output/epg-it.xml
Uso:
  python scripts/personali/scarica-epg.py               # solo IT
  python scripts/personali/scarica-epg.py it ch de      # più paesi
"""
import sys
import os
import urllib.request
from datetime import datetime

BASE_URL = "https://iptv-epg.org/files/epg-{}.xml"
OUTPUT_DIR = "output"

def scarica(paese):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    url = BASE_URL.format(paese.lower())
    output = os.path.join(OUTPUT_DIR, f"epg-{paese.lower()}.xml")

    print(f"⬇️  Scarico {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read()

    with open(output, "wb") as f:
        f.write(data)

    size_kb = len(data) / 1024
    print(f"   ✅ {output} ({size_kb:.0f} KB)")
    return output

def main():
    paesi = sys.argv[1:] if len(sys.argv) > 1 else ["it"]
    print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    for paese in paesi:
        try:
            scarica(paese)
        except Exception as e:
            print(f"   ❌ Errore {paese}: {e}")

if __name__ == "__main__":
    main()