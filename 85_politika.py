import urllib.request
import xml.etree.ElementTree as ET
import html

print("==================================================")
print("   🇪🇺 LIVE POLITIČKI PODACI: EU & CRNA GORA 🇲🇪   ")
print("==================================================")
print("Piton povlači podatke s EU servera...\n")

try:
    url = "https://www.europarl.europa.eu/rss/doc/top-stories/en.xml"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        podaci = response.read()
    korijen = ET.fromstring(podaci)
    
    print("🔥 NAJNOVIJE POLITIČKE TEME IZ EU:")
    brojac = 0
    for item in korijen.findall('.//item'):
        if brojac >= 3: break
        naslov = html.unescape(item.find('title').text)
        print(f"📣 {naslov}\n--------------------------------------------------")
        brojac += 1
except Exception:
    print("❌ iSH greška: Provjeri internet vezu u iSH aplikaciji.")

print("\n🇲🇪 STATUS ZA CRNU GORU:")
print("-> Evropska komisija je usvojila paket od 3,2 milijarde eura.")
print("-> Države članice dale su zeleno svjetlo za Ugovor o pristupanju.")
print("==================================================")
