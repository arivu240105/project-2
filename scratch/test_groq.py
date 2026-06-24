import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.llm.groq_client import GroqClient
from src.utils.evaluator import RAGEvaluator
from langchain_core.documents import Document

load_dotenv()

print("1. Initializing GroqClient...")
client = GroqClient()

print(f"Has API key: {client.has_api_key()}")
print(f"Model Name: {client.model_name}")

print("\n2. Testing query rewrite...")
query = "How does it work?"
chat_history = [
    {"role": "user", "content": "Tell me about FastAPI dependency injection."},
    {"role": "assistant", "content": "FastAPI has a dependency injection system that allows you declare dependencies."}
]
rewritten = client.rewrite_query(query, chat_history)
print(f"Original: '{query}'")
print(f"Rewritten: '{rewritten}'")

print("\n3. Testing generate_response_stream...")
context_docs = [
    Document(page_content="FastAPI dependency injection is a system that lets you declare dependencies using Depends().", metadata={"source": "fastapi_docs.md", "page": "1", "title": "Dependencies"})
]
response_stream = client.generate_response_stream(
    query="Explain FastAPI dependency injection briefly.",
    context_docs=context_docs,
    chat_history=[],
    mode="beginner",
    temperature=0.2
)

print("Streaming response:")
for chunk in response_stream:
    print(chunk.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8'), end="", flush=True)
print()

print("\n4. Testing RAGEvaluator with Groq...")
evaluator = RAGEvaluator(model_name="llama-3.1-8b-instant")
eval_result = evaluator.evaluate_rag(
    query="Explain FastAPI dependency injection briefly.",
    retrieved_docs=context_docs,
    generated_answer="FastAPI dependency injection is declared using Depends().",
    latency_seconds=1.5
)
print("Evaluation Result:")
import json
print(json.dumps(eval_result, indent=2))
