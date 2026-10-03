import os,sys,tempfile
from pathlib import Path
if len(sys.argv)!=3 or not all(x.strip() for x in sys.argv[1:]):
    sys.exit("Upotreba: naslov tekst")
subject,body=sys.argv[1:]
if "\n" in subject or "\r" in subject:
    sys.exit("Naslov mora biti jedan red")
os.umask(0o077)
r=Path("/root/FREYA_IPHONE_ISH_NODE_888/04_HUMAN_GATE")
d=Path(tempfile.mkdtemp(prefix="MAIL_NACRT_",dir=str(r)))
text=("HUMAN_REVIEW=PENDING\nSEND_AUTHORIZED=NO\n"
      "RECIPIENT=UNSET\nSUBJECT="+subject+"\n\n"+body+"\n")
p=d/"NACRT.txt"
with p.open("x") as f:
    f.write(text)
assert p.read_text()==text
print("DRAFT_WRITE=PASS\nEXTERNAL_SEND=NONE\nREVIEW="+str(p))
