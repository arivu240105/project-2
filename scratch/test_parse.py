import sys
from pathlib import Path
from pypdf import PdfReader

def test_parse():
    pdf_path = Path("data/uploaded_files/Sample pdf.pdf")
    print(f"File exists: {pdf_path.exists()}")
    if not pdf_path.exists():
        return
        
    try:
        reader = PdfReader(str(pdf_path))
        num_pages = len(reader.pages)
        print(f"Total pages: {num_pages}")
        
        # Check first 5 pages
        for idx in range(min(5, num_pages)):
            page = reader.pages[idx]
            text = page.extract_text()
            print(f"Page {idx+1} text length: {len(text) if text else 0}")
            if text:
                print(f"Page {idx+1} snippet: {repr(text[:200])}")
            else:
                print(f"Page {idx+1} is empty or has no extractable text")
                
    except Exception as e:
        print(f"Exception encountered: {e}")

if __name__ == "__main__":
    test_parse()
