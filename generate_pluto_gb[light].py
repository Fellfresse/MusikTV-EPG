#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

CHANNEL_IDS = {
    "69c3c6c912e978ee49277dc7": "that-s-60s",
}

BASE_URL = "https://api.pluto.tv/v2/channels"
BLOCK_HOURS = 12  # 12-Stunden-Abschnitte, um das versteckte API-Limit zu umgehen
#BLOCK_HOURS = 24


def get_time_blocks(total_hours, block_hours):
    now = datetime.now(timezone.utc)
    # Wir gehen 6 Stunden zurück, um die Sendung zu erfassen, die bereits läuft
    cursor = now - timedelta(hours=6)
    end_target = now + timedelta(hours=total_hours)
    blocks = []

    while cursor < end_target:
        block_end = cursor + timedelta(hours=block_hours)
        if block_end > end_target:
            block_end = end_target
        blocks.append((cursor, block_end))
        cursor = block_end
    return blocks


def fetch_all_channels_chunked(total_hours):
#    print(f"Nachholung des Programms in {BLOCK_HOURS}h-Blöcken, insgesamt {total_hours}h Stunden...")
    all_channels_data = {}

    for start_time, end_time in get_time_blocks(total_hours, BLOCK_HOURS):
        date_fmt = "%Y-%m-%dT%H:%M:%S.000Z"
        params = {
            "start": start_time.strftime(date_fmt),
            "stop": end_time.strftime(date_fmt),
            "appVersion": "5.41.0",
            "deviceMake": "Chrome",
            "deviceModel": "Chrome",
            "deviceType": "web",
            "clientID": "pluto-epg-generator",
            "serverSideAds": "false"
        }
        url = BASE_URL + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "X-Forwarded-For": "185.199.220.58"
        })

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
            channels = json.loads(body)

            for ch in channels:
                ch_id = ch.get("_id")
                if ch_id not in all_channels_data:
                    all_channels_data[ch_id] = {
                        "name": ch.get("name"),
                        "logo": (ch.get("colorLogoPNG") or {}).get("path") or (ch.get("logo") or {}).get("path"),
                        "timelines": []
                    }

                # Füge Sendungen hinzu und vermeide dabei Duplikate basierend auf der Startzeit
                existing_starts = {prog["start"] for prog in all_channels_data[ch_id]["timelines"]}
                for prog in ch.get("timelines", []):
                    if prog.get("start") not in existing_starts:
                        all_channels_data[ch_id]["timelines"].append(prog)
                        existing_starts.add(prog.get("start"))

        except urllib.error.HTTPError as e:
            print(f"⚠️  HTTP {e.code} Fehler {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}",
                  file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Netzwerkfehler: {e}", file=sys.stderr)

    return all_channels_data


def iso_to_xmltv(iso_string):
    # Liest die UTC-Zeit aus der API aus
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    # Explizit in deutsche Zeit umrechnen (UTC+2)
    dt_de = dt + timedelta(hours=2)
    # Gibt das Format mit fester deutscher Zeitzone zurück
    return dt_de.strftime("%Y%m%d%H%M%S +0200")


def build_xmltv(channels_data):
    lines = []
    lines.append("<?xml version='1.0' encoding='utf-8'?>")
    lines.append('<tv generator-info-name="Fellfresse" generator-info="Pluto TV GB EPG Light">')

    for ch in channels_data:
        lines.append(f'  <channel id="{escape(ch["xmltv_id"])}">')
        lines.append(f'    <display-name lang="en">{escape(ch["title"])}</display-name>')
        if ch["logo"]:
            lines.append(f'    <icon src="{escape(ch["logo"])}"></icon>')
        lines.append("  </channel>")

    for ch in channels_data:
        # Grundlegende chronologische Sortierung
        sorted_programs = sorted(ch["programs"], key=lambda p: p.get("start", ""))

        for prog in sorted_programs:
            try:
                start_xmltv = iso_to_xmltv(prog["start"])
                stop_xmltv = iso_to_xmltv(prog["stop"])
            except (ValueError, KeyError):
                continue

            title = escape(prog.get("title") or "")
            desc = escape((prog.get("episode") or {}).get("description") or "")

            lines.append(f'  <programme start="{start_xmltv}" stop="{stop_xmltv}" channel="{escape(ch["xmltv_id"])}">')
            lines.append(f'    <title lang="en">{title}</title>')
            if desc:
                lines.append(f'    <desc lang="en">{desc}</desc>')
            lines.append("  </programme>")

    lines.append("</tv>")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Erstellt EPG im XMLTV-Format für Pluto TV GB")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--out", default="epg_Pluto_GB[light].xml")
    args = parser.parse_args()

    print(f"Starte EPG-Generierung [Pluto TV GB] für {args.hours} Stunden...\n")
    raw_channels = fetch_all_channels_chunked(args.hours)

    channels_data = []
    for pluto_id, xmltv_id in CHANNEL_IDS.items():
        ch = raw_channels.get(pluto_id)
        if not ch:
            print(f"⚠️  Kanal nicht gefunden: {pluto_id}")
            continue

        channels_data.append({
            "xmltv_id": xmltv_id,
            "title": ch.get("name", xmltv_id),
            "logo": ch.get("logo"),
            "programs": ch.get("timelines", [])
        })
        print(f"→ {ch.get('name')}: {len(ch.get('timelines', []))} Programme")

    xml_content = build_xmltv(channels_data)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(xml_content)

    total_programs = sum(len(c["programs"]) for c in channels_data)
    print(f"\n✅ EPG geschrieben in {args.out}: {len(channels_data)} [Sender, {total_programs} Programme]")


if __name__ == "__main__":
    main()
