#!/usr/bin/env python3
"""
Genera un HTML autonomo dalla guida EPG.
Uso:
  python scripts/personali/genera-html-epg.py output/epg-it.xml
  python scripts/personali/genera-html-epg.py output/epg-it.xml templates/epg-template.html output/guida-tv.html
"""
import sys
import os
import json
import re
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree as ET

DEFAULT_TEMPLATE = "template/epg-template.html"

def parse_epg_date(s):
    if not s:
        return None
    parts = s.strip().split()
    d = parts[0]
    tz = parts[1] if len(parts) > 1 else '+0000'
    if len(d) < 14:
        return None
    year = int(d[0:4]); month = int(d[4:6]); day = int(d[6:8])
    hour = int(d[8:10]); minute = int(d[10:12]); second = int(d[12:14])
    m = re.match(r'([+-])(\d{2})(\d{2})', tz)
    offset_min = 0
    if m:
        sign = -1 if m.group(1) == '-' else 1
        offset_min = sign * (int(m.group(2)) * 60 + int(m.group(3)))
    dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    return dt - timedelta(minutes=offset_min)

def main():
    if len(sys.argv) < 2:
        print("Uso: genera-html-epg.py <input.xml> [template.html] [output.html]")
        sys.exit(1)

    xml_file = sys.argv[1]
    template_file = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TEMPLATE
    output_file = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
        "output",
        os.path.basename(xml_file).replace('.xml', '-guida.html')
    )

    if not os.path.exists(xml_file):
        print(f"❌ File non trovato: {xml_file}")
        sys.exit(1)
    if not os.path.exists(template_file):
        print(f"❌ Template non trovato: {template_file}")
        sys.exit(1)

    print(f"📖 Leggo {xml_file}")
    tree = ET.parse(xml_file)
    root = tree.getroot()

    channels = {}
    for ch in root.findall('channel'):
        cid = ch.get('id', '')
        name_el = ch.find('display-name')
        name = name_el.text.strip() if name_el is not None and name_el.text else cid
        icon_el = ch.find('icon')
        icon = icon_el.get('src', '') if icon_el is not None else ''
        channels[cid] = {'id': cid, 'name': name, 'icon': icon, 'programmes': []}

    for pr in root.findall('programme'):
        cid = pr.get('channel', '')
        if cid not in channels:
            continue
        start = parse_epg_date(pr.get('start'))
        stop = parse_epg_date(pr.get('stop'))
        if not start or not stop:
            continue
        title_el = pr.find('title')
        desc_el = pr.find('desc')
        ep_el = pr.find('episode-num')
        date_el = pr.find('date')
        cats = [c.text.strip() for c in pr.findall('category') if c.text and c.text.strip()]
        credits = {}
        cred_el = pr.find('credits')
        if cred_el is not None:
            dirs = [d.text.strip() for d in cred_el.findall('director') if d.text and d.text.strip()]
            if dirs:
                credits['director'] = dirs
        channels[cid]['programmes'].append({
            'start': start.isoformat(),
            'stop': stop.isoformat(),
            'title': title_el.text.strip() if title_el is not None and title_el.text else '',
            'desc': desc_el.text.strip() if desc_el is not None and desc_el.text else '',
            'episodeNum': ep_el.text.strip() if ep_el is not None and ep_el.text else '',
            'date': date_el.text.strip() if date_el is not None and date_el.text else '',
            'categories': cats,
            'credits': credits,
            'isNew': pr.find('new') is not None,
            'isLive': pr.find('live') is not None
        })

    channels_list = sorted(channels.values(), key=lambda c: c['name'].lower())
    for ch in channels_list:
        ch['programmes'].sort(key=lambda p: p['start'])

    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    channels_out = []
    for ch in channels_list:
        progs = []
        for p in ch['programmes']:
            ps = datetime.fromisoformat(p['start'])
            pe = datetime.fromisoformat(p['stop'])
            if ps < tomorrow and pe > today:
                progs.append(p)
        if progs:
            channels_out.append({
                'id': ch['id'],
                'name': ch['name'],
                'icon': ch['icon'],
                'programmes': progs
            })

    payload = {
        'date': today.isoformat(),
        'dateLabel': today.strftime('%A %d %B %Y'),
        'dateShort': today.strftime('%d/%m/%Y'),
        'channels': channels_out
    }

    payload_json = json.dumps(payload, ensure_ascii=False)
    payload_json = payload_json.replace('</script', '<\\/script')

    with open(template_file, 'r', encoding='utf-8') as f:
        template = f.read()

    html = template.replace('/*__DATA__*/', payload_json)

    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Generato {output_file}")
    print(f"   Canali: {len(channels_out)}")
    print(f"   Programmi oggi: {sum(len(c['programmes']) for c in channels_out)}")

if __name__ == "__main__":
    main()
