#!/usr/bin/env python3
"""
kira_wizard.py

Scarica TUTTI i match di oggi da streamed.pk, genera:
  - kira_ultra.html  (stile KIRA GATE)
  - kira_playlist.m3u

Funziona sia in locale (Pydroid) sia nella repo GitHub.
Dipendenze: solo requests.
"""

import html as html_lib
from datetime import datetime, date, timezone
from pathlib import Path
import requests


# ==================================================================
# CONFIGURAZIONE
# ==================================================================
SPORTS = [
    "football",
    "basketball",
    "american-football",
    "baseball",
    "motor-sports",
    "fight",
    "tennis",
    "golf",
    "billiards",
    "darts",
    "other",
]

API_BASE = "https://streamed.pk/api"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
    "Accept": "application/json",
}

SPORT_LABELS = {
    "football": "Calcio",
    "basketball": "Basket",
    "american-football": "Football Americano",
    "baseball": "Baseball",
    "motor-sports": "Motori",
    "fight": "Fight (UFC/Boxe)",
    "tennis": "Tennis",
    "golf": "Golf",
    "billiards": "Biliardo",
    "darts": "Freccette",
    "other": "Altro",
}

LOCAL_TZ = datetime.now().astimezone().tzinfo


# ==================================================================
# OUTPUT DIR - trova o crea la cartella output in modo sicuro
# ==================================================================
def find_output_dir() -> Path:
    """
    Prova a scrivere in /storage/emulated/0/output (memoria condivisa,
    visibile dal file manager di Android). Se non è possibile, usa la
    cartella accanto allo script.
    """
    # 1. Prova la memoria condivisa del telefono
    shared = Path("/storage/emulated/0/output")
    try:
        shared.mkdir(parents=True, exist_ok=True)
        # Test di scrittura reale
        test_file = shared / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return shared
    except (PermissionError, OSError):
        pass

    # 2. Fallback per GitHub: cerca "output" nei parent dello script
    here = Path(__file__).resolve().parent
    for base in [here, here.parent, here.parent.parent, here.parent.parent.parent]:
        candidate = base / "output"
        if candidate.is_dir():
            return candidate

    # 3. Ultima spiaggia: crea "output" accanto allo script
    fallback = here / "output"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


OUTPUT_DIR = find_output_dir()
OUTPUT_HTML = OUTPUT_DIR / "kira_xust.html"
OUTPUT_M3U = OUTPUT_DIR / "kira_xust.m3u"


# ==================================================================
# 1. FETCH
# ==================================================================
def fetch_matches(sport: str) -> list[dict]:
    url = f"{API_BASE}/matches/{sport}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  ✘ {sport}: {e}")
        return []


def fetch_all() -> list[dict]:
    print("→ Scarico eventi per sport...")
    all_events = []
    for sport in SPORTS:
        matches = fetch_matches(sport)
        for m in matches:
            m["_sport"] = sport
        all_events.extend(matches)
        print(f"  ✔ {sport}: {len(matches)} match")
    print(f"  ✔ Totale: {len(all_events)} match\n")
    return all_events


# ==================================================================
# 2. NORMALIZZAZIONE
# ==================================================================
def normalize(events: list[dict]) -> list[dict]:
    result = []
    for ev in events:
        ts = ev.get("date")
        if not ts:
            continue
        try:
            dt_utc = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
            dt_local = dt_utc.astimezone(LOCAL_TZ)
        except Exception:
            continue

        time_str = dt_local.strftime("%H:%M")
        date_str = dt_local.strftime("%d/%m/%Y")
        day_key = dt_local.strftime("%Y-%m-%d")
        sort_key = int(ts)

        links = []
        for src in ev.get("sources", []):
            source_name = src.get("source", "")
            source_id = src.get("id", "")
            if not source_id:
                continue
            url = f"https://golxu.st/eventostop.html?id={source_id}"
            label = {
                "admin": "Server 1 (admin)",
                "delta": "Server 2 (delta)",
                "echo":  "Server 3 (echo)",
            }.get(source_name, source_name or "Server")
            links.append({"name": label, "url": url})

        result.append({
            "id": ev.get("id", ""),
            "title": ev.get("title", "?"),
            "sport": ev.get("_sport", ""),
            "sport_label": SPORT_LABELS.get(ev.get("_sport", ""), ev.get("_sport", "")),
            "time": time_str,
            "date": date_str,
            "day_key": day_key,
            "timestamp": sort_key,
            "links": links,
        })
    return result


def filter_today(events: list[dict]) -> list[dict]:
    today_key = date.today().strftime("%Y-%m-%d")
    return [e for e in events if e["day_key"] == today_key]


def sort_events(events: list[dict]) -> list[dict]:
    return sorted(events, key=lambda e: e["timestamp"])


# ==================================================================
# 3. HTML
# ==================================================================
CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;background:#0a0a0a;
     color:#e2e8f0;min-height:100vh;padding-bottom:40px}
.container{max-width:1200px;margin:0 auto;padding:20px}
.header{text-align:center;padding:20px 0 25px;
        border-bottom:2px solid rgba(0,255,204,0.3);margin-bottom:20px}
.header h1{font-weight:900;font-size:2.2rem;color:#00ffcc;letter-spacing:3px}
.header .subtitle{color:#88ffdd;margin-top:6px;font-size:0.9rem}
.counter{text-align:center;color:#00ffcc;background:rgba(0,255,204,0.08);
    border:1px solid rgba(0,255,204,0.2);padding:8px 16px;border-radius:30px;
    display:inline-block;margin:0 auto 15px;font-size:0.9rem}
.counter span{font-weight:900;font-size:1.1rem}
.filter-bar{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;
            margin-bottom:15px}
.filter-btn{background:rgba(0,255,204,0.08);border:1px solid rgba(0,255,204,0.3);
    color:#00ffcc;padding:5px 12px;border-radius:20px;cursor:pointer;
    font-size:0.78rem;font-weight:600;transition:0.15s}
.filter-btn:hover,.filter-btn.active{background:#00ffcc;color:#0a0a0a}
.events-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));
             gap:14px}
.event-card{background:#141416;border:1px solid rgba(255,255,255,0.06);
    border-radius:12px;padding:15px;display:flex;flex-direction:column;
    transition:0.15s}
.event-card:hover{border-color:rgba(0,255,204,0.4);
                  box-shadow:0 0 20px rgba(0,255,204,0.08)}
.event-card.live{border-color:#dc2626;
    box-shadow:0 0 20px rgba(220,38,38,0.2)}
.event-info h3{font-weight:700;font-size:0.98rem;color:#fff;
    margin-bottom:6px;line-height:1.3}
.event-info .competition{color:#88ffdd;font-size:0.75rem;
    background:rgba(0,255,204,0.08);padding:2px 9px;border-radius:12px;
    display:inline-block;margin-bottom:6px}
.event-info .datetime{color:#88ddff;font-size:0.8rem;margin-bottom:5px}
.status-live-badge{display:inline-block;font-size:0.68rem;
    background:#dc2626;color:#fff;padding:2px 8px;border-radius:10px;
    font-weight:800;margin-left:6px;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}
.badge{display:inline-block;font-size:0.68rem;color:#88ffdd;
    background:rgba(0,255,204,0.1);padding:2px 8px;border-radius:10px;
    border:1px solid rgba(0,255,204,0.15)}
.event-links{margin-top:12px;padding-top:12px;
             border-top:1px solid rgba(255,255,255,0.06)}
.server-link{display:block;font-weight:700;color:#0a0a0a;background:#00ffcc;
    padding:9px 14px;border-radius:7px;text-decoration:none;text-align:center;
    font-size:0.85rem;transition:0.15s}
.server-link:hover{background:#00ddbb}
.dropdown select{width:100%;padding:9px 12px;background:#0a0a0a;
    color:#00ffcc;border:1px solid rgba(0,255,204,0.4);border-radius:7px;
    font-size:0.85rem;cursor:pointer;outline:none}
.no-link{display:block;color:#666;text-align:center;padding:8px;
         font-size:0.8rem}
.footer{text-align:center;padding:25px 0 15px;margin-top:30px;
        border-top:1px solid rgba(255,255,255,0.06);color:#555;
        font-size:0.75rem}
"""

JS = """
function filterSport(sport){
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('.event-card').forEach(c=>{
    if(sport==='all' || c.dataset.sport===sport) c.style.display='';
    else c.style.display='none';
  });
}
"""


def esc(s):
    return html_lib.escape(str(s), quote=True)


def build_html(events: list[dict]) -> str:
    now = datetime.now()
    sports = sorted(set(e["sport"] for e in events if e["sport"]))

    parts = [
        "<!DOCTYPE html>",
        '<html lang="it"><head><meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        "<title>KIRA GATE ACCESS</title>",
        f"<style>{CSS}</style></head><body>",
        '<div class="container">',
        '<header class="header">',
        "<h1>KIRA GATE ACCESS</h1>",
        f'<p class="subtitle">• Eventi del {now.strftime("%d/%m/%Y")} •</p>',
        "</header>",
        '<div style="text-align:center">',
        f'<div class="counter">🎯 <span>{len(events)}</span> eventi oggi</div>',
        "</div>",
    ]

    if sports:
        parts.append('<div class="filter-bar">')
        parts.append(
            '<button class="filter-btn active" onclick="filterSport(\'all\')">'
            'Tutti</button>'
        )
        for sp in sports:
            label = SPORT_LABELS.get(sp, sp)
            parts.append(
                f'<button class="filter-btn" onclick="filterSport(\'{esc(sp)}\')">'
                f'{esc(label)}</button>'
            )
        parts.append("</div>")

    parts.append('<div class="events-grid">')

    now_ts = int(now.timestamp() * 1000)

    for ev in events:
        links = ev["links"]
        is_live = ev["timestamp"] <= now_ts

        if len(links) == 1:
            links_html = (
                f'<a href="{esc(links[0]["url"])}" target="_blank" '
                f'class="server-link">▶ GUARDA — {esc(links[0]["name"])}</a>'
            )
        elif len(links) > 1:
            options = "".join(
                f'<option value="{esc(l["url"])}">{esc(l["name"])}</option>'
                for l in links
            )
            links_html = (
                '<div class="dropdown">'
                '<select onchange="if(this.value)window.open(this.value,\'_blank\');'
                ' this.selectedIndex=0;">'
                '<option value="">📡 Scegli il server...</option>'
                f'{options}'
                '</select></div>'
            )
        else:
            links_html = '<span class="no-link">Nessun server</span>'

        live_class = " live" if is_live else ""
        live_badge = '<span class="status-live-badge">🔴 LIVE</span>' if is_live else ""

        parts.append(
            f'<div class="event-card{live_class}" data-sport="{esc(ev["sport"])}">'
            '<div class="event-info">'
            f'<h3>{esc(ev["title"])}{live_badge}</h3>'
            f'<p class="competition">🏆 {esc(ev["sport_label"])}</p>'
            f'<p class="datetime">🕒 {esc(ev["time"])}</p>'
            f'<span class="badge">📡 {len(links)} server</span>'
            '</div>'
            f'<div class="event-links">{links_html}</div>'
            '</div>'
        )

    parts.append("</div>")
    parts.append(
        '<footer class="footer">'
        f'KIRA GATE • {now.strftime("%d/%m/%Y %H:%M")} • '
        f'{len(events)} eventi</footer>'
    )
    parts.append("</div>")
    parts.append(f"<script>{JS}</script>")
    parts.append("</body></html>")
    return "".join(parts)


# ==================================================================
# 4. M3U
# ==================================================================
def build_m3u(events: list[dict]) -> str:
    lines = ["#EXTM3U"]
    for ev in events:
        group = ev["sport_label"]
        for link in ev["links"]:
            title = f"{ev['title']} [{link['name']}]"
            lines.append(f'#EXTINF:-1 group-title="{group}",{title}')
            lines.append(link["url"])
    return "\n".join(lines)


# ==================================================================
# 5. ENTRY POINT (chiamabile da wrapper)
# ==================================================================
def run():
    """Esegue la pipeline completa e scrive i due file in output/."""
    print(f"→ Output dir: {OUTPUT_DIR}\n")

    raw = fetch_all()
    if not raw:
        print("✘ Nessun evento ricevuto")
        return

    events = normalize(raw)
    events = filter_today(events)
    events = sort_events(events)

    print(f"  ✔ {len(events)} eventi di oggi\n")

    OUTPUT_HTML.write_text(build_html(events), encoding="utf-8")
    print(f"✔ HTML: {OUTPUT_HTML}")

    OUTPUT_M3U.write_text(build_m3u(events), encoding="utf-8")
    print(f"✔ M3U:  {OUTPUT_M3U}")


if __name__ == "__main__":
    run()