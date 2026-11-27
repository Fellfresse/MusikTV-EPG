import datetime
import gzip
import xml.etree.ElementTree as ET
from xml.dom import minidom
from zoneinfo import ZoneInfo


def generate_dummy_magenta_musik_epg():
    # Zeitzone definieren (berücksichtigt automatisch MEZ/MESZ)
    tz = ZoneInfo("Europe/Berlin")

    # Konfiguration der Kanäle
    channels = [
        {"id": "WOA", "name": "W:O:A History",
         "desc": "Metal ist mehr als nur Musik – Metal ist eine Lebenseinstellung! Mit schwarzen Kutten, langen Haaren und Rhythmus im Blut prägte das Genre in den 70er-Jahren seinen unverwechselbaren Charakter. Diese Musikrichtung pulsiert mit energiegeladenen Gitarrenriffs und donnernden Schlagzeugbeats, die zum ultimativen Headbangen einladen."},
        {"id": "WOA HN 2025", "name": "W:O:A Holy Night 2025",
         "desc": "Was für ein Fest! Die Weltpremiere der W:O:A Holy Night mag vorbei sein, doch ihr könnt die einzigartige Metal-Weihnachtsstimmung erneut erleben. Scrollt einfach nach unten, wählt euer Lieblingsvideo aus und genießt die Show noch einmal in voller Lautstärke!"},
        {"id": "WOA 2026", "name": "Wacken Open Air 2026",
         "desc": "Das Wacken Open Air ist mehr als ein Festival - es ist ein Lebensgefühl. Seit 1990 färbt das Metal-Event die beschauliche Gemeinde Wacken in Schleswig-Holstein schwarz und lädt jährlich Tausende Fans zum Headbangen ein. Was mit sechs Bands auf einem Acker begann, ist nun das größte Heavy-Metal-Festival der Welt, das Fans aus dem ganzen Land und darüber hinaus anlockt."},
        {"id": "RAR 2026", "name": "Rock am Ring 2026",
         "desc": "Das Rock am Ring ist mehr als ein Festival, es ist pure Energie. Seit 1985 verwandelt das legendäre Kultevent die Eifel rund um den Nürburgring in ein Mekka für Rock- und Metal-Fans. Was einst als einmaliges Ereignis geplant war, ist längst zu einem der traditionsreichsten und größten Rockfestivals Europas herangewachsen. Hier findet ihr eine Auswahl packender Inhalte vom Nürburgring."},
        {"id": "Huri 2026", "name": "Hurricane 2026",
         "desc": "Das Hurricane Festival hat sich als eine der festen Größen in der europäischen Festivalszene etabliert. Seit seiner Gründung im Jahr 1997 zieht es jährlich Zehntausende von Musikfans nach Scheeßel, Niedersachsen. Mit einem vielfältigen Line-up aus Rock, Indie und elektronischer Musik bot das Festival 2026 erneut ein beeindruckendes Programm, das die Besucher begeistert hat. Die Mischung aus etablierten Künstlern und aufstrebenden Talenten sorgte für unvergessliche Momente und eine ausgelassene Festivalatmosphäre."},
        {"id": "Lolla 2026", "name": "Lollapalooza Berlin 2026",
         "desc": "Lollapalooza Berlin hat sich seit seiner Premiere 2015 als eines der aufregendsten Festivals in Deutschland etabliert. Im Jahr 2026 verwandelte es die Hauptstadt erneut in einen Hotspot für Musik und Kultur. Das Festival präsentierte ein breites Spektrum an internationalen Künstlern und bot den Besuchern ein einzigartiges Erlebnis mit Kunstinstallationen und nachhaltigen Initiativen. Lollapalooza Berlin bleibt ein Highlight im Veranstaltungskalender und zieht weiterhin ein internationales Publikum an."},
    ]

    filename = "epg_Dummy_Magenta_Musik.xml"
    gz_filename = "EPG_VOD_Magenta_Musik.xml.gz"

    # XML-Wurzelelement erstellen
    tv = ET.Element('tv', {"generator-info-name": "Fellfresse", "generator-info": "Dummy_Magenta_Musik_epg"})

    # Kanaldefinitionen hinzufügen
    for ch in channels:
        chan_elem = ET.SubElement(tv, 'channel', id=ch["id"])
        ET.SubElement(chan_elem, 'display-name').text = ch["name"]

    # Startdatum mit lokaler Zeitzone (00:00 Uhr)
    base_start = datetime.datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)

    for ch in channels:
        # Erzeugt 10 Blöcke à 1 Tag mit dynamischem Zeitzonen-Offset (%z)
        for i in range(10):
            # Durch .replace(tzinfo=tz) wird für jedes Datum neu geprüft, ob MEZ oder MESZ gilt
            prog_start = (base_start + datetime.timedelta(days=i)).replace(tzinfo=tz)
            prog_stop = (base_start + datetime.timedelta(days=i + 1)).replace(tzinfo=tz)
            
            start_str = prog_start.strftime('%Y%m%d%H%M%S %z')
            stop_str = prog_stop.strftime('%Y%m%d%H%M%S %z')

            prog = ET.SubElement(tv, 'programme', start=start_str, stop=stop_str, channel=ch["id"])
            ET.SubElement(prog, 'title', lang="de").text = ch['name']
            ET.SubElement(prog, 'desc', lang="de").text = ch['desc']

    # XML formatieren
    xml_string = ET.tostring(tv, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="  ")

    # Als normale .xml speichern
    with open(filename, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    # Zusätzlich als komprimierte .xml.gz speichern
    with gzip.open(gz_filename, "wt", encoding="utf-8") as gz_f:
        gz_f.write(pretty_xml)

    print(f"\n✅ {filename} und {gz_filename} erfolgreich erstellt")


if __name__ == "__main__":
    generate_dummy_magenta_musik_epg()
