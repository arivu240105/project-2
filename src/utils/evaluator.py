import json
import time
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document
from src.utils.config import DATA_DIR, GROQ_API_KEY
from src.utils.logger import logger

class RAGEvaluator:
    """
    Evaluates the quality of retrieved contexts and generated answers.
    Computes Faithfulness, Context Relevance, and Answer Relevance.
    Saves evaluation logs to data/evaluation_history.json.
    """
    def __init__(self, api_key: str = None, model_name: str = "llama-3.1-8b-instant"):
        self.api_key = api_key or GROQ_API_KEY
        self.model_name = model_name
        self.history_file = DATA_DIR / "evaluation_history.json"
        self._init_history_file()

    def _init_history_file(self):
        """
        Creates the evaluation history JSON file if it doesn't exist.
        """
        if not self.history_file.exists():
            try:
                with open(self.history_file, "w", encoding="utf-8") as f:
                    json.dump([], f)
                logger.info(f"Initialized evaluation history file at {self.history_file}")
            except Exception as e:
                logger.error(f"Failed to initialize evaluation history file: {e}")

    def evaluate_rag(
        self, 
        query: str, 
        retrieved_docs: List[Document], 
        generated_answer: str,
        latency_seconds: float = 0.0
    ) -> Dict[str, Any]:
        """
        Queries Groq to rate Faithfulness, Context Relevance, and Answer Relevance.
        Saves scores to history log.
        """
        default_result = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "query": query,
            "faithfulness_score": 0.0,
            "faithfulness_reason": "Evaluation failed or key missing",
            "context_relevance_score": 0.0,
            "context_relevance_reason": "Evaluation failed or key missing",
            "answer_relevance_score": 0.0,
            "answer_relevance_reason": "Evaluation failed or key missing",
            "latency_seconds": latency_seconds,
            "chunks_count": len(retrieved_docs)
        }

        if not self.api_key or not retrieved_docs or not generated_answer:
            logger.warning("RAG evaluation skipped due to missing API key, docs, or answer.")
            return default_result

        try:
            logger.info("Starting LLM-assisted RAG evaluation using Groq...")
            
            # Format contexts
            contexts_text = "\n\n".join([f"Context [{idx+1}]: {doc.page_content}" for idx, doc in enumerate(retrieved_docs)])

            prompt = f"""
You are an independent RAG (Retrieval-Augmented Generation) system evaluator.
Analyze the User Query, the Retrieved Contexts, and the Generated Answer to calculate three metrics.
Output your evaluation ONLY as a valid JSON object matching this schema:
{{
    "faithfulness_score": float (between 0.0 and 1.0),
    "faithfulness_reason": "string explaining the faithfulness rating",
    "context_relevance_score": float (between 0.0 and 1.0),
    "context_relevance_reason": "string explaining the context relevance rating",
    "answer_relevance_score": float (between 0.0 and 1.0),
    "answer_relevance_reason": "string explaining the answer relevance rating"
}}

Definitions of metrics:
1. **Faithfulness**: Rate if the Generated Answer is fully grounded in the Retrieved Contexts. If the answer contains assertions/claims NOT backed by the context, lower the score. 1.0 means fully grounded.
2. **Context Relevance**: Rate how relevant and helpful the Retrieved Contexts are to answering the User Query. If contexts are irrelevant, lower the score. 1.0 means highly relevant.
3. **Answer Relevance**: Rate if the Generated Answer directly addresses the User Query. If it is vague or goes off-topic, lower the score. 1.0 means extremely relevant.

Inputs:
User Query: "{query}"

Retrieved Contexts:
{contexts_text}

Generated Answer:
"{generated_answer}"

Output JSON:"""

            import requests
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.0,
                "response_format": {"type": "json_object"},
                "stream": False
            }
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            response_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            result_json = json.loads(response_text)
            
            # Merge with base structure
            evaluation_result = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "query": query,
                "faithfulness_score": float(result_json.get("faithfulness_score", 0.0)),
                "faithfulness_reason": result_json.get("faithfulness_reason", "No reason provided"),
                "context_relevance_score": float(result_json.get("context_relevance_score", 0.0)),
                "context_relevance_reason": result_json.get("context_relevance_reason", "No reason provided"),
                "answer_relevance_score": float(result_json.get("answer_relevance_score", 0.0)),
                "answer_relevance_reason": result_json.get("answer_relevance_reason", "No reason provided"),
                "latency_seconds": latency_seconds,
                "chunks_count": len(retrieved_docs)
            }

            self._save_to_history(evaluation_result)
            logger.info("Successfully completed RAG evaluation and saved logs.")
            return evaluation_result


            
        except Exception as e:
            logger.error(f"Error during RAG evaluation: {e}")
            return default_result

    def _save_to_history(self, record: Dict[str, Any]):
        """
        Appends an evaluation record to the history JSON.
        """
        try:
            if not self.history_file.exists():
                self._init_history_file()
                
            with open(self.history_file, "r+", encoding="utf-8") as f:
                data = json.load(f)
                data.append(record)
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error writing to evaluation history JSON: {e}")

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Loads the entire evaluation history.
        """
        try:
            if self.history_file.exists():
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error reading evaluation history: {e}")
        return []

    def get_average_scores(self) -> Dict[str, float]:
        """
        Computes historical averages for RAG metrics.
        """
        history = self.get_history()
        if not history:
            return {
                "avg_faithfulness": 0.0,
                "avg_context_relevance": 0.0,
                "avg_answer_relevance": 0.0,
                "avg_latency": 0.0
            }
            
        total_faithfulness = 0.0
        total_context = 0.0
        total_answer = 0.0
        total_latency = 0.0
        
        for record in history:
            total_faithfulness += record.get("faithfulness_score", 0.0)
            total_context += record.get("context_relevance_score", 0.0)
            total_answer += record.get("answer_relevance_score", 0.0)
            total_latency += record.get("latency_seconds", 0.0)
            
        n = len(history)
        return {
            "avg_faithfulness": round(total_faithfulness / n, 2),
            "avg_context_relevance": round(total_context / n, 2),
            "avg_answer_relevance": round(total_answer / n, 2),
            "avg_latency": round(total_latency / n, 2)
        }
        
    def clear_history(self):
        """
        Clears the evaluation log.
        """
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump([], f)
            logger.info("Cleared evaluation history log.")
        except Exception as e:
            logger.error(f"Failed to clear evaluation history: {e}")
