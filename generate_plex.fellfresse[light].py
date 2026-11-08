#!/usr/bin/env python3
import argparse
import gzip
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

Plex1_URL = "https://raw.githubusercontent.com/Fellfresse/Plex-EPG/master/epg-de.xml.gz"

ID_TRANSLATION = {
    "635177ecff6cd5445d7f9b0b-68965c76e4a79cd0c3f845da": "XITE Hits [DE]",
    "635177ecff6cd5445d7f9b0b-66be8cd4871131188099527e": "Trace UK",
    "635177ecff6cd5445d7f9b0b-6322658be67cf9cd9011fcda": "Trace Urban",
    "635177ecff6cd5445d7f9b0b-63226c03e67cf9cd9011fcdf": "Trace Latina",
    "635177ecff6cd5445d7f9b0b-6329474265c8569187176338": "Trace Brasil",
    "635177ecff6cd5445d7f9b0b-68e9436dda6bb987138625c7": "Metal.Rocks",
    "635177ecff6cd5445d7f9b0b-62d7f68fb19cbf65dc7bef7c": "Qello Concerts by Stingray [EU]",
    "635177ecff6cd5445d7f9b0b-61aaa014784a2161d3caf7fd": "Stingray Hit List",
    "635177ecff6cd5445d7f9b0b-62ee74af52f7d73061eec491": "Stingray Euro Hits",
    "635177ecff6cd5445d7f9b0b-61aa97d4113e1e5137fd5325": "Stingray Greatest Hits",
    "635177ecff6cd5445d7f9b0b-62ee7992271f393d2d9f709c": "Stingray Pop Adult",
    "635177ecff6cd5445d7f9b0b-62f15810a3ffe928ef806c75": "Stingray Flashback '70s",
    "635177ecff6cd5445d7f9b0b-61aa9f50784a2161d3caf7fb": "Stingray Remember the '80s",
    "635177ecff6cd5445d7f9b0b-62f13eeded056a1db9ef3d54": "Stingray Nothin' But '90s",
    "635177ecff6cd5445d7f9b0b-62ee72cc271f393d2d9f7098": "Stingray Y2K",
    "635177ecff6cd5445d7f9b0b-61aaa0cc784a2161d3caf7ff": "Stingray Classic Rock",
    "635177ecff6cd5445d7f9b0b-62efbb8652f7d73061eec498": "Stingray Alternative",
    "635177ecff6cd5445d7f9b0b-61aa9e73784a2161d3caf7f9": "Stingray Hot Country",
    "635177ecff6cd5445d7f9b0b-61aaa17a784a2161d3caf801": "Stingray Soul Storm",
    "635177ecff6cd5445d7f9b0b-62ee76b5271f393d2d9f709a": "Stingray Easy Listening",
    "635177ecff6cd5445d7f9b0b-62ee7ae2271f393d2d9f709e": "Stingray Hip-Hop'RnB",
    "635177ecff6cd5445d7f9b0b-62efba6588a16bb7d6b6fb58": "Stingray Éxitos del Momento",
    "635177ecff6cd5445d7f9b0b-62ee784852f7d73061eec493": "Stingray Smooth Jazz",
    "635177ecff6cd5445d7f9b0b-62ee6eae271f393d2d9f7096": "Stingray Today's K-Pop",
    "635177ecff6cd5445d7f9b0b-62f11395586633e88e3a3274": "Stingray Spa",
    "635177ecff6cd5445d7f9b0b-654eb862dde2222e8ba551f1": "Stingray Holidayscapes",
    "635177ecff6cd5445d7f9b0b-62d7f6904d0067dd4d60d0de": "Stingray Karaoke [EU]",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

def fetch_plex1_filtered():
    req = urllib.request.Request(Plex1_URL, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_data = resp.read()
    except urllib.error.HTTPError as e:
        print(f"⚠️  HTTP {e.code} beim Herunterladen fellfresse.plex", file=sys.stderr)
        return [], []
    except Exception as e:
        print(f"⚠️  Netzwerkfehler beim Herunterladen fellfresse.plex: {e}", file=sys.stderr)
        return [], []

    # Überprüft, ob die Datei komprimiert (gzip) ist oder ob es sich um reines XML handelt
    if raw_data.startswith(b'\x1f\x8b'):
        try:
            xml_bytes = gzip.decompress(raw_data)
        except OSError as e:
            print(f"⚠️  Fehler bei der Dekomprimierung fellfresse.plex: {e}", file=sys.stderr)
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
        clean_id = raw_id.strip() # Entfernt Leerzeichen von fellfresse.plex
        
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

    print(f"→ Plex DE EPG: {len(channels)} Sender, {len(programmes)} Programme (gefiltert)")
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
    parser.add_argument("--skip-plex1", action="store_true")
    parser.add_argument("--out", default="epg_Plex.fellfresse[light].xml")
    args = parser.parse_args()
    
    all_channels = []
    all_programmes = []
    
    for label, path in [
    ]:
        ch, pr = parse_local_xmltv(path)
        all_channels.extend(ch)
        all_programmes.extend(pr)
        
    if not args.skip_plex1:
        ch, pr = fetch_plex1_filtered()
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
        
    root = ET.Element("tv", {"generator-info-name": "Fellfresse", "generator-info": "Plex.fellfresse[light]_epg"})
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
