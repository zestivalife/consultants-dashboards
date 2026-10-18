"""P20 deterministic, dependency-free PDF and DOCX output primitives."""
from hashlib import sha256
from io import BytesIO
from zipfile import ZIP_DEFLATED,ZipFile
from xml.sax.saxutils import escape

REPORT_TYPES=frozenset({"CLIENT_PROGRESS_REPORT","PROGRAMME_COMPLETION_REPORT","ASSESSMENT_PROGRESS_REPORT","REHAB_PROGRESS_REPORT","COACHING_PROGRESS_REPORT","WELLNESS_PROGRESS_REPORT","THERAPY_PROGRESS_REPORT","BEHAVIOUR_PROGRESS_REPORT","DIABETES_EDUCATION_PROGRESS_REPORT","OT_PROGRESS_REPORT"})
PROVENANCE=frozenset({"CLIENT_REPORTED","PRACTITIONER_ENTERED","SYSTEM_DERIVED","LAB_CONFIRMED","WEARABLE_SOURCE"})

def checksum(data):return sha256(data).hexdigest()
def _pdf_escape(value):return str(value).replace("\\","\\\\").replace("(","\\(").replace(")","\\)")

def report_lines(snapshot):
    lines=[snapshot["title"],f"Period: {snapshot['period_start']} to {snapshot['period_end']}",f"Profession: {snapshot['profession_code']}"]
    if snapshot.get("consultant_summary"):lines.extend(["Consultant summary",snapshot["consultant_summary"]])
    for section in snapshot.get("sections",[]):
        lines.append(section["title"])
        for item in section.get("items",[]):lines.append(f"- {item.get('label','Item')}: {item.get('value','—')} [{item.get('provenance','SYSTEM_DERIVED')}]")
    return lines

def build_pdf(snapshot):
    lines=report_lines(snapshot);objects=[]
    stream="BT /F1 11 Tf 48 780 Td 14 TL "+" ".join(f"({_pdf_escape(line)}) Tj T*" for line in lines[:48])+" ET"
    objects=[b"<< /Type /Catalog /Pages 2 0 R >>",b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",f"<< /Length {len(stream.encode())} >>\nstream\n{stream}\nendstream".encode(),b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out=bytearray(b"%PDF-1.4\n");offsets=[0]
    for index,obj in enumerate(objects,1):offsets.append(len(out));out.extend(f"{index} 0 obj\n".encode()+obj+b"\nendobj\n")
    xref=len(out);out.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:out.extend(f"{offset:010d} 00000 n \n".encode())
    out.extend(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode());return bytes(out)

def build_docx(snapshot):
    paragraphs="".join(f"<w:p><w:r><w:t>{escape(str(line))}</w:t></w:r></w:p>" for line in report_lines(snapshot))
    document=f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{paragraphs}<w:sectPr/></w:body></w:document>'
    output=BytesIO()
    with ZipFile(output,"w",ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml",'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        archive.writestr("_rels/.rels",'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        archive.writestr("word/document.xml",document)
    return output.getvalue()
