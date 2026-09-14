#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FootyStream scraper -> output/kira_gate.{html,m3u,json}
Versione integrata per KIRA-BLASTER-MASTER
"""

import os
import sys
import re
import json
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
BASE_URL = "https://footystream.pk"
PAGES = [f"{BASE_URL}/", f"{BASE_URL}/today", f"{BASE_URL}/tomorrow"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL + "/",
}

DISPLAY_TZ = timezone(timedelta(hours=2))   # Europe/Rome (estate)

# Output nella cartella condivisa del wrapper
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_HTML = os.path.join(OUTPUT_DIR, "kira_foo.html")
OUTPUT_M3U  = os.path.join(OUTPUT_DIR, "kira_foo.m3u")
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "kira_foo.json")

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()


def parse_iso(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def format_dt(start_iso):
    dt = parse_iso(start_iso)
    if not dt:
        return ("Data N/D", "--:--")
    dt = dt.astimezone(DISPLAY_TZ)
    giorni = ["Monday", "Tuesday", "Wednesday", "Thursday",
              "Friday", "Saturday", "Sunday"]
    mesi = ["January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"]
    return (f"{giorni[dt.weekday()]}, {dt.day:02d} {mesi[dt.month-1]} {dt.year}",
            dt.strftime("%H:%M"))


def compute_status(start_iso, end_iso):
    now = datetime.now(timezone.utc)
    s, e = parse_iso(start_iso), parse_iso(end_iso)
    if not s or not e:
        return "unknown"
    if now < s:        return "next"
    if s <= now <= e:  return "live"
    return "finished"


def fetch(url, timeout=8, retries=2):
    """GET con retry leggero."""
    last = None
    for i in range(retries + 1):
        try:
            return SESSION.get(url, timeout=timeout, allow_redirects=True)
        except Exception as e:
            last = e
            if i < retries:
                time.sleep(1.5)
    raise last


# ---------------------------------------------------------------------------
# LISTA EVENTI
# ---------------------------------------------------------------------------
def parse_list_page(html):
    soup = BeautifulSoup(html, "lxml")
    events, seen = [], set()

    for link in soup.select("a[href*='/events/']"):
        href = link.get("href", "")
        if not href or href in seen:
            continue
        seen.add(href)

        card = link.find("div")
        if not card:
            continue

        rows = card.select(".flex-col .flex.gap-2")
        title    = clean(rows[0].get_text(" ", strip=True)) if rows else None
        category = clean(rows[1].get_text(" ", strip=True)) if len(rows) > 1 else "Sport"
        if not title:
            continue

        img = card.find("img")
        logo = img.get("src") if img else None

        cd = card.select_one(".data-countdown")
        start_iso = cd.get("data-start") if cd else None
        end_iso   = cd.get("data-end")   if cd else None

        date_str, time_str = format_dt(start_iso)
        events.append({
            "title": title, "category": category, "logo": logo,
            "start_iso": start_iso, "end_iso": end_iso,
            "date": date_str, "time": time_str,
            "status": compute_status(start_iso, end_iso),
            "event_url": urljoin(BASE_URL, href),
            "servers": [],
        })
    return events


def collect_all():
    all_ev = {}
    for page in PAGES:
        print(f"[*] {page} ...")
        try:
            r = fetch(page)
            evs = parse_list_page(r.text)
            print(f"    -> {len(evs)} eventi")
            for ev in evs:
                all_ev[ev["event_url"]] = ev
        except Exception as e:
            print(f"    ! errore: {e}")
        time.sleep(0.5)
    return list(all_ev.values())


# ---------------------------------------------------------------------------
# SERVER: link /alpha/ nella pagina evento
# ---------------------------------------------------------------------------
def extract_watch_links(html, event_url):
    soup = BeautifulSoup(html, "lxml")
    results = []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if "/alpha/" not in h:
            continue
        full = urljoin(event_url, h)

        # label "Link N"
        label = "Server"
        td = a.find_parent("td")
        if td:
            prev = td.find_previous_sibling("td")
            if prev:
                label = prev.get_text(strip=True) or label

        # meta (mobile/quality/ads/language)
        meta = {}
        tr = a.find_parent("tr")
        if tr:
            tds = [clean(t.get_text(" ", strip=True)) for t in tr.find_all("td")]
            if len(tds) >= 6:
                meta = {"mobile": tds[2], "quality": tds[3],
                        "ads": tds[4], "language": tds[5]}

        results.append({"label": label, "url": full, "meta": meta})
    return results


def enrich_servers(events, delay=0.4):
    for i, ev in enumerate(events, 1):
        # salta i terminati
        if ev["status"] == "finished":
            ev["servers"] = []
            print(f"  [{i}/{len(events)}] ✅ {ev['title']} (skip, terminato)")
            continue

        try:
            r = fetch(ev["event_url"], timeout=8)
            ev["servers"] = extract_watch_links(r.text, ev["event_url"])
        except Exception as e:
            print(f"  [{i}/{len(events)}] ! {ev['title']}: {e}")
            ev["servers"] = []
            time.sleep(delay)
            continue

        icon = {"live":"🔴","next":"⏳","finished":"✅","unknown":"❔"}.get(ev["status"], "❔")
        print(f"  [{i}/{len(events)}] {icon} {ev['title']} -> {len(ev['servers'])} link")
        time.sleep(delay)


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CYBER GATE ACCESS</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Audiowide&family=Grotesk:wght@400;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Grotesk',sans-serif;background:#0a0a0a;color:#00ffcc;min-height:100vh}}
.matrix-bg{{position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;background:#0a0a0a;overflow:hidden}}
.matrix-bg::before{{content:'';position:absolute;top:0;left:0;width:100%;height:100%;
background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,255,204,0.03) 2px,rgba(0,255,204,0.03) 4px);
animation:matrixScroll 15s linear infinite}}
@keyframes matrixScroll{{0%{{transform:translateY(0)}}100%{{transform:translateY(100%)}}}}
.container{{max-width:1200px;margin:0 auto;padding:20px;position:relative;z-index:1}}
.header{{text-align:center;padding:30px 0 40px;border-bottom:2px solid rgba(0,255,204,0.3);margin-bottom:40px}}
.header h1{{font-family:'Orbitron',sans-serif;font-weight:900;font-size:3.5rem;
text-shadow:0 0 20px rgba(0,255,204,0.5);background:linear-gradient(135deg,#00ffcc,#00ccff);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px}}
.header .subtitle{{font-family:'Audiowide',cursive;color:#88ffdd;font-size:1.2rem;margin-top:10px}}
.event-counter{{text-align:center;font-family:'Orbitron',monospace;font-size:1.2rem;color:#00ffcc;
background:rgba(0,255,204,0.08);border:1px solid rgba(0,255,204,0.2);padding:12px 20px;
border-radius:30px;display:inline-block;margin:0 auto 30px}}
.event-counter span{{font-weight:900;font-size:1.5rem}}
.events-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:25px;margin-top:20px}}
.event-card{{background:rgba(0,30,30,0.7);border:1px solid rgba(0,255,204,0.2);border-radius:15px;
padding:25px;transition:all 0.3s ease;display:flex;flex-direction:column}}
.event-card:hover{{transform:translateY(-5px);border-color:rgba(0,255,204,0.6);box-shadow:0 0 40px rgba(0,255,204,0.15)}}
.event-info h3{{font-family:'Orbitron',sans-serif;font-weight:700;font-size:1.3rem;color:#00ffcc;margin-bottom:8px}}
.event-info .competition{{font-family:'Audiowide',cursive;color:#88ffdd;font-size:0.9rem;
background:rgba(0,255,204,0.1);padding:4px 12px;border-radius:20px;display:inline-block;margin-bottom:10px}}
.event-info .datetime{{color:#88ddff;font-size:0.9rem;opacity:0.85}}
.fonte-badge{{display:inline-block;font-size:0.75rem;background:rgba(0,255,204,0.15);color:#88ffdd;
padding:2px 12px;border-radius:12px;margin-top:5px;border:1px solid rgba(0,255,204,0.2)}}
.status-live{{display:inline-block;font-size:0.7rem;background:rgba(255,0,0,0.3);color:#ff4444;
padding:2px 10px;border-radius:12px;margin-left:8px;animation:pulse 1.5s ease-in-out infinite}}
.status-next{{display:inline-block;font-size:0.7rem;background:rgba(0,100,255,0.3);color:#4488ff;
padding:2px 10px;border-radius:12px;margin-left:8px}}
.status-finished{{display:inline-block;font-size:0.7rem;background:rgba(100,100,100,0.3);color:#888;
padding:2px 10px;border-radius:12px;margin-left:8px}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.5}}}}
.event-links{{margin-top:15px;padding-top:15px;border-top:1px solid rgba(0,255,204,0.15)}}
.server-link{{display:inline-block;font-family:'Orbitron',monospace;font-weight:700;color:#0a0a0a;
background:#00ffcc;padding:12px 24px;border-radius:8px;text-decoration:none;text-align:center;
width:100%;transition:all 0.3s ease}}
.server-link:hover{{background:#00ddbb;box-shadow:0 0 40px rgba(0,255,204,0.5)}}
.dropdown select{{width:100%;padding:12px 15px;background:rgba(0,20,20,0.9);color:#00ffcc;
border:1px solid rgba(0,255,204,0.4);border-radius:10px;font-family:'Orbitron',monospace;
font-size:0.85rem;cursor:pointer;outline:none}}
.no-link{{display:inline-block;font-family:'Orbitron',monospace;color:#666;text-align:center;width:100%;padding:10px}}
.footer{{text-align:center;padding:40px 0 20px;margin-top:60px;border-top:1px solid rgba(0,255,204,0.2);color:#88ddff;opacity:0.7}}
.footer .neon-text{{font-family:'Orbitron',monospace;color:#00ffcc;font-size:1rem}}
</style>
</head>
<body>
<div class="matrix-bg"></div>
<div class="container">
<header class="header">
    <h1>KIRA GATE ACCESS</h1>
    <p class="subtitle">• Eventi di Oggi •</p>
</header>
<div style="text-align:center;">
    <div class="event-counter">🎯 <span>{count}</span> eventi disponibili</div>
</div>
<div class="events-grid">
{cards}
</div>
<footer class="footer">
    <p class="neon-text">KIRA GSI SPORT • Eventi in Diretta • {year} • Developed by KIRA GSI GROUP</p>
</footer>
</div>
</body>
</html>
"""

CARD_TEMPLATE = """<div class="event-card">
    <div class="event-info">
        <h3>{title} {status_badge}</h3>
        <p class="competition">🏆 {category}</p>
        <p class="datetime">🕒 {time} • 📅 {date}</p>
        <span class="fonte-badge">📡 footystream.pk</span>
    </div>
    <div class="event-links">
{links_block}
    </div>
</div>
"""


def status_badge(status):
    return {
        "live":     '<span class="status-live">🔴 LIVE</span>',
        "next":     '<span class="status-next">⏳ PROSSIMO</span>',
        "finished": '<span class="status-finished">✅ TERMINATO</span>',
        "unknown":  '<span class="status-finished">❔ N/D</span>',
    }.get(status, "")


def build_links_block(ev):
    servers = ev["servers"]
    status = ev["status"]

    if status == "finished":
        return '        <span class="no-link">✅ Evento terminato</span>'

    if not servers:
        if status == "next":
            return '        <span class="no-link">⏳ Server disponibili poco prima dell\'inizio</span>'
        if status == "live":
            return '        <span class="no-link">🔴 In attesa del flusso…</span>'
        return '        <span class="no-link">⚠ Nessun server</span>'

    if len(servers) == 1:
        s = servers[0]
        return f'        <a href="{s["url"]}" target="_blank" class="server-link">▶ {s["label"]}</a>'

    opts = "\n".join(
        f'                    <option value="{s["url"]}">{s["label"]}'
        + (f' ({s["meta"].get("quality","")} {s["meta"].get("language","")})' if s.get("meta") else '')
        + '</option>'
        for s in servers
    )
    return f'''        <div class="dropdown">
            <select onchange="window.open(this.value, '_blank'); this.selectedIndex=0;">
                <option value="">📡 Scegli il server ({len(servers)})...</option>
{opts}
            </select>
        </div>'''


def render_html(events, path=OUTPUT_HTML):
    cards = []
    for ev in events:
        cards.append(CARD_TEMPLATE.format(
            title=ev["title"],
            status_badge=status_badge(ev["status"]),
            category=ev["category"],
            time=ev["time"],
            date=ev["date"],
            links_block=build_links_block(ev),
        ))
    html = HTML_TEMPLATE.format(count=len(events), cards="\n".join(cards), year=datetime.now().year)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] HTML -> {path}")


# ---------------------------------------------------------------------------
# M3U
# ---------------------------------------------------------------------------
def render_m3u(events, path=OUTPUT_M3U):
    lines = ["#EXTM3U"]
    skipped = 0
    for ev in events:
        servers = ev.get("servers") or []
        if not servers:
            skipped += 1
            continue
        logo = ev.get("logo") or ""
        group = ev["category"]
        for i, s in enumerate(servers, 1):
            url = s.get("url_final") or s["url"]
            name = ev["title"] if len(servers) == 1 else f'{ev["title"]} - {s["label"]}'
            lines.append(
                f'#EXTINF:-1 tvg-name="{ev["title"]}" tvg-logo="{logo}" '
                f'group-title="{group}",{name}'
            )
            lines.append(url)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[+] M3U -> {path}  ({skipped} eventi senza server saltati)")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("🎾 FOOTYSTREAM SCRAPER")
    print("=" * 70)

    print("[*] Raccolgo eventi...")
    events = collect_all()
    print(f"[+] Totale: {len(events)} eventi\n")

    # Sanity check: se 0 eventi, il sito è probabilmente down → non sovrascrivo
    if len(events) == 0:
        print("[!] Nessun evento trovato. Probabilmente il sito è down.")
        print("[!] NON sovrascrivo i file esistenti.")
        return

    order = {"live": 0, "next": 1, "unknown": 2, "finished": 3}
    events.sort(key=lambda e: (order.get(e["status"], 9), e["start_iso"] or ""))

    print("[*] Estraggo link /alpha/ dalle pagine evento...")
    enrich_servers(events, delay=0.4)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2, default=str)
    print(f"[+] JSON -> {OUTPUT_JSON}")

    render_html(events)
    render_m3u(events)

    print("\n===== RIEPILOGO =====")
    for ev in events:
        icon = {"live":"🔴","next":"⏳","finished":"✅","unknown":"❔"}.get(ev["status"], "❔")
        print(f"{icon} [{ev['category']}] {ev['title']}  ({len(ev['servers'])} link)")
    print(f"\n✅ Fatto! {len(events)} eventi.")


if __name__ == "__main__":
    main()
