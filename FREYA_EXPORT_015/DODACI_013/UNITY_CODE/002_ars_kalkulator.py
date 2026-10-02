print("==================================================")
print("     📊 FINANSIJSKI KALKULATOR: ARS PROJEKAT     ")
print("==================================================")
print("Bok Danijela! Piton je spreman za biznis analizu.\n")

try:
    # Tražimo od šefa (root) da unese cifre
    investicija = float(input("💰 Unesi iznos ukupne investicije za ARS (€): "))
    godisnji_prihod = float(input("📈 Unesi očekivani godišnji neto profit (€): "))
    
    # Najvrijednije investicione kalkulacije
    roi = (godisnji_prihod / investicija) * 100
    period_povrata = investicija / godisnji_prihod
    
    print("\n--------------------------------------------------")
    print("📊 REZULTATI NAJVRIJEDNIJIH KALKULACIJA:")
    print("--------------------------------------------------")
    print(f"➡️  Ukupna investicija: {investicija:,.2f} €")
    print(f"➡️  Godišnji povrat (ROI): {roi:.2f}%")
    print(f"➡️  Novac se potpuno vraća za: {period_povrata:.1f} godina")
    
    print("\n--------------------------------------------------")
    if roi >= 20:
        print("🔥 Piton kaže: ARS projekat ima brutalan povrat! Sretno!")
    elif roi >= 10:
        print("👍 Piton kaže: Ovo je stabilna i pametna investicija.")
    else:
        print("⚠️ Piton kaže: Povrat je sporiji, provjeri troškove.")
        
except ValueError:
    print("❌ Greška: Molimo te unesi samo čiste brojeve (npr. 50000).")

print("==================================================")
