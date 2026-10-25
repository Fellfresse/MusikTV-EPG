#!/usr/bin/env python3
import argparse
import gzip
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

SAM_URL = "https://github.com/matthuisman/i.mjh.nz/raw/refs/heads/master/SamsungTVPlus/all.xml.gz"

ID_TRANSLATION = {
    "GBBB3800005QO": "GBBB3800005QO",
    "USBD3300004RH": "USBD3300004RH",
    "USBB320000647": "USBB320000647",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

def fetch_sam_filtered():
    req = urllib.request.Request(SAM_URL, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_data = resp.read()
    except urllib.error.HTTPError as e:
        print(f"⚠️  HTTP {e.code} beim Herunterladen i.mjh.nz", file=sys.stderr)
        return [], []
    except Exception as e:
        print(f"⚠️  Netzwerkfehler beim Herunterladen i.mjh.nz: {e}", file=sys.stderr)
        return [], []

    # Überprüft, ob die Datei komprimiert (gzip) ist oder ob es sich um reines XML handelt
    if raw_data.startswith(b'\x1f\x8b'):
        try:
            xml_bytes = gzip.decompress(raw_data)
        except OSError as e:
            print(f"⚠️  Fehler bei der Dekomprimierung i.mjh.nz: {e}", file=sys.stderr)
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

    print(f"→ Samsung EPG: {len(channels)} Sender, {len(programmes)} Programme (gefiltert)")
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
    parser.add_argument("--skip-sam", action="store_true")
    parser.add_argument("--out", default="epg_samsung[light].xml")
    args = parser.parse_args()
    
    all_channels = []
    all_programmes = []
    
    for label, path in [
    ]:
        ch, pr = parse_local_xmltv(path)
        all_channels.extend(ch)
        all_programmes.extend(pr)
        
    if not args.skip_sam:
        ch, pr = fetch_sam_filtered()
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
        
    root = ET.Element("tv", {"generator-info-name": "Fellfresse", "generator-info": "Samsung[light]_epg"})
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
