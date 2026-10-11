#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Palinsesto settimanale da asiria.is SENZA link streaming
Fonte: indexgol.txt
"""

import re
import urllib.request
from datetime import date, timedelta, datetime
from collections import defaultdict
from jinja2 import Environment

URL_TXT = "https://asiria.is/indexgol.txt"
OUTPUT_HTML = "Eventi della Settimana.html"
GIORNI = 7

MESI = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}


def scarica_testo(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def parsa_data(stringa):
    """Parsa 'Sunday, 11 October 2026' in date."""
    m = re.match(
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(\d+)\s+(\w+)\s+(\d{4})",
        stringa.strip(), re.IGNORECASE
    )
    if not m:
        return None
    try:
        return date(int(m.group(4)), MESI[m.group(3).lower()], int(m.group(2)))
    except (ValueError, KeyError):
        return None


def parsa_indexgol_completo(testo):
    """
    Parsa TUTTO indexgol.txt.
    Ritorna: {data_iso: {sport: [eventi]}}
    """
    palinsesto = defaultdict(lambda: defaultdict(list))
    
    # Dividi per date: ogni data è un header "Day, DD Month YYYY"
    pattern_data = re.compile(
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+\d+\s+\w+\s+\d{4}",
        re.IGNORECASE
    )
    
    # Trova tutte le date e le loro posizioni
    matches = list(pattern_data.finditer(testo))
    
    for i, m in enumerate(matches):
        data_str = m.group(0)
        data_obj = parsa_data(data_str)
        if not data_obj:
            continue
        data_iso = data_obj.isoformat()
        
        inizio = m.end()
        fine = matches[i + 1].start() if i + 1 < len(matches) else len(testo)
        
        sezione = testo[inizio:fine]
        
        # Dividi in blocchi per separatore -----
        blocchi = re.split(r"-{10,}", sezione)
        
        for blocco in blocchi:
            blocco = blocco.strip()
            if not blocco:
                continue
            righe = [r.strip() for r in blocco.split("\n") if r.strip()]
            if not righe:
                continue
            
            prima = righe[0]
            m2 = re.match(r"^(\d{1,2}:\d{2})\s+(.+)$", prima)
            if not m2:
                continue
            
            orario = m2.group(1)
            resto = m2.group(2)
            
            if ":" in resto:
                sport_raw, evento = resto.split(":", 1)
                sport = sport_raw.strip().capitalize()
                evento = evento.strip()
            else:
                if resto.lower().startswith("tennis"):
                    sport = "Tennis"
                else:
                    sport = "Altro"
                evento = resto
            
            palinsesto[data_iso][sport].append({
                "time": orario,
                "event": evento
            })
    
    return {d: dict(s) for d, s in palinsesto.items()}


def estrai_settimana():
    print("=" * 55)
    print("  ASIRIA.IS — PALINSESTO SETTIMANALE (SENZA LINK)")
    print("=" * 55)
    
    testo = scarica_testo(URL_TXT)
    print(f"\n📡 Scaricati {len(testo)} caratteri")
    
    completo = parsa_indexgol_completo(testo)
    print(f"📅 Date trovate nel file: {len(completo)}")
    
    oggi = date.today()
    limite = oggi + timedelta(days=GIORNI)
    
    # Filtra solo i giorni nell'intervallo
    palinsesto = {}
    for d_iso, sport_dict in completo.items():
        d = date.fromisoformat(d_iso)
        if oggi <= d < limite:
            palinsesto[d_iso] = sport_dict
    
    totale = sum(len(v) for sd in palinsesto.values() for v in sd.values())
    print(f"\n✅ {totale} eventi nell'intervallo {oggi} → {limite}")
    for d_iso in sorted(palinsesto):
        n = sum(len(v) for v in palinsesto[d_iso].values())
        print(f"   📅 {d_iso}: {n} eventi")
    
    return palinsesto


# HTML_PURO rimane identico a prima (senza link)
HTML_PURO = r"""..."""  # ← COPIA quello che hai già


def genera_html(palinsesto):
    if not palinsesto:
        print("❌ Nessun evento")
        return
    giorni = sorted(palinsesto.keys())
    giorno_label = {}
    for d_iso in giorni:
        d = date.fromisoformat(d_iso)
        giorno_label[d_iso] = d.strftime("%A %d %B %Y").capitalize()
    sport_ordinati = {}
    for d_iso in giorni:
        sl = list(palinsesto[d_iso].keys())
        sl.sort()
        sport_ordinati[d_iso] = sl
    settimana = f"{date.fromisoformat(giorni[0]).strftime('%d/%m')} - {date.fromisoformat(giorni[-1]).strftime('%d/%m/%Y')}"
    env = Environment()
    t = env.from_string(HTML_PURO)
    out = t.render(palinsesto=palinsesto, giorni=giorni,
                   giorno_label=giorno_label, sport_ordinati=sport_ordinati,
                   settimana=settimana)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"\n✅ Generato: {OUTPUT_HTML}")


if __name__ == "__main__":
    p = estrai_settimana()
    if p:
        genera_html(p)
    else:
        print("⚠️ Nessun evento nella settimana")