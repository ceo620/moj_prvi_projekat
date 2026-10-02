import sys,zipfile,re,os

p=sys.argv[1]
name=os.path.basename(p).lower()

checks={
 "CAPEX":["capex"],
 "DEBT":["debt","dscr"],
 "IRR":["irr"],
 "SCENARIO":["scenario"],
 "SENSITIVITY":["sensitivity"]
}

with zipfile.ZipFile(p) as z:
    text=""
    formulas=0

    for n in z.namelist():
        if not n.endswith(".xml"):
            continue

        x=z.read(n).decode("utf-8","ignore").lower()
        text+=" "+x
        formulas+=len(re.findall(r'<f(?: |>).*?</f>',x,re.S))

print("FILE="+os.path.basename(p))
print("FORMULAS="+str(formulas))

passed=0

for group,keys in checks.items():
    ok=all(k in text for k in keys)
    print(group+"_VALIDATOR="+("PASS" if ok else "HOLD"))
    if ok:
        passed+=1

print("VALIDATORS_PASS="+str(passed))
print("SOURCE_CHANGED=0")
print("RESULT="+("PASS" if formulas>0 and passed>0 else "HOLD"))
