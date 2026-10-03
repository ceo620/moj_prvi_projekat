import urllib.parse

print("==================================================")
print("    🌐 PITONOV LINKEDIN ASISTENT ZA UMREŽAVANJE   ")
print("==================================================")
print("Bok Danijela! Budući da nas LinkedIn špijunira i ne da")
print("da budemo botovi, ja ću ti pomoći da ih pametno pretražiš!\n")

pojam = input("Unesi zanimanje ili titulu ljudi koje želiš naći: ")

# Kodiranje teksta za web adresu
kodirani_pojam = urllib.parse.quote(pojam)

# Stvaranje direktnog linka za pretragu ljudi na LinkedInu
link = f"https://www.linkedin.com/search/results/people/?keywords={kodirani_pojam}"

print("\n--------------------------------------------------")
print("🚀 TVOJ TAJNI LINK ZA PRETRAGU JE SPREMAN:")
print("--------------------------------------------------")
print(link)
print("\nKopiraj ovaj link, zalijepi ga u Safari na telefonu i")
print("otvorit će ti se točno najbitniji ljudi za taj pojam!")
print("==================================================")
