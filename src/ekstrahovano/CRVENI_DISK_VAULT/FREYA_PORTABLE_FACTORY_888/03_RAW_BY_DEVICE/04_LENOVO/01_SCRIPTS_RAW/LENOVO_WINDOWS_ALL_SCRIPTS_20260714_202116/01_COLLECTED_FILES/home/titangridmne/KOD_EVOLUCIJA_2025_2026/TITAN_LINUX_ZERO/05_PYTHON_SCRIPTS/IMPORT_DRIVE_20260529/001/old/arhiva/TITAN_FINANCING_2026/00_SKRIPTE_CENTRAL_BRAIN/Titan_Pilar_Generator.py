import os

def generate_pilar():
    print("\n--- 🏛️ TITAN GRID: PILAR GENERATOR v1.0 ---")
    print("1. Zeleni Grant (ESG & DNSH)")
    print("2. Digitalna Transformacija (Smart Factory)")
    print("3. Investicioni Briefing (Hamza Yavuz & ROI)")
    print("4. Socijalni Impakt (Zaposljavanje u Tuzima)")
    
    choice = input("\nKoji projekat pišemo danas, Onur? (1-4): ")
    
    pilars = {
        "1": "🌿 [ESG PILAR]: Projekt TITAN implementira DNSH principe kroz nultu stopu zagadjenja u Tuzima i 95% reciklabilnost metala. Marel Engineering garantuje energetsku efikasnost.",
        "2": "🤖 [DIGITAL PILAR]: Integracija SCADA sistema, ABB kontrolera i Elkom kabliranja stvara prvu Smart fabriku transformatorskih kazana u CG. Upravljanje putem Centralnog Mozga.",
        "3": "💰 [FINANCIAL PILAR]: Partnerstvo sa Hamzom Yavuzom osigurava strateski equity. CAPEX optimizovan kroz Change Order Dashboard (Beton Mont, MetAlCon). Rok: 23.04.2026.",
        "4": "👥 [SOCIAL PILAR]: Transfer tehnologije i visoko-tehnoloska radna mjesta za lokalnu zajednicu u Tuzima. Tim predvodjen Onur (CFO) i Darkom Djurovicem."
    }
    
    res = pilars.get(choice, "Pogresan unos. Pokusaj ponovo.")
    print("\n--- 📄 GENERISANI TEKST ZA TVOJ PROJEKAT ---")
    print(res)
    print("\n--- Tekst je spreman za Copy-Paste! ---")

if __name__ == "__main__":
    generate_pilar()
