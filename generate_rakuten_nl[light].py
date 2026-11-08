#!/usr/bin/env python3

import argparse
import gzip
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

CHANNEL_IDS = [
    "your-60-s-nl",
    "your-70-s-nl",
    "your-80-s-nl",
    "tmf-nl",
]

BASE_URL = "https://gizmo.rakuten.tv/v3/live_channels/{channel_id}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://rakuten.tv",
    "Referer": "https://rakuten.tv/",
}

BLOCK_DAYS = 3
TZ_ROME_OFFSET_HOURS = 2


def iso_to_xmltv(iso_string):
    dt = datetime.fromisoformat(iso_string)
    offset = dt.strftime("%z")
    return dt.strftime("%Y%m%d%H%M%S") + " " + offset


def daterange_blocks(total_days, block_days):
    now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    blocks = []
    cursor = now
    remaining = total_days
    while remaining > 0:
        span = min(block_days, remaining)
        block_end = cursor + timedelta(days=span)
        blocks.append((cursor, block_end))
        cursor = block_end
        remaining -= span
    return blocks


def fetch_channel_block(channel_id, starts_at, ends_at):
    duration_minutes = int((ends_at - starts_at).total_seconds() // 60)
    date_fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    params = {
        "device_identifier": "web",
        "device_stream_audio_quality": "2.0",
        "device_stream_hdr_type": "NONE",
        "device_stream_video_quality": "HD",
        "epg_duration_minutes": str(duration_minutes),
        "epg_starts_at": starts_at.strftime(date_fmt),
        "epg_starts_at_timestamp": str(int(starts_at.timestamp())),
        "epg_ends_at": ends_at.strftime(date_fmt),
        "epg_ends_at_timestamp": str(int(ends_at.timestamp())),
        "locale": "nl",
        "market_code": "nl",
    }
    url = BASE_URL.format(channel_id=channel_id) + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw_body = resp.read()
            content_encoding = resp.headers.get("Content-Encoding", "")
        try:
            if content_encoding == "gzip":
                raw_body = gzip.decompress(raw_body)
            elif content_encoding == "deflate":
                raw_body = zlib.decompress(raw_body)
        except OSError as e:
            print(f"  Dekompressionsfehler ({content_encoding}) für {channel_id}: {e}", file=sys.stderr)
            return None
        body = raw_body.decode("utf-8")
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")[:300]
        except Exception:
            pass
        print(f"  ⚠️  HTTP {e.code} für {channel_id} [{starts_at.date()} → {ends_at.date()}] — {error_body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  ⚠️  Netzwerkfehler bei {channel_id}: {e}", file=sys.stderr)
        return None
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        print(f"  ⚠️  Keine JSON-Antwort für {channel_id}", file=sys.stderr)
        return None
    if "error" in payload:
        err_type = payload["error"].get("type", "sconosciuto")
        print(f"  ⚠️  API-Fehler für {channel_id}: {err_type}", file=sys.stderr)
        return None
    data = payload.get("data")
    if not data or not data.get("id"):
        return None
    return data


def fetch_channel_full(channel_id, total_days):
    print(f"→ {channel_id}")
    title = None
    logo = None
    programs = []
    seen_program_keys = set()
    for starts_at, ends_at in daterange_blocks(total_days, BLOCK_DAYS):
        data = fetch_channel_block(channel_id, starts_at, ends_at)
        time.sleep(0.4)
        if not data:
            continue
        if title is None:
            title = data.get("title", channel_id)
            logo = (data.get("images") or {}).get("artwork")
        for prog in data.get("live_programs", []):
            key = (prog.get("starts_at"), prog.get("title"))
            if key in seen_program_keys:
                continue
            seen_program_keys.add(key)
            programs.append(prog)
    programs.sort(key=lambda p: p.get("starts_at", ""))
    return {"id": channel_id, "title": title or channel_id, "logo": logo, "programs": programs}


def build_xmltv(channels):
    lines = []
    lines.append("<?xml version='1.0' encoding='utf-8'?>")
    lines.append('<tv generator-info-name="Fellfresse" generator-info="EPG/RakutenTV-NL[light]">')
    for ch in channels:
        lines.append(f'  <channel id="{escape(ch["id"])}">')
        lines.append(f'    <display-name lang="nl">{escape(ch["title"])}</display-name>')
        if ch["logo"]:
            lines.append(f'    <icon src="{escape(ch["logo"])}"></icon>')
        lines.append("  </channel>")
    for ch in channels:
        for prog in ch["programs"]:
            starts_raw = prog.get("starts_at")
            ends_raw = prog.get("ends_at")
            if not starts_raw or not ends_raw:
                continue
            try:
                start_xmltv = iso_to_xmltv(starts_raw)
                stop_xmltv = iso_to_xmltv(ends_raw)
            except ValueError:
                continue
            title = escape(prog.get("title") or "")
            desc = escape(prog.get("description") or "")
            lines.append(f'  <programme start="{start_xmltv}" stop="{stop_xmltv}" channel="{escape(ch["id"])}">')
            lines.append(f'    <title lang="nl">{title}</title>')
            if desc:
                lines.append(f'    <desc lang="nl">{desc}</desc>')
            lines.append("  </programme>")
    lines.append("</tv>")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Erstellt EPG im XMLTV-Format für einige Rakuten TV NL Sender")
    parser.add_argument("--days", type=int, default=3, help="Nachzuholende Programmiertage (default: 3)")
    parser.add_argument("--out", default="epg_Rakuten_NL[light].xml", help="Datei Ausgabe (default: epg_Rakuten_NL[light])")
    parser.add_argument("--channels", nargs="*", default=None, help="Überschreiben der Kanalliste (slug)")
    args = parser.parse_args()
    channel_ids = args.channels or CHANNEL_IDS
    print(f" ...generiere EPG für {len(channel_ids)} Sender, {args.days} Tage...")
    channels_data = []
    for channel_id in channel_ids:
        channels_data.append(fetch_channel_full(channel_id, args.days))
    xml_content = build_xmltv(channels_data)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(xml_content)
    total_programs = sum(len(c["programs"]) for c in channels_data)
    print(f"\n✅ Geschrieben {args.out}: {len(channels_data)} Sender, {total_programs} Sendungen insgesamt.")


if __name__ == "__main__":
    main()
