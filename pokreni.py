import requests

print("Sistem je spreman! Provera internet konekcije...")
odgovor = requests.get("https://deb.debian.org")
print(f"Status odgovora Debian servera: {odgovor.status_code}")
