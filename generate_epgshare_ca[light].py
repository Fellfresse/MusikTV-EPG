#!/usr/bin/env python3
import argparse
import gzip
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

EPGshareCA_URL = "https://epgshare01.online/epgshare01/epg_ripper_CA2.xml.gz"

ID_TRANSLATION = {
    "Stingray.Jukebox.Oldies.ca2": "Stingray Jukebox Oldies",
    "Stingray.Souvenirs.ca2": "Stingray Souvenirs",
    "Stingray.Le.Palmarès.ca2": "Stingray le Palmares",
    "Stingray.Nostalgie.ca2": "Stingray Nostalgie",
    "Stingray.Franco.Country.ca2": "Stingray Franco Country",
    "Stingray.Franco.Pop.ca2": "Stingray Franco Pop",
    "Stingray.Franco.Retro.ca2": "Stingray Franco Retro",
    "TikTok.Radio.on.Stingray.ca2": "Stingray TikTok Radio",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


def fetch_EPGshareCA_filtered():
    req = urllib.request.Request(EPGshareCA_URL, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_data = resp.read()
    except urllib.error.HTTPError as e:
        print(f"⚠️  HTTP {e.code} beim Herunterladen EPGshareCA", file=sys.stderr)
        return [], []
    except Exception as e:
        print(f"⚠️  Netzwerkfehler beim Herunterladen EPGshareCA: {e}", file=sys.stderr)
        return [], []

    # Überprüft, ob die Datei komprimiert (gzip) ist oder ob es sich um reines XML handelt
    if raw_data.startswith(b'\x1f\x8b'):
        try:
            xml_bytes = gzip.decompress(raw_data)
        except OSError as e:
            print(f"⚠️  Fehler bei der Dekomprimierung EPGshareCA: {e}", file=sys.stderr)
            return [], []
    else:
        xml_bytes = raw_data

    root = ET.fromstring(xml_bytes)

    channels = []
    programmes = []
    valid_new_ids = set(ID_TRANSLATION.keys())

    # 1. Kanäle entwickeln
    for ch in root.findall("channel"):
        raw_id = ch.get("id")
        if raw_id is None: continue
        clean_id = raw_id.strip()  # Entfernt Leerzeichen von EPGshareCA

        if clean_id in valid_new_ids:
            old_id = ID_TRANSLATION[clean_id]  # Übersetzt in die alte ID
            ch.set("id", old_id)
            channels.append(ch)

    # 2. Programme erarbeiten
    for pr in root.findall("programme"):
        raw_id = pr.get("channel")
        if raw_id is None: continue
        clean_id = raw_id.strip()  # Entfernt Leerzeichen

        if clean_id in valid_new_ids:
            old_id = ID_TRANSLATION[clean_id]  # Übersetzt in die alte ID
            pr.set("channel", old_id)
            programmes.append(pr)

    print(f"→ EPGshareCA EPG: {len(channels)} Sender, {len(programmes)} Programme (gefiltert)")
    return channels, programmes

def parse_local_xmltv(path):
    try:
        tree = ET.parse(path)
    except (FileNotFoundError, ET.ParseError) as e:
        print(f"⚠️  Nicht lesbar {path}: {e}", file=sys.stderr)
        return [], []
    root = tree.getroot()
    channels = root.findall("channel")
    programmes = root.findall("programme")
    print(f"→ {path}: {len(channels)} Sender, {len(programmes)} Programme")
    return channels, programmes


def main():
    parser = argparse.ArgumentParser(description="gefilterte Datei")
    parser.add_argument("--skip-EPGshareCA", action="store_true")
    parser.add_argument("--out", default="epg_Share_CA[light].xml")
    args = parser.parse_args()

    all_channels = []
    all_programmes = []

    for label, path in [
    ]:
        ch, pr = parse_local_xmltv(path)
        all_channels.extend(ch)
        all_programmes.extend(pr)

    if not args.skip_EPGshareCA:
        ch, pr = fetch_EPGshareCA_filtered()
        all_channels.extend(ch)
        all_programmes.extend(pr)

    seen_channel_ids = set()
    deduped_channels = []
    for ch in all_channels:
        cid = ch.get("id")
        if cid in seen_channel_ids:
            continue
        seen_channel_ids.add(cid)
        deduped_channels.append(ch)

    root = ET.Element("tv", {"generator-info-name": "Fellfresse", "generator-info": "epg_Share_CA[light]_epg"})
    for ch in deduped_channels:
        root.append(ch)
    for pr in all_programmes:
        root.append(pr)

    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    tree.write(args.out, encoding="utf-8", xml_declaration=True)
    print(f"\n✅ Geschrieben: {args.out} [{len(deduped_channels)} Sender, {len(all_programmes)} Programme] ")


if __name__ == "__main__":
    main()