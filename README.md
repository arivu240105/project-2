Projct 2 was a differ from rest of all projectsis an internship-grade, multi-source developer documentation assistant powered by Retrieval-Augmented Generation (RAG). It enables developers to ingest, index, search, and converse with local PDFs, text/markdown files, website URLs, and entire GitHub repositories. this can be create an interaction among the people

Built with Python, Streamlit, LangChain, FAISS, and Groq API, the platform includes advanced hybrid search pipelines, Cross-Encoder reranking, context compression, real-time citation matching, and dynamic response expertise levels (Expert, Beginner, ELI5).

---

## Key Features

- **📂 Multi-Source Ingestion**:
  - **Local Files**: Fast parsing and page indexing for PDFs and text/markdown files.
  - **Website Crawling**: Domain-locked, recursive crawler with depth limits and extraction of clean text.
  - **GitHub Repositories**: Automatic repository download (cloning or fallback ZIP extraction), scan for READMEs and docs folders.
- **🔄 Advanced Hybrid RAG Pipeline**:
  - **Embedding Generation**: Local vectorization with `BAAI/bge-small-en-v1.5`.
  - **Hybrid Search**: Combines semantic dense retrieval (FAISS) and lexical keyword matching (BM25) using reciprocal rank fusion (RRF).
  - **Cross-Encoder Reranking**: Re-evaluates top 20 retrieved chunks usinng `cross-encoder/ms-marco-MiniLM-L-6-v2` to select the top 5 most relevant context pieces.
  - **Context Compression**: Deduplicates repetitive sentences and truncates content blocks to keep the prompt clear and context-dense.
- **🧠 Advanced Conversational Orchestration**:
  - **Groq LLMs**: High-performance open models like Llama 3.3.
  - **Query Rewriting**: Contextualizes follow-up questions (e.g., "how does it work?" becomes "how does FastAPI dependency injection work?").
  - **Expertise Levels**: 
    - *Expert*: Dense explanation and production-grade code.
    - *Beginner*: Simple terms with comments on each line.
    - *ELI5*: Metric-driven metaphors, zero jargon.
  - **Citation Attribution**: Every answer links back to its exact file/page/URL block.
  - **Follow-up Suggestions**: Auto-generates 3 relevant followup prompts.
- **📊 Analytics & Pipeline Debugging**:
  - **Visual Ingestion Metrics**: Monitor indexed document distributions and size metrics.
  - **RAG Quality Evaluation**: Evaluates Groundedness/Faithfulness, Search Precision, and Answer Relevance.
  - **Semantic Sandbox**: Query vectors directly and inspect L2 distance scores.

---

## System Architecture

```
                    ┌────────────────────────┐
                    │  Data Sources Ingest   │
                    │ (Files, Web, GitHub)   │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │ Recursive Character    │
                    │ Text Splitter          │
                    └───────────┬────────────┘
                                │ Chunks
                                ▼
                    ┌────────────────────────┐
                    │   Embedding Model:     │     Store
                    │   bge-small-en-v1.5    ├─────────────┐
                    └────────────────────────┘             │
                                                           ▼
┌──────────────┐    ┌────────────────────────┐    ┌────────────────┐
│  User Query  │───►│  Query Rewriter (Groq) ├───►│  Vector Store  │
└──────────────┘    └────────────────────────┘    │    (FAISS)     │
                                                  └────────┬───────┘
                                                           │
                                                           ▼
┌──────────────┐    ┌────────────────────────┐    ┌────────────────┐
│ Cited Stream │◄───│   Groq LLM (Llama)     │◄───│ Hybrid Search  │
│  + Followups │    │     Generations        │    │  (Dense+Sparse)│
└──────────────┘    └────────────────────────┘    └────────┬───────┘
                                                           │
                                                           ▼
                                                  ┌────────────────┐
                                                  │ Cross-Encoder  │
                                                  │   Reranking    │
                                                  └────────┬───────┘
                                                           │
                                                           ▼
                                                  ┌────────────────┐
                                                  │    Context     │
                                                  │  Compression   │
                                                  └────────────────┘
```

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Git CLI (optional, falls back to downloading ZIP archives)

### 1. Clone & Set Up Workspace
```bash
git clone <repository-url>
cd devdocs-rag-pro
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file in the root directory based on the `.env.example` file:
```bash
cp .env.example .env
```
Open `.env` and configure your Groq API Key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

For Streamlit, you can also store the key securely in `.streamlit/secrets.toml`:
```toml
[GROQ]
API_KEY = "your_groq_api_key_here"
```

### 5. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## Directory Structure

```
devdocs-rag-pro/
├── .env.example               # Config template
├── README.md                  # Detailed overview
├── app.py                     # Main dashboard page
├── requirements.txt           # Project dependencies
├── logs/                      # System logs
│   └── devdocs_rag.log        # Dual console/file handler output
├── pages/                     # Streamlit multi-page setup
│   ├── 1_💬_Chat_Interface.py
│   ├── 2_📥_Ingestion_Center.py
│   └── 3_📊_Analytics_&_Debugger.py
└── src/                       # Application code
    ├── ingestion/             # Loaders, Web crawler, Splitters
    ├── llm/                   # Groq setup & templates
    ├── retrieval/             # Hybrid search, reranking, compressors
    ├── utils/                 # Config loader, Evaluator, Logger
    └── vectorstore/           # FAISS manager
```

---

## Evaluation & Metrics Dashboard

The application runs a lightweight evaluation utility using Groq to automatically check:
1. **Faithfulness**: Verifies if the model's response contains assertions unsupported by the context.
2. **Context Relevance**: Measures if the retriever successfully extracted documents containing terms helpful for answering the prompt.
3. **Answer Relevance**: Checks if the response addresses the prompt directly.

Average scores are visualised over time in the **Analytics** tab along with detailed latency benchmarks, enabling developers to tune chunk sizes, overlap parameters, and retrieval settings.
