import pypdfium2 as pdfium
from pathlib import Path

pdf_path = Path("data/uploaded_files/Sample pdf.pdf")
doc = pdfium.PdfDocument(str(pdf_path))
all_scanned = True


doc = pdfium.PdfDocument(str(pdf_path))
all_scanned = True



