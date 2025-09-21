import logging
import asyncio
import os
from typing import List, Dict, Any
from pydantic import BaseModel
import google.generativeai as genai
from knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY environment variable")
genai.configure(api_key=GEMINI_API_KEY)

# Data models
class ChatMessage(BaseModel):
    role: str
    content: str

async def summarize_history(chat_history: List[ChatMessage]) -> str:
    """Summarize chat history using Gemini if too long."""
    if len(chat_history) <= 4:
        return ""
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        history_text = "\n".join([f"{msg.role}: {msg.content}" for msg in chat_history[-10:]])
        prompt = f"Summarize the following conversation concisely in up to 100 words:\n{history_text}"
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error summarizing chat history: {e}")
        return ""

async def generate_response(query: str, chat_history: List[ChatMessage], session_id: str, knowledge_bases: Dict[str, KnowledgeBase]) -> Dict[str, Any]:
    """Generate a response using Gemini directly with raw document content."""
    try:
        if session_id not in knowledge_bases or knowledge_bases[session_id].is_empty():
            return {
                "answer": "I don't have enough information to answer. Try refreshing the knowledge base with a specific topic. Maybe API Limit has exhausted.",
                "sources": []
            }
        
        # Extract raw documents from KnowledgeBase
        kb = knowledge_bases[session_id]
        documents = kb.documents  # Assuming documents is a list of SearchDocument objects
        if not documents:
            return {
                "answer": "No documents available to answer your query. Try refreshing the knowledge base.",
                "sources": []
            }

        # Prepare document context and sources
        doc_context = "\n\n".join([f"Document {i+1}: {doc.content}" for i, doc in enumerate(documents)])
        sources = [{"title": doc.title, "url": doc.url} for doc in documents if doc.url]

        # Summarize chat history
        history_summary = await summarize_history(chat_history)
        formatted_history = history_summary if history_summary else "\n".join(
            [f"{msg.role}: {msg.content}" for msg in chat_history[-4:]]
        )

        # Create prompt for Gemini
        prompt = f"""
        You are SCEPTRE (Smart Cognitive Engine for Preventing Tricks, Rumors & Errors), 
        an AI-powered assistant designed to combat misinformation and promote digital literacy. 

        Your job is to:
        1. Analyze the given content carefully using the provided context.
        2. Detect signals of potential misinformation, manipulation, or bias.
        3. Explain clearly *why* the content might be misleading (e.g., lack of credible sources, emotional manipulation, logical fallacies, unverifiable claims).
        4. Provide fact-based clarification or direct the user towards credible sources (when available).
        Keep the tone supportive, simple, and empowering. Keep your answer under 50-60 words.

        Context (from retrieved documents and sources):
        {doc_context}

        Chat History:
        {formatted_history}

        User Question or Content to Verify:
        {query}

        Answer (detailed, fact-aware, and user-friendly):
        """

        # Generate response using Gemini
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = await asyncio.to_thread(model.generate_content, prompt)
        answer = response.text if response else "I couldn't generate a response based on the provided information."

        return {
            "answer": answer,
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return {
            "answer": "I encountered an error while processing your request. Please try a more specific query.",
            "sources": []
        }