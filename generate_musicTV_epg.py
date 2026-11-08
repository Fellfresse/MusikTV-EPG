#!/usr/bin/env python3
import argparse
import gzip
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

SAM_URL = "https://github.com/matthuisman/i.mjh.nz/raw/refs/heads/master/SamsungTVPlus/all.xml.gz"

ID_TRANSLATION = {
    "DE2500001DO": "Cool Summer Channel",
    "GBBC19000017V": "Vevo Pop [UK]",
    "GBBD1900009UD": "Vevo 70s-80s [UK]",
    "GBBC2100002HP": "Vevo 90s-00s [UK]",
    "GBBD2300001C0": "Vevo Hip Hop-R-B [UK]",
    "GBBD3000004VR": "Def Jam",
    "FRBC2100001YY": "Vevo Pop [FR]",
    "FRBD1900013CB": "Vevo Rétro [FR]",
    "FRBC2100002JA": "Vevo Hip Hop-R-B [FR]",
    "ESBC2100001IU": "Vevo Pop [ES]",
    "ESBD230000289": "Vevo Retro [ES]",
    "ESBC2100002LV": "Vevo Latino [ES]",
    "ITBC2100001G9": "Vevo Pop [IT]",
    "ITBD1900010JL": "Vevo 70s-80s [IT]",
    "ITBC210000200": "Vevo 90s-00s [IT]",
    "ITBC1100011RK": "Rock TV [IT]",
    "IT500006GE": "70-80.it",
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
        print(f"⚠️  HTTP {e.code} beim herunterladen epg_sam", file=sys.stderr)
        return [], []
    except Exception as e:
        print(f"⚠️  Netzwerkfehler beim Herunterladen epg_sam: {e}", file=sys.stderr)
        return [], []

    # Überprüfe, ob die Datei komprimiert (gzip) ist oder ob es sich um reines XML handelt
    if raw_data.startswith(b'\x1f\x8b'):
        try:
            xml_bytes = gzip.decompress(raw_data)
        except OSError as e:
            print(f"⚠️  Fehler bei der Dekomprimierung epg_sam: {e}", file=sys.stderr)
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
        clean_id = raw_id.strip()
        
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

    print(f"→ epg_sam: {len(channels)} Sender, {len(programmes)} Programme")
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
    parser = argparse.ArgumentParser(description="Führt die EPGs zusammen")
    parser.add_argument("--pluto_ca", default="epg_Pluto_CA[light].xml")
    parser.add_argument("--pluto_br", default="epg_Pluto_BR[light].xml")
    parser.add_argument("--pluto_gb", default="epg_Pluto_GB[light].xml")
    parser.add_argument("--pluto_us", default="epg_Pluto_US[light].xml")
    parser.add_argument("--plex_mjh", default="epg_Plex.mjh[light].xml")
    parser.add_argument("--plex_fell", default="epg_Plex.fellfresse[light].xml")
    parser.add_argument("--rakuten_de", default="epg_Rakuten_DE[light].xml")
    parser.add_argument("--rakuten_nl", default="epg_Rakuten_NL[light].xml")
    parser.add_argument("--epgshare_ca", default="epg_Share_CA[light].xml")
    parser.add_argument("--zattoo_at", default="epg_Zattoo_AT[light].xml")
    parser.add_argument("--zattoo_ch", default="epg_Zattoo_CH[light].xml")
    parser.add_argument("--open_de", default="epg_OpenDE[light].xml")
    parser.add_argument("--open_fr", default="epg_OpenFR[light].xml")
    parser.add_argument("--vantage", default="epg_Vantage[light].xml")
    parser.add_argument("--musikbox", default="epg_Musikbox[light].xml")

    parser.add_argument("--skip-sam", action="store_true")
    parser.add_argument("--out", default="EPG_MusikTV.xml")
    args = parser.parse_args()
    
    all_channels = []
    all_programmes = []
    
    # Liste der zu verarbeitenden Dateien
    for label, path in [
    ("Pluto_CA", args.pluto_ca), 
    ("Pluto_BR", args.pluto_br), 
    ("Pluto_GB", args.pluto_gb), 
    ("Pluto_US", args.pluto_us), 
    ("Plex_MJH", args.plex_mjh),
    ("Plex_Fell", args.plex_fell),
    ("Rakuten_DE", args.rakuten_de),
    ("Rakuten_NL", args.rakuten_nl),
    ("EPG_Share_CA", args.epgshare_ca),
    ("Zattoo_AT", args.zattoo_at),
    ("Zattoo_CH", args.zattoo_ch),
    ("OpenDE", args.open_de),
    ("OpenFR", args.open_fr),
    ("Vantage", args.vantage),
    ("MusikBox", args.musikbox)
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
        
    root = ET.Element("tv", {"generator-info-name": "Fellfresse", "generator-info": "MusikTV-EPG"})
    for ch in deduped_channels:
        root.append(ch)
    for pr in all_programmes:
        root.append(pr)
        
    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    tree.write(args.out, encoding="utf-8", xml_declaration=True)
    print(f"\n✅ Erzeuge {args.out}: {len(deduped_channels)} Sender, {len(all_programmes)} Programme total")


if __name__ == "__main__":
    main()
