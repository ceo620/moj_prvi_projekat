import os, zipfile, html

OUT = "/mnt/c/Users/titangrid.info/Desktop/TITAN_GRID_TOP3_WORD_NARRATIVES_READY/R02_DATA_ROOM_REVIEW"
DOCX = os.path.join(OUT, "TITAN_GRID_R02_DATA_ROOM_REVIEW_EXECUTIVE_NARRATIVE_V2_NOT_FOR_SENDING.docx")
SRC = os.path.join(OUT, "TITAN_GRID_R02_DATA_ROOM_REVIEW_EXECUTIVE_NARRATIVE_V2_SOURCE.md")

def p(text, style=None):
    text = html.escape(text)
    if style:
        return f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'
    return f'<w:p><w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'

CONTENT = [
    ("TITAN GRID — Executive Data Room Review Narrative", "Title"),
    ("Prepared by Danijela Đurović Keskin, CEO, TITAN GRID", None),
    ("Status: Not for sending yet", None),
    ("Human Gate: Active", None),

    ("1. Executive Note", "Heading1"),
    ("TITAN GRID is being prepared as a structured business review system for complex project material. Its purpose is to help turn scattered documentation, evidence, technical records, financial preparation notes and business context into a clear first-review package.", None),
    ("This document is not an approval request. It is a controlled review-route document. The first goal is to identify the correct person or department for an initial data room and project-structure review.", None),

    ("2. Why This Matters", "Heading1"),
    ("In serious industrial, infrastructure, finance or project-development work, documentation often becomes fragmented. Important material may exist across emails, archives, laptops, old folders, technical files, contracts, screenshots, supplier records, lender requirements and multiple document versions.", None),
    ("When that happens, a reviewer cannot easily understand what exists, what has been verified, what is missing, what is only internal preparation, and what decision is actually being requested.", None),
    ("TITAN GRID is being built to reduce that confusion before external review begins.", None),

    ("3. The Business Problem", "Heading1"),
    ("A project may have valuable information, but if the information is not organized, the value is difficult to review. This creates delays, misunderstanding and unnecessary risk.", None),
    ("A bank, advisor, investor, due diligence reviewer, legal team, technical reviewer or strategic partner usually needs a clean review package before engaging seriously.", None),
    ("The problem is not only document storage. The problem is decision readiness.", None),

    ("4. The TITAN GRID Approach", "Heading1"),
    ("TITAN GRID prepares a controlled review structure. It does not replace lawyers, auditors, banks, engineers or due diligence professionals. It prepares the material so the right expert can review it more efficiently.", None),
    ("The system is designed to show:", None),
    ("- what material exists", None),
    ("- where the material came from", None),
    ("- what has been verified", None),
    ("- what is still missing", None),
    ("- what should not be claimed yet", None),
    ("- what decision or review route is needed next", None),

    ("5. Why This Is a Data Room Review Request", "Heading1"),
    ("This R02 package is focused on data room and control structure review. The purpose is to determine whether the available material can be organized into a reviewable package and what additional documentation would be required before any stronger business, finance or investment discussion.", None),
    ("The request is intentionally narrow: identify the correct review route before sending fuller materials.", None),

    ("6. What We Are Asking From the Recipient", "Heading1"),
    ("The first request is simple:", None),
    ("- Are you the correct person to review this type of structured project package?", None),
    ("- If not, who is the correct person or department?", None),
    ("- What should be included before a fuller package is sent?", None),
    ("- Would a one-page summary and short presentation be appropriate for initial review?", None),

    ("7. What We Are Not Claiming", "Heading1"),
    ("To avoid misunderstanding, TITAN GRID is not claiming:", None),
    ("- bank approval", None),
    ("- lender approval", None),
    ("- institutional approval", None),
    ("- investment readiness", None),
    ("- technical certification", None),
    ("- formal partnership", None),
    ("- completed due diligence", None),
    ("- final valuation", None),
    ("- or external validation", None),

    ("8. Proposed Initial Package", "Heading1"),
    ("If the recipient confirms relevance, a short follow-up package may be prepared containing:", None),
    ("- one-page executive summary", None),
    ("- selected evidence/source index", None),
    ("- human-readable presentation", None),
    ("- financial preparation checklist", None),
    ("- clear review question", None),

    ("9. Human Gate Status", "Heading1"),
    ("Recipient confirmed: NO", None),
    ("Claims approved: NO", None),
    ("Attachments approved: NO", None),
    ("Final wording approved: NO", None),
    ("Email send allowed: NO", None),
    ("Ready to send: NO", None),
    ("Human Gate: ACTIVE", None),

    ("10. Current Decision", "Heading1"),
    ("This V2 document is an executive narrative draft. It is stronger than the V1 template, but it is still not approved for sending. It becomes send-ready only after a real recipient is confirmed, the attachment list is approved, the claims are reviewed, and Human Gate gives final approval.", None),
]

def doc_xml(paragraphs):
    body = "\n".join(paragraphs)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
{body}
<w:sectPr>
<w:pgSz w:w="11906" w:h="16838"/>
<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
</w:sectPr>
</w:body>
</w:document>'''

CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''

RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

DOC_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'''

STYLES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:style w:type="paragraph" w:default="1" w:styleId="Normal">
<w:name w:val="Normal"/>
<w:rPr><w:sz w:val="22"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="Title">
<w:name w:val="Title"/>
<w:rPr><w:b/><w:sz w:val="36"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="Heading1">
<w:name w:val="Heading 1"/>
<w:rPr><w:b/><w:sz w:val="30"/></w:rPr>
</w:style>
</w:styles>'''

os.makedirs(OUT, exist_ok=True)

paragraphs = [p(text, style) for text, style in CONTENT]

with zipfile.ZipFile(DOCX, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", CONTENT_TYPES)
    z.writestr("_rels/.rels", RELS)
    z.writestr("word/_rels/document.xml.rels", DOC_RELS)
    z.writestr("word/styles.xml", STYLES)
    z.writestr("word/document.xml", doc_xml(paragraphs))

with open(SRC, "w", encoding="utf-8") as f:
    for text, style in CONTENT:
        if style == "Title":
            f.write(f"# {text}\n\n")
        elif style == "Heading1":
            f.write(f"## {text}\n\n")
        else:
            f.write(f"{text}\n\n")

print("R02_V2_EXECUTIVE_DOCX_CREATED=" + DOCX)
print("R02_V2_SOURCE_CREATED=" + SRC)
