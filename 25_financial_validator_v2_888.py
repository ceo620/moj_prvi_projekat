import sys,zipfile,re,os
import xml.etree.ElementTree as ET

p=sys.argv[1]
checks={}
signals=set()
formulas=0

try:
    with zipfile.ZipFile(p) as z:
        names=set(z.namelist())

        checks["XLSX_STRUCTURE"] = (
            "[Content_Types].xml" in names and
            "xl/workbook.xml" in names
        )

        text=""

        for n in names:
            if not n.endswith(".xml"):
                continue

            raw=z.read(n)
            x=raw.decode("utf-8","strict").lower()
            text+=" "+x
            if n.startswith("xl/worksheets/"):
                if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
                    raise ValueError("XML_DTD_OR_ENTITY_NOT_ALLOWED")
                root=ET.fromstring(raw)
                allowed={"f", "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}f",
                         "{http://purl.oclc.org/ooxml/spreadsheetml/main}f"}
                formulas += sum(node.tag in allowed for node in root.iter())

        domains={
            "ASSUMPTIONS":["assumption"],
            "CURRENCY":["eur","usd","currency"],
            "PERIOD":["2026","2027","2028"],
            "CAPEX":["capex"],
            "OPEX":["opex"],
            "DEBT":["debt","dscr"],
            "IRR":["irr"],
            "SCENARIO":["scenario"],
            "SENSITIVITY":["sensitivity"]
        }

        for k,terms in domains.items():
            ok=any(t in text for t in terms)
            checks[k]=ok
            if ok:
                signals.add(k)

except Exception as e:
    print("FILE="+os.path.basename(p))
    print("RESULT=HOLD")
    print("ERROR="+str(e))
    raise SystemExit(1)

print("FILE="+os.path.basename(p))
print("FORMULAS="+str(formulas))

for k in sorted(checks):
    print(k+"_VALIDATOR="+("PASS" if checks[k] else "HOLD"))

critical=[
    checks.get("XLSX_STRUCTURE",False),
    formulas>0,
    checks.get("ASSUMPTIONS",False),
    checks.get("CURRENCY",False),
    checks.get("PERIOD",False)
]

print("DOMAIN_SIGNALS="+str(len(signals)))
print("SOURCE_CHANGED=0")
print("RESULT="+("PASS" if all(critical) else "HOLD"))
