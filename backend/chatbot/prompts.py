"""System prompts and prompt construction templates for the Estate Intelligence AI RAG Chatbot."""
from typing import Any, Dict, List
from backend.models.schemas import ChatMessage

SYSTEM_INSTRUCTIONS = """You are an AI real estate research assistant specializing in publicly available information from DarGlobal and Wasalt.

Answer questions exclusively using information retrieved from the indexed knowledge base.

Always:

1. Provide accurate, relevant, and understandable answers.
2. Distinguish between DarGlobal and Wasalt information.
3. Cite the source website and provide clickable source URLs.
4. Never invent prices, availability, project specifications, amenities, or payment plans.
5. Clearly state when information is unavailable or cannot be verified.
6. If asked to compare projects, organize the comparison into clear categories.
7. If the user asks about something outside the indexed data, explain the limitation rather than guessing.
8. Distinguish between confirmed facts and information that may have changed.
9. Never claim that a property is currently available unless the indexed source explicitly confirms it.
10. Use a professional, helpful, conversational tone.

Formatting Rules:
- Always format source links as clickable Markdown links: [Project Name — Source Website](URL).
- When comparing projects or platforms, include a structured Markdown table alongside categorized bullet points.
- Never fabricate any figure, price, payment plan, or completion date not explicitly present in the retrieved context."""


def build_rag_messages(
    user_query: str,
    retrieved_chunks: List[Dict[str, Any]],
    history: List[ChatMessage],
) -> List[Dict[str, str]]:
    """Construct the OpenRouter chat completion message list with retrieved RAG context and conversation history."""
    context_blocks: List[str] = []
    for idx, ch in enumerate(retrieved_chunks, start=1):
        meta = ch.get("metadata", {})
        block = (
            f"--- RETRIEVED SOURCE #{idx} (Score: {ch.get('score', 0.0):.3f}) ---\n"
            f"Source Website: {meta.get('source_website', 'Unknown')}\n"
            f"Project Name: {meta.get('project_name', 'Unknown')}\n"
            f"Location: {meta.get('location', 'Unknown')}\n"
            f"Developer: {meta.get('developer', 'Unknown')}\n"
            f"Status: {meta.get('status', 'Unknown')}\n"
            f"Completion Timeline: {meta.get('completion_info', 'Not publicly specified')}\n"
            f"Pricing: {meta.get('pricing', 'Available on request')}\n"
            f"Payment Plan: {meta.get('payment_plan', 'Available on request')}\n"
            f"Original URL: {meta.get('page_url', '')}\n"
            f"Content: {ch.get('text', '')}\n"
        )
        context_blocks.append(block)

    formatted_context = "\n".join(context_blocks) if context_blocks else "NO MATCHING SOURCES FOUND IN KNOWLEDGE BASE."

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
    ]

    # Include up to last 6 turns of conversation history for context awareness
    for msg in history[-6:]:
        messages.append({"role": msg.role, "content": msg.content})

    user_prompt = (
        f"RETRIEVED KNOWLEDGE BASE CONTEXT (DarGlobal & Wasalt):\n"
        f"{formatted_context}\n\n"
        f"USER QUESTION:\n{user_query}\n\n"
        f"Instructions: Answer the user's question strictly using the retrieved context above. "
        f"Clearly distinguish between DarGlobal and Wasalt, cite every referenced project with its clickable Markdown URL "
        f"[Project Name](URL), and explicitly state if any requested detail (such as exact unit pricing or payment plan) "
        f"is not publicly listed in the indexed sources."
    )
    messages.append({"role": "user", "content": user_prompt})
    return messages
