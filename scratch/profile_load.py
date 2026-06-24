import time
print("Starting imports...")
start = time.time()
import streamlit as st
import pandas as pd
from pathlib import Path
print(f"Base imports took: {time.time() - start:.2f}s")

# Measure loading store.py and creating VectorStoreManager
start = time.time()
from src.vectorstore.store import VectorStoreManager
print(f"Importing store took: {time.time() - start:.2f}s")

start = time.time()
v = VectorStoreManager()
print(f"Creating VectorStoreManager took: {time.time() - start:.2f}s")

# Measure loading reranker
start = time.time()
from src.retrieval.reranker import CrossEncoderReranker
print(f"Importing reranker took: {time.time() - start:.2f}s")

start = time.time()
r = CrossEncoderReranker()
print(f"Creating CrossEncoderReranker took: {time.time() - start:.2f}s")
