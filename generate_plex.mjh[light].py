#!/usr/bin/env python3
import argparse
import gzip
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

Plex2_URL = "https://github.com/matthuisman/i.mjh.nz/raw/refs/heads/master/Plex/all.xml.gz"

ID_TRANSLATION = {
    "64305451fc3be5947773c339-68965bb7e4a79cd0c3f845d8": "XITE Hits [UK]",
    "647f8d22a2fc3fadb4721685-688945673b7708975e7c07e5": "XITE Country Today [CA]",
    "647f8d22a2fc3fadb4721685-688d399a8ceaa3681d9425d3": "XITE Classic Country [CA]",
    "647f8d22a2fc3fadb4721685-68800926996f1a2fb393a6e7": "XITE XITE R-B Classic Jams [CA]",
    "647f8d22a2fc3fadb4721685-62fbf197c67d52bddf74cc87": "Movie Music by Stingray",
    "6a1610bebdf296985fd95603-688002cd996f1a2fb393a6e3": "XITE Hits [US]",
    "6a1610bebdf296985fd95603-688005bc015fe7e375a1a0aa": "XITE 60s - 70s Groove [US]",
    "6a1610bebdf296985fd95603-688006e7015fe7e375a1a0ac": "XITE 80s Flashback [US]",
    "6a1610bebdf296985fd95603-6889430a3b7708975e7c07e3": "XITE 90s Throwback [US]",
    "6a1610bebdf296985fd95603-68800806996f1a2fb393a6e5": "XITE Rock X Metal [US]",
    "6a1610bebdf296985fd95603-6889467267ddc0ef2cdbf4ff": "XITE Just Chill [US]",
    "6a1610bebdf296985fd95603-68894a9267ddc0ef2cdbf503": "XITE Celebrates [US]",
    "6a1610bebdf296985fd95603-6889479e67ddc0ef2cdbf501": "XITE Nuevo Latino [US]",
    "6a1610bebdf296985fd95603-68800a594033a6a442ad9237": "XITE Siempre Latino [US]",
    "6a1610bebdf296985fd95603-68800c6c4033a6a442ad923b": "XITE R-B Feels [US]",
    "6a1610bebdf296985fd95603-68894b6e10df0c242e4136cc": "XITE Hip-Hop Evolution [US]",
    "6a1610bebdf296985fd95603-68800b694033a6a442ad9239": "XITE Rap Game [US]",
    "6a1610bebdf296985fd95603-5fe27da28c198b002d179199": "Qello Concerts by Stingray",
    "6a1610bebdf296985fd95603-5fc705daa2236e002d69f108": "Stingray Karaoke",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

def fetch_plex2_filtered():
    req = urllib.request.Request(Plex2_URL, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_data = resp.read()
    except urllib.error.HTTPError as e:
        print(f"⚠️  HTTP {e.code} beim Herunterladen plex i.mjh.nz", file=sys.stderr)
        return [], []
    except Exception as e:
        print(f"⚠️  Netzwerkfehler beim Herunterladen plex i.mjh.nz: {e}", file=sys.stderr)
        return [], []

    # Überprüft, ob die Datei komprimiert (gzip) ist oder ob es sich um reines XML handelt
    if raw_data.startswith(b'\x1f\x8b'):
        try:
            xml_bytes = gzip.decompress(raw_data)
        except OSError as e:
            print(f"⚠️  Fehler bei der Dekomprimierung plex i.mjh.nz: {e}", file=sys.stderr)
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
        clean_id = raw_id.strip() # Entfernt Leerzeichen von i.mjh.nz
        
        if clean_id in valid_new_ids:
            old_id = ID_TRANSLATION[clean_id] # Übersetzt in die alte ID
            ch.set("id", old_id) 
            channels.append(ch)
            
    # 2. Programme erarbeiten
    for pr in root.findall("programme"):
        raw_id = pr.get("channel")
        if raw_id is None: continue
        clean_id = raw_id.strip() # Entfernt Leerzeichen
        
        if clean_id in valid_new_ids:
            old_id = ID_TRANSLATION[clean_id] # Übersetzt in die alte ID
            pr.set("channel", old_id)
            programmes.append(pr)

    print(f"→ Plex2 EPG: {len(channels)} Sender, {len(programmes)} Programme (gefiltert)")
    return channels, programmes

# ... (Lasse ab hier den gesamten Rest deines Skripts unverändert: parse_local_xmltv und main) ...


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
    parser.add_argument("--skip-plex2", action="store_true")
    parser.add_argument("--out", default="epg_Plex.mjh[light].xml")
    args = parser.parse_args()
    
    all_channels = []
    all_programmes = []
    
    for label, path in [
    ]:
        ch, pr = parse_local_xmltv(path)
        all_channels.extend(ch)
        all_programmes.extend(pr)
        
    if not args.skip_plex2:
        ch, pr = fetch_plex2_filtered()
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
        
    root = ET.Element("tv", {"generator-info-name": "Fellfresse", "generator-info": "Plex.mjh[light]_epg"})
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
