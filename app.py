import streamlit as st
import pandas as pd
import time
import re
import os
from pathlib import Path

from src.vectorstore.store import VectorStoreManager
from src.retrieval.retriever import HybridRetriever
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.compressor import ContextCompressor
from src.llm impessor
from src.llm import GroqClient
from src.utils.evaluator import RAGEvaluator
from src.utils.logger import logger
from src.utils.config import VECTOR_DB_DIR, DATA_DIR
from src.ingestion.parser import
# 1. Page Configuration
st.set_page_config(
    page_title="DevDocs RAG Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.set_page_config(
    page_title="DevDocs RAG Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)
# 2. Premium Theme CSS injection
st.markdown("""
    <style>
        .reportview-container {
            background: #0e1117;
        }
        .main-header {
            font-size: 2.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 50%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
            text-align: left;
        }
        .subheader {
            color: #9ca3af;
            font-size: 1.1rem;
            margin-bottom: 1.5rem;
            font-weight: 400;
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 1.2rem;
            text-align: center;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(5px);
            -webkit-backdrop-filter: blur(5px);
            transition: transform 0.3s ease, border-color 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-3px);
            border-color: rgba(59, 130, 246, 0.5);
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 700;
            color: #3b82f6;
            margin-bottom: 0.3rem;
        }
        .metric-label {
            font-size: 0.85rem;
            font-weight: 600;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .feature-box {
            background: rgba(255, 255, 255, 0.02);
            border-left: 4px solid #8b5cf6;
            padding: 0.8rem;
            border-radius: 4px;
            margin-bottom: 0.8rem;
            font-size: 0.95rem;
        }
        .citation-box {
            background-color: rgba(59, 130, 246, 0.05);
            border: 1px solid rgba(59, 130, 246, 0.15);
            border-radius: 8px;
            padding: 0.8rem;
            margin-top: 0.5rem;
            font-size: 0.9rem;
        }
        
        /* Mobile-First Responsive Styles */
        @media (max-width: 768px) {
            .main-header {
                font-size: 1.8rem !important;
                text-align: center !important;
        rder-left: 4px solid #8b5cf6;
            padding: 0.8rem;
            border-radius: 4px;
            margin-bottom: 0.8rem;
            font-size: 0.95rem;
        }
        .citation-box {
            background-color: rgba(59, 130, 246, 0.05);
            border: 1px solid rgba(59, 130, 246, 0.15);
            border-radius: 8px;
            padding: 0.8rem;    }
            .subheader {
                font-size: 0.9rem !important;
                text-align: center !important;
                margin-bottom: 1rem !important;
            }
            
            .metric-label {
                font-size: 0.65rem !important;
                letter-spacing: 0.5px !important;
            }
            .feature-box {
                padding: 0.6rem !important;
                margin-bottom: 0.5rem !important;
                font-size: 0.85rem !important;
            }
            .citation-box {
                font-size: 0.8rem !important;
                padding: 0.5rem !important;
            }
            /* Make Streamlit tabs wider and easier to tap on mobile */
            div[data-baseweb="tab-list"] {
                flex-wrap: wrap !important;
                gap: 5px !important;
            }
            button[data-baseweb="tab"] {
                padding-left: 8px !important;
                padding-right: 8px !important;
                font-size: 0.85rem !important;
            }
        }
    </style>

""", unsafe_allow_html=True)

# 3. State Management
if "store_manager" not in st.session_state:
    st.session_state.store_manager = VectorStoreManager()
if "retriever" not in st.session_state:
    st.session_state.retriever = HybridRetriever(st.session_state.store_manager)
if "reranker" not in st.session_state:
    st.session_state.reranker = CrossEncoderReranker()
if "compressor" not in st.session_state:
    st.session_state.compressor = ContextCompressor()
if "groq_client" not in st.session_state:
    st.session_state.groq_client = GroqClient()
if "evaluator" not in st.session_state:
    st.session_state.evaluator = RAGEvaluator()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "debug_info" not in st.session_state:
    st.session_state.debug_info = {}

# Upload Directory setup
UPLOAD_DIR = DATA_DIR / "uploaded_files"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 4. Header Section
st.markdown("<div class='main-header'>DevDocs RAG Pro</div>", unsafe_allow_html=True)
st.markdown("<div class='subheader'>Secure Multi-Source Developer Documentation Assistant powered by Hybrid RAG</div>", unsafe_allow_html=True)

# 5. Sidebar Configuration Settings (NO API KEY MENTIONED AT ALL)
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("🤖 Model Settings")
    llm_model = st.selectbox(
        "Groq Model",
        options=["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "meta-llama/llama-4-scout-17b-16e-instruct"],
        index=0,
        help="Select the Groq model. 'llama-3.3-70b-versatile' is recommended for high quality and reasoning."
    )
    active_client = st.session_state.groq_client
    active_client.model_name = llm_model

    st.session_state.evaluator.model_name = llm_model
    from src.utils.config import GROQ_API_KEY
    st.session_state.evaluator.api_key = GROQ_API_KEY
    
    st.subheader("🎓 Conversation Mode")
    response_mode = st.selectbox(
        "Response Expertise",
        options=["Expert", "Beginner", "ELI5"],
        index=0,
        help="Expert: Detailed + full code; Beginner: Simple definitions; ELI5: Analogies."
    )
    
    st.subheader("🔍 Retrieval Settings")
    use_rewriter = st.toggle("Enable Query Rewriting", value=True, help="Converts follow-up questions to search queries using the LLM. Disable this for faster responses.")
    retrieve_k = st.slider("Retrieval K (Dense/Sparse)", min_value=5, max_value=40, value=20)
    
    use_rerank = st.toggle("Enable Cross-Encoder Reranking", value=True)
    rerank_k = st.slider("Rerank K to Keep", min_value=2, max_value=15, value=5, disabled=not use_rerank)
    
    use_compression = st.toggle("Enable Context Compression", value=True)
    max_words = st.slider("Max Words per Chunk", min_value=100, max_value=500, value=300, disabled=not use_compression)
    st.session_state.compressor.max_words_per_chunk = max_words

    st.subheader("🎛️ Hyperparameters")
    llm_temperature = st.slider("LLM Temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.05)

    st.subheader("🧹 Actions")
    if st.button("Reset Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.debug_info = {}
        st.rerun()

# 6. Global Stats Calculation (Loads cached stats instantly without importing PyTorch/Embeddings)
try:
    metadata = st.session_state.store_manager.get_cached_metadata()
    summary = metadata["sources_summary"]
    total_sources = metadata["total_sources"]
    total_chunks = metadata["total_chunks"]
    total_kb = metadata["total_kb"]
except Exception as e:
    summary = []
    total_sources = 0
    total_chunks = 0
    total_kb = 0.0


# 7. Tab Layout
tab_chat, tab_ingest, tab_analytics, tab_db_manage = st.tabs([
    "💬 Chat Assistant", 
    "📥 Ingestion Center", 
    "📊 Pipeline Analytics",
    "⚙️ Database Management"
])

# ----------------------------
# TAB 1: Chat Assistant
# ----------------------------
with tab_chat:
    # Check if database is empty
    if total_sources == 0:
        st.info("💡 **Welcome to DevDocs RAG Pro!** The vector index is currently empty. Head over to the **📥 Ingestion Center** tab to upload files or crawl documentation URLs to get started.")
    else:
        # Show stats banner
        banner_cols = st.columns(4)
        with banner_cols[0]:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_sources}</div><div class='metric-label'>Sources</div></div>", unsafe_allow_html=True)
        with banner_cols[1]:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_chunks}</div><div class='metric-label'>Chunks</div></div>", unsafe_allow_html=True)
        with banner_cols[2]:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_kb} KB</div><div class='metric-label'>Data Vol</div></div>", unsafe_allow_html=True)
        with banner_cols[3]:
            # Simple status metric
            st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#10b981'>Active</div><div class='metric-label'>RAG Engine</div></div>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)

        # Print history
        for idx, msg in enumerate(st.session_state.chat_history):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # User Query
        user_query = st.chat_input("Ask a technical question...")
        
        clicked_followup = None
        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "assistant":
            last_answer = st.session_state.chat_history[-1]["content"]
            if "### Follow-up Questions" in last_answer:
                parts = last_answer.split("### Follow-up Questions")
                followups = parts[-1].strip().split("\n")
                followup_questions = []
                for line in followups:
                    line_clean = line.strip().lstrip("-* ").lstrip("123. ")
                    if line_clean and line_clean.endswith("?"):
                        followup_questions.append(line_clean)
                
                if followup_questions:
                    st.write("**Suggested follow-up questions:**")
                    cols = st.columns(len(followup_questions))
                    for c_idx, q_text in enumerate(followup_questions):
                        with cols[c_idx]:
                            if st.button(q_text, key=f"fup_{len(st.session_state.chat_history)}_{c_idx}", use_container_width=True):
                                clicked_followup = q_text

        active_query = user_query or clicked_followup

        if active_query:
            with st.chat_message("user"):
                st.markdown(active_query)
            st.session_state.chat_history.append({"role": "user", "content": active_query})
            
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                start_time = time.time()
                
                active_client = st.session_state.groq_client
                
                # Query Rewriting
                if use_rewriter:
                    rewritten_query = active_client.rewrite_query(
                        active_query, st.session_state.chat_history[:-1]
                    )
                else:
                    rewritten_query = active_query
                
                # Retrieval
                raw_docs = st.session_state.retriever.retrieve(
                    query=rewritten_query, 
                    retrieve_k=retrieve_k
                )
                
                # Reranking
                if use_rerank and raw_docs:
                    reranked_docs = st.session_state.reranker.rerank(
                        query=rewritten_query, 
                        documents=raw_docs, 
                        rerank_k=rerank_k
                    )
                else:
                    reranked_docs = raw_docs[:rerank_k] if use_rerank else raw_docs
                    
                # Context Compression
                if use_compression and reranked_docs:
                    final_docs = st.session_state.compressor.compress(reranked_docs)
                else:
                    final_docs = reranked_docs
                    
                retrieval_latency = time.time() - start_time
                
                # Streaming generation
                full_response = ""
                try:
                    response_stream = active_client.generate_response_stream(
                        query=active_query,
                        context_docs=final_docs,
                        chat_history=st.session_state.chat_history[:-1],
                        mode=response_mode,
                        temperature=llm_temperature
                    )
                    
                    for token in response_stream:
                        full_response += token
                        response_placeholder.markdown(full_response + "▌")
                        
                    response_placeholder.markdown(full_response)
                except Exception as e:
                    logger.error(f"Error during response stream: {e}")
                    full_response = f"⚠️ **Error**: {e}"
                    response_placeholder.markdown(full_response)
                    
                generation_latency = time.time() - start_time - retrieval_latency
                total_latency = retrieval_latency + generation_latency
                
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                
                # Evaluation
                eval_result = {}
                if active_client.has_api_key() and final_docs:
                    eval_result = st.session_state.evaluator.evaluate_rag(
                        query=active_query,
                        retrieved_docs=final_docs,
                        generated_answer=full_response,
                        latency_seconds=total_latency
                    )

                st.session_state.debug_info = {
                    "rewritten_query": rewritten_query,
                    "raw_retrieval_count": len(raw_docs),
                    "reranked_count": len(reranked_docs),
                    "compressed_count": len(final_docs),
                    "retrieval_latency": retrieval_latency,
                    "generation_latency": generation_latency,
                    "raw_docs": raw_docs,
                    "reranked_docs": reranked_docs,
                    "compressed_docs": final_docs,
                    "eval_result": eval_result
                }
                st.rerun()

        # Download Panel
        if st.session_state.chat_history and st.session_state.debug_info:
            st.markdown("---")
            act_col1, act_col2 = st.columns(2)
            
            # Helper to generate PDF bytes
            def generate_pdf_bytes(history) -> bytes:
                from fpdf import FPDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", size=12)
                pdf.set_font("Helvetica", style="B", size=18)
                pdf.cell(200, 10, text="DevDocs RAG Pro - Chat History", ln=True, align="C")
                pdf.ln(10)
                
                for idx, msg in enumerate(history):
                    role = "User" if msg["role"] == "user" else "Assistant"
                    content = msg["content"]
                    clean_content = content.encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_font("Helvetica", style="B", size=12)
                    pdf.cell(200, 8, text=f"{role}:", ln=True)
                    pdf.set_font("Helvetica", size=10)
                    pdf.multi_cell(0, 5, text=clean_content)
                    pdf.ln(5)
                return bytes(pdf.output())

            def extract_citations_text(history) -> str:
                if not history:
                    return ""
                last_msg = history[-1]
                if last_msg["role"] != "assistant":
                    return ""
                content = last_msg["content"]
                parts = content.split("---")
                if len(parts) > 1:
                    return "Sources Cited in Last Answer:\n" + parts[-1].strip()
                return "No explicitly formatted sources section found in the last message."

            with act_col1:
                try:
                    pdf_data = generate_pdf_bytes(st.session_state.chat_history)
                    st.download_button(
                        label="📄 Export Chat History to PDF",
                        data=pdf_data,
                        file_name="devdocs_chat_history.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.warning(f"Could not generate PDF export: {e}")
                    
            with act_col2:
                citations_txt = extract_citations_text(st.session_state.chat_history)
                if citations_txt:
                    st.download_button(
                        label="📥 Download Answer Citations",
                        data=citations_txt,
                        file_name="answer_citations.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

            # RAG Pipeline Debugger
            with st.expander("🛠️ Real-Time RAG Pipeline Debugger"):
                db_info = st.session_state.debug_info
                t_col1, t_col2, t_col3 = st.columns(3)
                t_col1.metric("Query Rewrite", db_info.get("rewritten_query", "N/A"))
                t_col2.metric("Retrieval Latency", f"{db_info.get('retrieval_latency', 0.0):.2f}s")
                t_col3.metric("Generation Latency", f"{db_info.get('generation_latency', 0.0):.2f}s")
                
                eval_res = db_info.get("eval_result", {})
                if eval_res:
                    st.subheader("📊 RAG Evaluation Quality Metrics")
                    ev_col1, ev_col2, ev_col3 = st.columns(3)
                    ev_col1.metric("Faithfulness (Groundedness)", f"{eval_res.get('faithfulness_score', 0.0) * 100:.0f}%", help=eval_res.get("faithfulness_reason", ""))
                    ev_col2.metric("Context Relevance", f"{eval_res.get('context_relevance_score', 0.0) * 100:.0f}%", help=eval_res.get("context_relevance_reason", ""))
                    ev_col3.metric("Answer Relevance", f"{eval_res.get('answer_relevance_score', 0.0) * 100:.0f}%", help=eval_res.get("answer_relevance_reason", ""))
                
                tab_raw, tab_rank, tab_comp = st.tabs([
                    f"1. Raw Retrieval ({db_info.get('raw_retrieval_count', 0)})",
                    f"2. Cross-Encoder Reranked ({db_info.get('reranked_count', 0)})",
                    f"3. Compressed Context ({db_info.get('compressed_count', 0)})"
                ])
                
                with tab_raw:
                    for idx, doc in enumerate(db_info.get("raw_docs", [])):
                        st.markdown(f"**Chunk {idx+1} | Source:** `{doc.metadata.get('source')}` | **Page:** `{doc.metadata.get('page', 'N/A')}`")
                        st.code(doc.page_content[:400] + "...")
                with tab_rank:
                    for idx, doc in enumerate(db_info.get("reranked_docs", [])):
                        score = doc.metadata.get("rerank_score", 0.0)
                        st.markdown(f"**Chunk {idx+1} | Re-Rank Score:** `{score:.4f}` | **Source:** `{doc.metadata.get('source')}`")
                        st.code(doc.page_content[:400] + "...")
                with tab_comp:
                    for idx, doc in enumerate(db_info.get("compressed_docs", [])):
                        st.markdown(f"**Chunk {idx+1} | Source:** `{doc.metadata.get('source')}`")
                        st.code(doc.page_content)

# ----------------------------
# TAB 2: Ingestion Center
# ----------------------------
with tab_ingest:
    st.subheader("📥 Ingestion Center")
    st.write("Add documents to build your semantic search index.")
    
    subtab_file, subtab_web, subtab_github = st.tabs([
        "📄 Local PDF & Text Files", 
        "🌐 Website Crawler", 
        "🐙 GitHub Repository"
    ])
    
    # Text splitter settings
    st.markdown("---")
    st.markdown("**Ingestion Chunking Properties**")
    f_col1, f_col2 = st.columns(2)
    chunk_size = f_col1.number_input("Chunk Size (characters)", min_value=100, max_value=5000, value=1000)
    chunk_overlap = f_col2.number_input("Chunk Overlap (characters)", min_value=0, max_value=1000, value=200)
    
    # 1. Local files
    with subtab_file:
        st.write("Upload `.pdf`, `.md`, `.txt` documentation files.")
        uploaded_files = st.file_uploader("Choose files", type=["pdf", "md", "txt"], accept_multiple_files=True)
        if st.button("Process & Index Files", disabled=not uploaded_files, use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            parsed_documents = []
            
            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.write(f"Parsing ({idx+1}/{len(uploaded_files)}): {uploaded_file.name}...")
                save_path = UPLOAD_DIR / uploaded_file.name
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                docs = DocParser.parse(save_path)
                parsed_documents.extend(docs)
                progress_bar.progress(int((idx + 1) / len(uploaded_files) * 50))
                
            if parsed_documents:
                status_text.write("Chunking parsed documents...")
                splitter = DocSplitter(chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap))
                chunks = splitter.split_documents(parsed_documents)
                progress_bar.progress(70)
                status_text.write("Writing to FAISS vector database...")
                st.session_state.store_manager.add_documents(chunks)
                progress_bar.progress(100)
                st.success(f"Added {len(chunks)} chunks to FAISS vector store!")
                st.session_state.retriever.update_retrievers() # Rebuild retrievers
                time.sleep(1)
                st.rerun()
            else:
                st.error("No content could be parsed.")
            status_text.empty()
            
    # 2. Web Crawler
    with subtab_web:
        st.write("Crawl technical blogs or documentation URLs recursively.")
        target_url = st.text_input("Start URL", placeholder="https://fastapi.tiangolo.com/tutorial/")
        c_col1, c_col2 = st.columns(2)
        crawl_depth = c_col1.number_input("Recursion Depth", min_value=0, max_value=3, value=1)
        max_pages = c_col2.number_input("Max Pages Limit", min_value=1, max_value=100, value=20)
        
        if st.button("Crawl & Index Website", disabled=not target_url, use_container_width=True):
            if not target_url.startswith(("http://", "https://")):
                st.error("Please enter a valid URL.")
            else:
                status_text = st.empty()
                status_text.write(f"Crawling {target_url}...")
                try:
                    crawler = WebCrawler(max_depth=int(crawl_depth), max_pages=int(max_pages))
                    web_docs = crawler.crawl(target_url)
                    if web_docs:
                        status_text.write("Chunking crawled pages...")
                        splitter = DocSplitter(chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap))
                        chunks = splitter.split_documents(web_docs)
                        status_text.write("Writing to vector database...")
                        st.session_state.store_manager.add_documents(chunks)
                        st.success(f"Crawled {len(web_docs)} pages! Added {len(chunks)} chunks.")
                        st.session_state.retriever.update_retrievers() # Rebuild retrievers
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("No content could be retrieved.")
                except Exception as e:
                    st.error(f"Crawl failed: {e}")
                finally:
                    status_text.empty()
                    
    # 3. GitHub repository
    with subtab_github:
        st.write("Downloads Markdown files and folders from public repositories.")
        repo_url = st.text_input("Repository URL", placeholder="https://github.com/fastapi/fastapi")
        if st.button("Download & Index GitHub Repo", disabled=not repo_url, use_container_width=True):
            if "github.com" not in repo_url:
                st.error("Please provide a valid GitHub link.")
            else:
                status_text = st.empty()
                status_text.write("Downloading repo...")
                try:
                    downloader = GitHubDownloader(repo_url)
                    git_docs = downloader.load_documents()
                    if git_docs:
                        status_text.write("Chunking repository files...")
                        splitter = DocSplitter(chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap))
                        chunks = splitter.split_documents(git_docs)
                        status_text.write("Writing to FAISS vector store...")
                        st.session_state.store_manager.add_documents(chunks)
                        st.success(f"Loaded repo! Added {len(chunks)} chunks.")
                        st.session_state.retriever.update_retrievers() # Rebuild retrievers
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("No markdown files found.")
                except Exception as e:
                    st.error(f"Ingestion failed: {e}")
                finally:
                    status_text.empty()

# ----------------------------
# TAB 3: Pipeline Analytics
# ----------------------------
with tab_analytics:
    subtab_db_stats, subtab_eval_metrics, subtab_search_sandbox = st.tabs([
        "📈 Database Analytics",
        "🎯 RAG Quality Metrics",
        "🔍 Semantic Search Sandbox"
    ])
    
    with subtab_db_stats:
        st.subheader("Database Analytics")
        if summary:
            df = pd.DataFrame(summary)
            total_chunks = sum(df["chunks_count"])
            total_chars = sum(df["char_count"])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Indexed Chunks", total_chunks)
            col2.metric("Unique Sources", len(df))
            col3.metric("Total Characters", f"{total_chars:,}")
            
            st.markdown("---")
            plot_col1, plot_col2 = st.columns(2)
            
            with plot_col1:
                import plotly.express as px
                st.markdown("**Distribution by Ingestion Type**")
                type_counts = df.groupby("type")["chunks_count"].sum().reset_index()
                fig_pie = px.pie(type_counts, values="chunks_count", names="type", hole=0.4)
                fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with plot_col2:
                import plotly.express as px
                st.markdown("**Top Sources by Chunks Count**")
                top_sources = df.sort_values(by="chunks_count", ascending=False).head(8)
                fig_bar = px.bar(top_sources, x="chunks_count", y="title", orientation="h", color="type")
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Database is empty. Statistics will render once documents are ingested.")
            
    with subtab_eval_metrics:
        st.subheader("RAG Groundedness & Performance Metrics")
        eval_history = st.session_state.evaluator.get_history()
        
        if eval_history:
            avgs = st.session_state.evaluator.get_average_scores()
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Faithfulness", f"{avgs['avg_faithfulness'] * 100:.0f}%")
            m_col2.metric("Context Relevance", f"{avgs['avg_context_relevance'] * 100:.0f}%")
            m_col3.metric("Answer Relevance", f"{avgs['avg_answer_relevance'] * 100:.0f}%")
            m_col4.metric("Avg Latency", f"{avgs['avg_latency']:.2f}s")
            
            st.markdown("---")
            df_eval = pd.DataFrame(eval_history)
            df_eval["timestamp"] = pd.to_datetime(df_eval["timestamp"])
            df_eval = df_eval.sort_values(by="timestamp")
            
            st.markdown("**Quality Score Trends**")
            import plotly.graph_objects as go
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=df_eval["timestamp"], y=df_eval["faithfulness_score"], mode="lines+markers", name="Faithfulness", line=dict(color="#10b981")))
            fig_trend.add_trace(go.Scatter(x=df_eval["timestamp"], y=df_eval["context_relevance_score"], mode="lines+markers", name="Context Relevance", line=dict(color="#3b82f6")))
            fig_trend.add_trace(go.Scatter(x=df_eval["timestamp"], y=df_eval["answer_relevance_score"], mode="lines+markers", name="Answer Relevance", line=dict(color="#8b5cf6")))
            fig_trend.update_layout(xaxis_title="Time", yaxis_title="Score", yaxis=dict(range=[-0.05, 1.05]), margin=dict(t=20, b=20, l=40, r=20))
            st.plotly_chart(fig_trend, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Evaluation Logs")
            show_df = df_eval.rename(columns={
                "timestamp": "Timestamp",
                "query": "Query Asked",
                "faithfulness_score": "Faithfulness",
                "context_relevance_score": "Context Relevance",
                "answer_relevance_score": "Answer Relevance",
                "latency_seconds": "Latency (s)",
                "chunks_count": "Chunks"
            })
            st.dataframe(show_df[["Timestamp", "Query Asked", "Faithfulness", "Context Relevance", "Answer Relevance", "Latency (s)", "Chunks"]], use_container_width=True)
        else:
            st.info("Ask questions in the Chat tab to view evaluations and logs.")
            
    with subtab_search_sandbox:
        st.subheader("Vector DB Sandbox Search")
        search_query = st.text_input("Enter term to match vectors", placeholder="e.g. FastAPI tutorial")
        search_k = st.slider("Docs to Retrieve", min_value=1, max_value=20, value=5, key="sb_k")
        if st.button("Query Database Sandbox", disabled=not search_query, use_container_width=True):
            if st.session_state.store_manager.vector_store is None:
                st.error("Vector DB is empty.")
            else:
                try:
                    results = st.session_state.store_manager.vector_store.similarity_search_with_score(search_query, k=search_k)
                    for idx, (doc, score) in enumerate(results):
                        similarity = max(0.0, min(1.0, 1.0 - (score / 2.0)))
                        st.markdown(f"**Match {idx+1} | Source:** `{doc.metadata.get('source')}` | **L2 Distance:** `{score:.4f}` | **Similarity:** `{similarity*100:.1f}%`")
                        with st.expander("Show Chunk text"):
                            st.code(doc.page_content)
                except Exception as e:
                    st.error(f"Search failed: {e}")

# ----------------------------
# TAB 4: Database Management
# ----------------------------
with tab_db_manage:
    st.subheader("⚙️ Database Management")
    if summary:
        st.write("Current Document Index:")
        df_manage = pd.DataFrame(summary).rename(columns={
            "title": "Source Name",
            "type": "Ingest Type",
            "chunks_count": "Chunks",
            "char_count": "Characters",
            "source": "Location"
        })
        st.dataframe(df_manage, use_container_width=True)
    else:
        st.info("Database is empty.")
        
    st.markdown("---")
    st.warning("⚠️ **Danger Zone**: Wiping the database permanently deletes all index files and vectors from the disk.")
    if st.button("Wipe FAISS Index Database", type="secondary", use_container_width=True):
        try:
            if "retriever" in st.session_state:
                st.session_state.retriever.dense_retriever = None
                st.session_state.retriever.ensemble_retriever = None
                del st.session_state.retriever
            st.session_state.store_manager.reset_database()
            if "store_manager" in st.session_state:
                del st.session_state.store_manager
            st.success("Database wiped successfully!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Wipe failed: {e}")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #6b7280; font-size: 0.85rem;'>DevDocs RAG Pro • Portfolio-Grade AI Engineering</p>", unsafe_allow_html=True)
