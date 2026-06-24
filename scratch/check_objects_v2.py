import pypdfium2 as pdfium
from pathlib import Path

pdf_path = Path("data/uploaded_files/Sample pdf.pdf")
doc = pdfium.PdfDocument(str(pdf_path))
page = doc[0]
for obj in page.get_objects():
    print(f"Object: {obj}, type: {type(obj)}, dir: {dir(obj)}")
