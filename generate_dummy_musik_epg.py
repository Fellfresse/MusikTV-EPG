import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_dummy_musik_epg():
    # Configuration
    channels = [
        {"id": "V2BEAT", "name": "V2BEAT", "title": "Pop & Dance Video-Hits", "desc": "V2BEAT Music TV ist ein unabhängiger Pop- und Tanz-Videokanal weltweit"},
        {"id": "TV Rock Brasilien", "name": "TV Rock Brasilien", "title": "Rock und Real Metal", "desc": "TV Rock Brazil Live-Highlights Heavy Guitars und Rock- und Metal-Künstler in ihrer musikalischen Auswahl."},
        {"id": "RadioU TV", "name": "RadioU", "title": "Alternative Musik", "desc": "RadioU Live TV kombiniert alternative Rock-, Metal- und Hip-Hop-Musikvideos mit Interviews und Studiobeiträgen."},
        {"id": "Radio M2O TV", "name": "Radio M2O TV", "title": "Musikalisches Web-TV von Elemedia", "desc": "Videoclips, Club- und DJ-Sets sowie Live-Inhalte rund um Dance, Electronic und House im Livestream."},
        {"id": "MiamiTV Music", "name": "Miami TV Music", "title": "Musikprogramm", "desc": "Miami TV Music ist ein Unterhaltungskanal im Miami TV FAST-Netzwerk, der eine Vielzahl von Musikgenres 24/7 bietet, darunter Pop, Rock, Latin-Hits, elektronische Mixe und Live-Auftritte für nonstop musikalische Unterhaltung."},
        {"id": "MiamiTV DJ", "name": "MiamiTV DJ", "title": "Musikprogramm", "desc": "Miami TV DJ ist ein 24/7 Musikkanal des Miami TV-Netzwerks, der kontinuierliche elektronische Tanzmusikmixe von DJs weltweit anbietet und sich auf Nonstop-EDM-, House- und Club-Beats konzentriert."},
        {"id": "CMC-California Music Channel", "name": "CMC-California Music Channel", "title": "Amerikas #1 lokale Musikvideostation", "desc": "California Music Channel (CMC) ist ein US-amerikanischer Fernsehsender für Musikvideos mit Sitz in der San Francisco Bay Area. Er zählt zu den weltweit am längsten bestehenden lokalen Fernsehsendern für Musikvideos."},
        {"id": "CMC-Country Music Channel", "name": "CMC-Country Music Channel", "title": "Country-Hits und Klassiker", "desc": "CMC-USA ist ein von der CMC Broadcasting Company betriebener Country-Musik-Sender, der Country-Hits und -Klassiker im Video-Jukebox-Format ausstrahlt."},
        {"id": "Dance TV", "name": "Dance TV", "title": "House, Electro, Trap oder Melodic Techno", "desc": "DanceTV ist Europas führende kostenlose 24/7 elektronische Dance-Musik-Streaming-Plattform. DanceTV wurde 2009 in den Niederlanden gegründet und überträgt Live-DJ-Sets, Festival-Streams und kuratierte Musikvideos an Millionen von Zuschauern weltweit über Webbrowser."},
        {"id": "First Music Channel", "name": "First Music Channel", "title": "Videoclips", "desc": "Non-Stop-Musikvideostream mit Schwerpunkt auf populärer Unterhaltungsmusik"},
        {"id": "Totalmusic", "name": "Totalmusic", "title": "Videoclips", "desc": "24/7 Musikkanal mit Videoclips aller Genres, die klassische und aktuelle Hits kombinieren, ideal als musikalisches Hauptsignal am Raster. Höher oben, auf dieser Seite, ist die heutige Programmierung auf Ihrer lokalen Zeit und was jetzt auf Sendung ist."},
        {"id": "Totalmusic 2000s", "name": "Totalmusic 2000s", "title": "Videoclips", "desc": "Musikalisches Signal, das den großen Hits und unterbewerteten Juwelen des neuen Jahrtausendsjahrzehnt gewidmet ist, mit kontinuierlicher Programmierung von ikonischen Videoclips des Jahrzehnts. Höher oben, auf dieser Seite, ist die heutige Programmierung auf Ihrer lokalen Zeit und was jetzt auf Sendung ist."},
        {"id": "Totalmusic 80s", "name": "Totalmusic 80s", "title": "Videoclips", "desc": "Der thematische Kanal konzentrierte sich ausschließlich auf Erfolge und unterbewertete Juwelen des goldenen Jahrzehnts, die sich an nostalgischen und hohen Engagement-Zielgruppen orientieren. Höher oben, auf dieser Seite, ist die heutige Programmierung auf Ihrer lokalen Zeit und was jetzt auf Sendung ist."},
        {"id": "Impact TV Dance", "name": "Impact TV Dance", "title": "Dance-, House- und elektronische Musik", "desc": "Impact Dance liefert dir die angesagtesten Beats und elektronische Musik – nonstop, rund um die Uhr, in HD-Qualität und direkt in deiner Box"},
    ]
    
    filename = "epg_Dummy_Musik.xml"
    
    # Create XML Root
    tv = ET.Element('tv', {"generator-info-name": "Fellfresse", "generator-info": "Dummy_Musik_epg"})
    
    # Add Channel Definitions with Logos
    for ch in channels:
        chan_elem = ET.SubElement(tv, 'channel', id=ch["id"])
        ET.SubElement(chan_elem, 'display-name').text = ch["name"]

    # Generate Programming
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    base_start = now_utc.replace(minute=0, second=0, microsecond=0)
    
    for ch in channels:
            # Generates 18 blocks of 8 hour each using the channel name
            for i in range(18):
                prog_start = base_start + datetime.timedelta(hours=i * 8)
                prog_stop = prog_start + datetime.timedelta(hours=8)
                start_str = prog_start.strftime('%Y%m%d%H%M%S +0100')
                stop_str = prog_stop.strftime('%Y%m%d%H%M%S +0100')
                
                prog = ET.SubElement(tv, 'programme', start=start_str, stop=stop_str, channel=ch["id"])
                ET.SubElement(prog, 'title', lang="de").text = ch['title']
                ET.SubElement(prog, 'desc', lang="de").text = ch['desc']

    # Format and Save XML
    xml_string = ET.tostring(tv, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="  ")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
        
    print(f"\n✅ {filename} erfolgreich mit 8-Stunden-Beschriftungen erstellt")

if __name__ == "__main__":
    generate_dummy_musik_epg()
