import pypdfium2 as pdfium
import easyocr
import numpy as np
from PIL import Image
import time
from pathlib import Path

pdf_path = Path("data/uploaded_files/Sample pdf.pdf")

print("Initializing EasyOCR reader...")
reader = easyocr.Reader(['en'])

print("Opening PDF with pypdfium2...")
doc = pdfium.PdfDocument(str(pdf_path))
page = doc[0]

# Render page to PIL image
print("Rendering page 1...")
start_time = time.time()
bitmap = page.render(scale=2.0) # render at 144 DPI
pil_img = bitmap.to_pil()
render_time = time.time() - start_time
print(f"Rendered in {render_time:.2f}s")

# Convert PIL image to numpy array (EasyOCR takes PIL image, file path, bytes or numpy array)
print("Running OCR on page 1...")
start_ocr = time.time()
results = reader.readtext(np.array(pil_img), detail=0)
ocr_time = time.time() - start_ocr
print(f"OCR finished in {ocr_time:.2f}s")

text = "\n".join(results)
print(f"Extracted text length: {len(text)}")
print(f"Text snippet:\n{text[:500]}")
