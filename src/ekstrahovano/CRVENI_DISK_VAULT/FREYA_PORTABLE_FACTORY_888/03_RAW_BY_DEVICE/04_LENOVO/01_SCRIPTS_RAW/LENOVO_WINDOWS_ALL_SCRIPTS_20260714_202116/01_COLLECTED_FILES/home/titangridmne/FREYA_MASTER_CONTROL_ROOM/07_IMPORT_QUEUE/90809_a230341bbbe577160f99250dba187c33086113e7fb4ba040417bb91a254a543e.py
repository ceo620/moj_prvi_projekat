import os, zipfile, html

OUT = "/mnt/c/Users/titangrid.info/Desktop/TITAN_GRID_TOP3_WORD_NARRATIVES_READY"

packages = [
    ("R02_DATA_ROOM_REVIEW", "Data Room Review"),
    ("R03_CONTROL_TOWER_REVIEW", "Control Tower Review"),
    ("R04_DUE_DILIGENCE_REVIEW", "Due Diligence Review"),
]

def p(text, style=None):
    text = html.escape(text)
    if style:
        return f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r><w:t>{text}</w:t></w:r></w:p>'
    return f'<w:p><w:r><w:t>{text}</w:t></w:r></w:p>'

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
<w:style w:type="paragraph" w:styleId="Heading2">
<w:name w:val="Heading 2"/>
<w:rPr><w:b/><w:sz w:val="26"/></w:rPr>
</w:style>
</w:styles>'''

def write_docx(path, paragraphs):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/document.xml", doc_xml(paragraphs))

def narrative_paragraphs(title):
    return [
        p(f"TITAN GRID - {title}", "Title"),
        p("Structured Project Review Narrative"),
        p("Status: Not for sending yet"),
        p("Human Gate: Active"),

        p("1. Executive Narrative", "Heading1"),
        p("TITAN GRID is being prepared as a structured way to organize complex project material before it is shared for external review."),
        p("The purpose is to turn scattered documents, evidence, technical records, financial preparation notes and business context into a clear first-review package."),

        p("2. The Business Problem", "Heading1"),
        p("In serious projects, information often becomes scattered across emails, folders, archives, technical files, contracts, screenshots, financial notes, supplier records and older versions."),
        p("This creates confusion for banks, investors, advisors, partners and due diligence reviewers who need to understand what exists, what is verified, what is missing and what decision is needed next."),

        p("3. The TITAN GRID Approach", "Heading1"),
        p("TITAN GRID prepares a controlled review structure. It does not replace expert review. It prepares the material so the correct person can review it more efficiently."),
        p("- what material exists"),
        p("- where the material came from"),
        p("- what has been verified"),
        p("- what is still missing"),
        p("- what should not be claimed yet"),
        p("- what decision is needed next"),

        p("4. Why This Package Exists", "Heading1"),
        p("This document is not an approval request. It is a review-route request."),
        p("The immediate goal is to identify whether the recipient is the correct person to receive a short introductory package, or whether the matter should be routed to another person or department."),

        p("5. What We Are Asking", "Heading1"),
        p("- Confirm whether this type of structured project package is relevant to your role."),
        p("- Confirm whether you are the correct person to review it."),
        p("- If not, indicate the correct person or department."),
        p("- Confirm what should be included before a fuller package is sent."),

        p("6. What We Are Not Claiming", "Heading1"),
        p("- No bank approval is claimed."),
        p("- No lender approval is claimed."),
        p("- No institutional approval is claimed."),
        p("- No investment readiness is claimed."),
        p("- No certification is claimed."),
        p("- No partnership is claimed."),
        p("- No completed due diligence is claimed."),
        p("- No valuation is claimed."),

        p("7. Proposed Next Step", "Heading1"),
        p("If relevant, a short follow-up package can be prepared with a one-page business summary, selected evidence index, short presentation, financial preparation checklist and a clear review question."),

        p("8. Human Gate Status", "Heading1"),
        p("- Recipient confirmed: NO"),
        p("- Claims approved: NO"),
        p("- Attachments approved: NO"),
        p("- Final wording approved: NO"),
        p("- Email send allowed: NO"),
        p("- Ready to send: NO"),
        p("- Human Gate: ACTIVE"),
    ]

def email_paragraphs(title):
    return [
        p(f"TITAN GRID - CEO Email Draft - {title}", "Title"),
        p("Status: Not for sending yet"),
        p("Subject: Request for correct review route - structured project review package"),

        p("Dear [Name],"),
        p("My name is Danijela Djurovic Keskin, and I am preparing TITAN GRID as a structured way to organize complex project material before it is shared for external review."),
        p("The purpose is to turn scattered documents, evidence, technical records, financial preparation notes and business context into a clear first-review package."),
        p("At this stage, I am not asking for approval, investment, certification, partnership or due diligence confirmation."),
        p("My first request is only to identify the correct review route."),
        p("Could you please let me know whether you are the appropriate person to receive a short introductory package, or whether there is someone else I should contact?"),
        p("If relevant, I can send a brief one-page summary and a short presentation for initial review."),
        p("Kind regards,"),
        p("Danijela Djurovic Keskin"),
        p("CEO"),
        p("TITAN GRID"),
        p("ceo@titangrid.info"),

        p("Human Gate", "Heading1"),
        p("- Recipient confirmed: NO"),
        p("- Email send allowed: NO"),
        p("- Ready to send: NO"),
        p("- Human Gate: ACTIVE"),
    ]

for code, title in packages:
    folder = os.path.join(OUT, code)
    write_docx(
        os.path.join(folder, f"TITAN_GRID_{code}_NARRATIVE_REVIEW_DOCUMENT_V1_NOT_FOR_SENDING.docx"),
        narrative_paragraphs(title)
    )
    write_docx(
        os.path.join(folder, f"TITAN_GRID_{code}_CEO_EMAIL_NARRATIVE_V1_NOT_FOR_SENDING.docx"),
        email_paragraphs(title)
    )

readme = os.path.join(OUT, "README_DOCX_DIRECT_EXPORT.md")
with open(readme, "w", encoding="utf-8") as f:
    f.write("""# TITAN GRID TOP3 Word Narratives

Created by direct DOCX generator, without Word COM.

Contents:
- R02 Data Room Review
- R03 Control Tower Review
- R04 Due Diligence Review

Each folder contains:
- narrative review document
- CEO email narrative draft

SAFE STATUS:
READY_TO_SEND=NO
EMAIL_SEND_ALLOWED=NO
RECIPIENT_CONFIRMED=NO
HUMAN_GATE=ACTIVE
""")

print("DOCX_DIRECT_EXPORT_COMPLETE")
