"""Chatbot package initializer."""
from backend.chatbot.rag import RAGEngine
from backend.chatbot.openrouter import OpenRouterClient
from backend.chatbot.prompts import SYSTEM_INSTRUCTIONS, build_rag_messages

__all__ = [
    "RAGEngine",
    "OpenRouterClient",
    "SYSTEM_INSTRUCTIONS",
    "build_rag_messages",
]
