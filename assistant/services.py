"""
Groq AI service wrapper (legacy module).
Now delegates to the centralized TaskFlow AI package (ai.services).
Preserved for backward compatibility.
"""

from ai.services import (
    GroqClient,
    get_groq_client,
    generate_chat_response as get_chat_response,
    generate_task_suggestion,
    get_groq_api_key,
    get_groq_model,
    GROQ_API_URL,
    MAX_MESSAGE_LENGTH,
    MAX_HISTORY_MESSAGES,
    PLACEHOLDER_KEYS,
)
import ai.services


def is_groq_configured() -> bool:
    """Check if Groq API is configured. Delegates to ai.services."""
    key = get_groq_api_key()
    if not key or key.lower() in PLACEHOLDER_KEYS:
        return False
    return True


def get_task_description_suggestion(title: str, user=None) -> dict:
    """
    Backward-compatible wrapper for task description suggestion.
    Delegates to ai.services.generate_task_suggestion.
    """
    return generate_task_suggestion(topic=title, user=user)

