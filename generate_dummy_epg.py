import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_dummy_channel_epg():
    # Configuration
    channels = [
        {"id": "MiamiTV Music", "name": "Miami TV Music", "desc": "Variety of Music 24/7"},
        {"id": "MiamiTV DJ", "name": "Miami TV DJ", "desc": "Continuous DJ electronic music from DJs around the world."},
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
                ET.SubElement(prog, 'title', lang="de").text = ch['name']
                ET.SubElement(prog, 'desc', lang="de").text = ch['desc']

    # Format and Save XML
    xml_string = ET.tostring(tv, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="  ")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
        
    print(f"\n✅ {filename} erfolgreich mit 1-Stunden-Beschriftungen erstellt")

if __name__ == "__main__":
    generate_dummy_channel_epg()
