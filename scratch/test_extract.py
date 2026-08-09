import sys
from pathlib import Path

pdf_path = Path("data/uploaded_files/Sample pdf.pdf")

print("--- Testing pdfplumber ---")
try:
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        print(f"pdfplumber opened. Pages: {len(pdf.pages)}")
        for idx in range(min(5, len(pdf.pages))):
            text = pdf.pages[idx].extract_text()
            print(f"Page {idx+1} text length: {len(text) if text else 0}")
            if text:
                print(f"Page {idx+1} snippet: {repr(text[:200])}")
except Exception as e:
    print(f"pdfplumber failed: {e}")

print("\n--- Testing pdfminer.six ---")
try:
    from pdfminer.high_level import extract_text
    # Extract first page only to test
    from pdfminer.pdfpage import PDFPage
    with open(pdf_path, 'rb') as fp:
        pages = list(PDFPage.get_pages(fp))
        print(f"pdfminer pages: {len(pages)}")
    text = extract_text(str(pdf_path), page_numbers=[0, 1, 2])
    print(f"pdfminer extract_text (pages 0-2) length: {len(text)}")
    print(f"pdfminer snippet: {repr(text[:200])}")
except Exception as e:
    print(f"pdfminer failed: {e}")


