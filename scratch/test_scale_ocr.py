import pypdfium2 as pdfium
import easyocr
import numpy as np
import time
from pathlib import Path

pdf_path = Path("data/uploaded_files/Sample pdf.pdf")
reader = easyocr.Reader(['en'], verbose=False)
doc = pdfium.PdfDocument(str(pdf_path))
page = doc[0]

for scale in [1.0, 1.5, 2.0]:
    t0 = time.time()
    bitmap = page.render(scale=scale)
    pil_img = bitmap.to_pil()
    render_time = time.time() - t0
    
    t0 = time.time()
    results = reader.readtext(np.array(pil_img), detail=0)
    ocr_time = time.time() - t0
    
    print(f"Scale: {scale:.1f} | Render: {render_time:.2f}s | OCR: {ocr_time:.2f}s | Text length: {len(' '.join(results))}")
