#!/bin/sh
set -eu
umask 077
d=$(mktemp -d /root/FREYA_IPHONE_ISH_NODE_888/04_HUMAN_GATE/freya_srednja_klasa_XXXXXX)
cat > "$d/NACRT.txt" <<'FREYA_TEXT'
NACRT — HUMAN_REVIEW=PENDING; TVRDNJE_NEPROVJERENE

======================================================================
      FREYA ZA SREDNJU KLASU - STRATEGIJA MASOVNOG TRŽIŠTA (2026)
======================================================================

1. ŠTA SREDNJOJ KLASI ZAPRAVO TREBA?
* Potreba za smanjenjem troškova (Cost-Cutting): Srednja klasa je umorna od 
  pretplata. Netflix, Spotify, iCloud, softverske licence – sve im uzima novac 
  svakog meseca. Žele "kupiš jednom, tvoje je zauvek".
* Zaštita od digitalnog mobinga: Odbijaju ciljane oglase koji im iskaču sekundu 
  nakon što nešto izgovore pored telefona. Žele mir i privatnost bez komplikovanog 
  IT znanja.
* Automatizacija kućnog biznisa: Freelanceri i mali preduzetnici žele stabilan 
  sistem koji radi za njih bez skupih agencija.

----------------------------------------------------------------------
2. PROIZVOD: "FREYA HOME-BOX" ILI LOKALNI APP COMPANION
Za razliku od enterprise verzije, srednjoj klasi prepakujemo sistem u:
- Ultra-light iOS/Android prateću aplikaciju koja lokalno hostuje iSH okruženje.
- Cijena: €49 jednokratno ili €4.99/mesečno – dostupno svima.

----------------------------------------------------------------------
3. TRI STRATEŠKA PILARA ZA MARKETING (SREDNJA KLASA)

* PILAR A: "Prekinite pretplatnički feudalizam"
  Tekst: "Zašto plaćaš iCloud i eksterne cloud storidže svakog meseca da bi ti 
  skenirali slike? Poveži eksterni disk sa telefonom. FREYA storage_node radi 
  lokalni backup. Tvoj hardver – tvoj mir."

* PILAR B: "Ugasi prisluškivanje odmah"
  Tekst: "Nisi lud, telefon te stvarno sluša. Naš network_comm_audit.sh modul 
  smo spakovali u jednostavan toggle switch. Sečemo telemetrijske pakete velikih 
  kompanija direktno na nivou kernela."

* PILAR C: "Autonomni asistent za male biznise"
  Tekst: "Kao mali preduzetnik, nemaš budžet za marketing tim. Naš optimizovani 
  orkestrator radi žetvu lokalnih signala i šalje ponude dok ti spremaš kafu."
======================================================================
FREYA_TEXT
echo "REVIEW=$d/NACRT.txt"
