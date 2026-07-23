import pypdfium2 as pdfium
from pathlib import Path

pdf_path = Path("data/uploaded_files/Sample pdf.pdf")
doc = pdfium.PdfDocument(str(pdf_path))
all_scanned = True
for idx, page in enumerate(doc):
    objs = list(page.get_objects())
    types = [type(obj).__name__ for obj in objs]
    print(f"Page {idx+1}: {types}")
    if any(t == 'PdfText' for t in types):
        all_scanned = False
print(f"Are all pages scanned (no text objects)? {all_scanned}")

