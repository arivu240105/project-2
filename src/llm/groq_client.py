import os
import requests
import json
from typing import List, Dict, Any, Generator
from langchain_core.documents import Document
from src.utils.config import GROQ_API_KEY
from src.utils.logger import logger

class GroqClient:
    """
    Manages communication with Groq models (e.g., Llama, Mixtral).
    Handles conversation history, query rewriting, system prompt switching,
    streaming, citations, and follow-up questions.
    """
    def __init__(self, api_key: str = None, model_name: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or GROQ_API_KEY
        self.model_name = model_name
        self._setup_client()

    def _setup_client(self):
        """
        Validates that the API key is present.
        """
        if self.api_key:
            logger.info("Groq API client configured successfully.")
        else:
            logger.warning("No Groq API key provided. LLM calls will fail until configured.")

    def set_api_key(self, api_key: str):
        """
        Updates the API key dynamically.
        """
        self.api_key = api_key
        self._setup_client()

    def has_api_key(self) -> bool:
        return bool(self.api_key)

    def rewrite_query(self, query: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Rewrites conversational queries to make them self-contained for search/retrieval.
        """
        if not self.api_key:
            return query
            
        if not chat_history:
            return query

        try:
            logger.info("Rewriting user query using Groq based on chat history...")
            
            # Format chat history for context
            history_text = ""
            for msg in chat_history[-4:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_text += f"{role}: {msg['content']}\n"
                
            prompt = f"""
Given the following conversation history and a follow-up query, rewrite the follow-up query to be a self-contained search query. 
Do NOT answer the query. Just output the rewritten query. If the query is already self-contained, output it unchanged.

Conversation History:
{history_text}

Follow-up Query: {query}

Rewritten self-contained search query:"""

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
                "stream": False
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            res_json = response.json()
            rewritten = res_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            if rewritten.startswith('"') and rewritten.endswith('"'):
                rewritten = rewritten[1:-1]
            logger.info(f"Original query: '{query}' -> Rewritten: '{rewritten}'")
            return rewritten
        except Exception as e:
            logger.error(f"Error rewriting query with Groq: {e}. Using original query.")
            return query

    def _get_system_instructions(self, mode: str) -> str:
        """
        Returns system instructions based on the selected mode (Expert, Beginner, ELI5).
        """
        base_instructions = """You are 'DevDocs RAG Pro', a professional AI developer documentation assistant.
Your goal is to answer technical questions using the provided context chunks.
CRITICAL RULES:
1. Answer the question based ONLY on the provided context. If the context does not contain enough details to answer, say: "I'm sorry, but the provided documentation does not contain enough information to answer that question." Do not make up facts.
2. Cite your sources. Whenever you refer to facts or code snippets from the context, use inline numerical citations like [Source 1], [Source 2], etc., corresponding to the numbered context blocks.
3. At the very end of your response, after your answer, output a dedicated markdown horizontal rule '---' and then list the numbered sources you cited in this format:
Source [number]: <file_name/url/repo> | Page: <page_number or N/A> | Section: <title or section name>
4. Include exactly 3 suggested follow-up questions at the very bottom under a header '### Follow-up Questions' (after the sources section). Make them relevant, brief, and interesting.
"""

        if mode.lower() == "expert":
            mode_instructions = """
MODE: EXPERT
- Provide highly technical, dense, and precise explanations.
- Explain internal mechanics, architecture, performance implications, and structural design.
- Generate complete, production-grade code snippets. Use descriptive variable names, handle exceptions, and add minimal but critical inline comments.
- Do not simplify complex concepts; use industry-standard terminology.
"""
        elif mode.lower() == "beginner":
            mode_instructions = """
MODE: BEGINNER
- Explain concepts using clear, accessible language.
- Introduce technical terms gently and define them immediately.
- Break down procedures into step-by-step instructions.
- Provide simple, focused, and clean code examples with comments explaining what every line does.
"""
        elif mode.lower() == "eli5":
            mode_instructions = """
MODE: ELI5 (Explain Like I'm Five)
- Explain the concept using simple, real-world metaphors and analogies (e.g., "Think of API endpoints like waiters in a restaurant").
- Avoid complex technical jargon entirely. If a term is absolutely necessary, explain it with a simple analogy.
- Keep explanation structures very simple and narrative.
- Keep code examples extremely basic or omit them if the analogy is sufficient, or explain the code like a recipe.
"""
        else:
            mode_instructions = "\nMode: General standard technical response."

        return base_instructions + mode_instructions

    def generate_response_stream(
        self, 
        query: str, 
        context_docs: List[Document], 
        chat_history: List[Dict[str, str]], 
        mode: str = "expert",
        temperature: float = 0.2
    ) -> Generator[str, None, None]:
        """
        Constructs the prompt, queries Groq API, and yields response tokens as a stream.
        """
        if not self.api_key:
            yield "⚠️ **Error**: Groq API Key is not configured. Please add it to your `.env` file."
            return

        try:
            # 1. Format Context Blocks
            context_text = ""
            for idx, doc in enumerate(context_docs):
                source = doc.metadata.get("source", "Unknown")
                page = doc.metadata.get("page", "N/A")
                title = doc.metadata.get("title", "N/A")
                
                context_text += f"--- Context Block [Source {idx + 1}] ---\n"
                context_text += f"Source URL/Path: {source}\n"
                context_text += f"Page: {page}\n"
                context_text += f"Section/Title: {title}\n"
                context_text += f"Content:\n{doc.page_content}\n\n"

            # 2. Build Messages Payload
            system_instruction = self._get_system_instructions(mode)
            messages = [
                {"role": "system", "content": system_instruction}
            ]
            
            # Format/add chat history
            for msg in chat_history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
                
            # Add user query with context
            user_content = f"""Provided Documentation Context:
{context_text}

User Query: {query}

Instructions: Analyze the provided documentation context above. Answer the User Query in '{mode.upper()}' mode. Remember to cite inline, list sources at the bottom, and provide 3 follow-up questions."""
            
            messages.append({"role": "user", "content": user_content})

            logger.info(f"Querying Groq Model {self.model_name} (temperature={temperature}, mode={mode})...")

            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "stream": True
            }

            response = requests.post(url, headers=headers, json=payload, stream=True, timeout=15)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8').strip()
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            delta = data_json.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            pass
                            
            logger.info("Successfully received full streaming response from Groq.")
        except Exception as e:
            logger.error(f"Error generating response from Groq: {e}")
            yield f"⚠️ **Error**: An error occurred while generating a response: {str(e)}"
