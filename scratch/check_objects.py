import pypdfium2 as pdfium
from pathlib import Path

pdf_path = Path("data/uploaded_files/Sample pdf.pdf")
doc = pdfium.PdfDocument(str(pdf_path))
print(f"Total pages: {len(doc)}")

for i in range(min(5, len(doc))):
    page = doc[i]
    print(f"Page {i+1} size: {page.get_size()}")
    images = list(page.get_objects())
    print(f"Page {i+1} number of objects: {len(images)}")
    img_count = sum(1 for obj in page.get_objects() if obj.type == pdfium.PDFOBJ_IMAGE)
    text_count = sum(1 for obj in page.get_objects() if obj.type == pdfium.PDFOBJ_TEXT)
    print(f"Page {i+1} - Images: {img_count}, Text objects: {text_count}")
