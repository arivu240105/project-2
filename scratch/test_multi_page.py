import pypdfium2 as pdfium
import easyocr
import numpy as np
import time
from pathlib import Path

pdf_path = Path("data/uploaded_files/Sample pdf.pdf")

print("Initializing EasyOCR...")
reader = easyocr.Reader(['en'], verbose=False)
doc = pdfium.PdfDocument(str(pdf_path))

for page_idx in range(3):
    print(f"\n--- Page {page_idx+1} ---")
    t0 = time.time()
    page = doc[page_idx]
    bitmap = page.render(scale=2.0)
    pil_img = bitmap.to_pil()
    render_time = time.time() - t0
    
    t0 = time.time()
    results = reader.readtext(np.array(pil_img), detail=0)
    ocr_time = time.time() - t0
    
    print(f"Render time: {render_time:.2f}s | OCR time: {ocr_time:.2f}s")
    print(f"Text length: {len(' '.join(results))}")
