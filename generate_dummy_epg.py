import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_dummy_channel_epg():
    # Configuration
    channels = [
        {"id": "V2BEAT", "name": "V2BEAT", "title": "Pop & Dance Video-Hits", "desc": "V2BEAT Music TV ist ein unabhängiger Pop- und Tanz-Videokanal weltweit"},
        {"id": "RadioU", "name": "RadioU", "title": "Alternative Musik", "desc": "RadioU Live TV kombiniert alternative Rock-, Metal- und Hip-Hop-Musikvideos mit Interviews und Studiobeiträgen."},
        {"id": "TV Rock Brasilien", "name": "TV Rock Brasilien", "title": "Rock und Real Metal", "desc": "TV Rock Brazil Live-Highlights Heavy Guitars und Rock- und Metal-Künstler in ihrer musikalischen Auswahl."},
        {"id": "MiamiTV Music", "name": "Miami TV Music", "title": "Musikprogramm", "desc": "Miami TV Music ist ein Unterhaltungskanal im Miami TV FAST-Netzwerk, der eine Vielzahl von Musikgenres 24/7 bietet, darunter Pop, Rock, Latin-Hits, elektronische Mixe und Live-Auftritte für nonstop musikalische Unterhaltung."},
        {"id": "MiamiTV DJ", "name": "MiamiTV DJ", "title": "Musikprogramm", "desc": "Miami TV DJ ist ein 24/7 Musikkanal des Miami TV-Netzwerks, der kontinuierliche elektronische Tanzmusikmixe von DJs weltweit anbietet und sich auf Nonstop-EDM-, House- und Club-Beats konzentriert."},
        {"id": "Totalmusic", "name": "Totalmusic", "title": "Videoclips", "desc": "24/7 Musikkanal mit Videoclips aller Genres, die klassische und aktuelle Hits kombinieren, ideal als musikalisches Hauptsignal am Raster. Höher oben, auf dieser Seite, ist die heutige Programmierung auf Ihrer lokalen Zeit und was jetzt auf Sendung ist."},
   ]
    
    filename = "epg_Dummy.xml"
    
    # Create XML Root
    tv = ET.Element('tv', {"generator-info-name": "Fellfresse", "generator-info": "dummy_epg"})
    
    # Add Channel Definitions with Logos
    for ch in channels:
        chan_elem = ET.SubElement(tv, 'channel', id=ch["id"])
        ET.SubElement(chan_elem, 'display-name').text = ch["name"]

    # Generate Programming
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    base_start = now_utc.replace(minute=0, second=0, microsecond=0)
    
    for ch in channels:
            # Generates 48 blocks of 1 hour each using the channel name
            for i in range(48):
                prog_start = base_start + datetime.timedelta(hours=i)
                prog_stop = prog_start + datetime.timedelta(hours=1)
                start_str = prog_start.strftime('%Y%m%d%H%M%S +0000')
                stop_str = prog_stop.strftime('%Y%m%d%H%M%S +0000')
                
                prog = ET.SubElement(tv, 'programme', start=start_str, stop=stop_str, channel=ch["id"])
                ET.SubElement(prog, 'title', lang="de").text = ch['title']
                ET.SubElement(prog, 'desc', lang="de").text = ch['desc']

    # Format and Save XML
    xml_string = ET.tostring(tv, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="  ")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
        
    print(f"\n✅ {filename} erfolgreich mit 1-Stunden-Beschriftungen erstellt")

if __name__ == "__main__":
    generate_dummy_channel_epg()
