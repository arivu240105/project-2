import easyocr
import time

t0 = time.time()
reader = easyocr.Reader(['en'])
print(f"Reader init time: {time.time() - t0:.3f}s")

t0 = time.time()
reader2 = easyocr.Reader(['en'])
print(f"Second reader init time: {time.time() - t0:.3f}s")
