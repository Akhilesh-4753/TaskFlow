"""
Groq AI service module.
All API communication is done server-side. Never expose the API key to the browser.
"""

import os
import requests
import logging
from django.conf import settings

logger = logging.getLogger('assistant')

GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY_MESSAGES = 10

PLACEHOLDER_KEYS = {
    '',
    'your-groq-api-key-here',
    'your_groq_api_key_here',
    'gsk_your_groq_api_key_here',
    'your_api_key_here',
}


class GroqClient:
    """
    Groq AI Client wrapper.
    Securely manages Groq API credentials loaded via os.getenv() / django settings,
    manages HTTP sessions, handles API requests, and provides logging and error handling.
    """

    def __init__(self, api_key: str = None, model: str = None, api_url: str = None):
        self._custom_api_key = str(api_key).strip() if api_key is not None else None
        self._custom_model = str(model).strip() if model is not None else None
        self.api_url = api_url or getattr(settings, 'GROQ_API_URL', GROQ_API_URL)

        if not self.is_configured():
            logger.error(
                "AI service is not configured. GROQ_API_KEY is missing or empty in .env. "
                "Please configure a valid GROQ_API_KEY in your .env file."
            )
        else:
            masked_key = self.api_key[:6] + '...' + self.api_key[-4:] if len(self.api_key) > 10 else '***'
            logger.info("GroqClient initialized successfully (model: %s, key: %s).", self.model, masked_key)

    @property
    def api_key(self) -> str:
        if self._custom_api_key is not None:
            return self._custom_api_key
        key = getattr(settings, 'GROQ_API_KEY', None)
        if key is None or not str(key).strip():
            key = os.getenv('GROQ_API_KEY', '')
        return str(key or '').strip()

    @property
    def model(self) -> str:
        if self._custom_model is not None:
            return self._custom_model
        m = getattr(settings, 'GROQ_MODEL', None)
        if m is None or not str(m).strip():
            m = os.getenv('GROQ_MODEL', 'llama3-8b-8192')
        return str(m or 'llama3-8b-8192').strip()

    def is_configured(self) -> bool:
        """Check if client has a valid, non-placeholder API key."""
        return is_groq_configured()

    def get_headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

    def chat_completion(self, messages: list, max_tokens: int = 500, temperature: float = 0.8, timeout: int = 20) -> dict:
        """Send chat completion request to Groq API with robust error handling."""
        if not self.is_configured():
            logger.error("AI service configuration error: GROQ_API_KEY is not configured in .env.")
            return {'success': False, 'error': 'AI service is not configured. Please add your GROQ_API_KEY.'}

        payload = {
            'model': self.model,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
        }

        try:
            response = requests.post(
                self.api_url,
                headers=self.get_headers(),
                json=payload,
                timeout=timeout,
            )

            if response.status_code == 401:
                logger.error("Groq API 401 Unauthorized: Invalid GROQ_API_KEY. Please verify the key in your .env file.")
                return {'success': False, 'error': 'AI service authentication failed. Invalid GROQ_API_KEY.'}
            elif response.status_code == 429:
                logger.warning("Groq API 429 Rate Limit exceeded.")
                return {'success': False, 'error': 'AI service rate limit reached. Please wait a moment and try again.'}

            response.raise_for_status()
            data = response.json()
            reply = data['choices'][0]['message']['content'].strip()
            return {'success': True, 'content': reply}

        except requests.exceptions.Timeout:
            logger.error('Groq API request timed out after %ds', timeout)
            return {'success': False, 'error': 'AI service timed out. Please try again.'}
        except requests.exceptions.RequestException as e:
            logger.error('Groq API request error: %s', e)
            return {'success': False, 'error': 'AI service is currently unavailable.'}
        except (KeyError, IndexError, ValueError) as e:
            logger.error('Groq API response parsing error: %s', e)
            return {'success': False, 'error': 'Unexpected response from AI service.'}


_client_instance = None


def get_groq_client() -> GroqClient:
    """Return an initialized GroqClient instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = GroqClient()
    return _client_instance


def is_groq_configured() -> bool:
    """Check if Groq API is properly configured."""
    key = getattr(settings, 'GROQ_API_KEY', None)
    if key is None or not str(key).strip():
        key = os.getenv('GROQ_API_KEY', '')
    cleaned = str(key or '').strip()
    if not cleaned or cleaned.lower() in PLACEHOLDER_KEYS:
        return False
    return True


def get_task_description_suggestion(title: str, user=None) -> dict:
    """
    Generate a task description suggestion using Groq API.
    Returns {'success': True, 'description': '...'} or {'success': False, 'error': '...'}
    """
    if not is_groq_configured():
        return {'success': False, 'error': 'AI service is not configured. Please add your GROQ_API_KEY.'}

    if not title or len(title.strip()) < 3:
        return {'success': False, 'error': 'Please enter a task title first.'}

    system_prompt = (
        "You are a productivity assistant. When given a task title, "
        "write a clear, concise, and actionable task description in 2-4 sentences. "
        "Focus on what needs to be done, why it matters, and any key steps. "
        "Do not include the title in the description. Keep it professional and practical."
    )

    client = get_groq_client()
    result = client.chat_completion(
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'Write a description for this task: {title.strip()}'},
        ],
        max_tokens=300,
        temperature=0.7,
        timeout=15,
    )
    if result.get('success'):
        return {'success': True, 'description': result['content']}
    return result


def get_chat_response(user_message: str, conversation_history: list, user=None) -> dict:
    """
    Get a chat response from Groq AI.
    conversation_history: list of {'role': 'user'|'assistant', 'content': str}
    Returns {'success': True, 'response': '...'} or {'success': False, 'error': '...'}
    """
    if not is_groq_configured():
        return {'success': False, 'error': 'AI service is not configured. Please add your GROQ_API_KEY.'}

    if not user_message or len(user_message.strip()) < 1:
        return {'success': False, 'error': 'Please enter a message.'}

    if len(user_message) > MAX_MESSAGE_LENGTH:
        return {'success': False, 'error': f'Message is too long (max {MAX_MESSAGE_LENGTH} characters).'}

    # Build a safe, controlled system prompt
    system_prompt = (
        "You are TaskFlow AI, a helpful productivity assistant integrated into the TaskFlow task management application. "
        "You help users organize tasks, set priorities, improve productivity, break down complex work, and stay focused. "
        "Be concise, practical, and encouraging. If users ask about their tasks, remind them they can view details in the app. "
        "Do not make up task data. Do not execute code, access databases, or perform system operations."
    )

    # Add user context if available
    if user and user.is_authenticated:
        from tasks.models import Task
        task_count = Task.objects.filter(user=user).count()
        pending_count = Task.objects.filter(user=user, completed=False).count()
        system_prompt += f"\n\nUser context: {user.first_name or user.username} has {task_count} total tasks, {pending_count} pending."

    # Limit history to prevent token overflow
    safe_history = []
    for msg in conversation_history[-MAX_HISTORY_MESSAGES:]:
        role = msg.get('role', '')
        content = str(msg.get('content', ''))[:MAX_MESSAGE_LENGTH]
        if role in ('user', 'assistant') and content:
            safe_history.append({'role': role, 'content': content})

    messages = [{'role': 'system', 'content': system_prompt}]
    messages.extend(safe_history)
    messages.append({'role': 'user', 'content': user_message.strip()})

    client = get_groq_client()
    result = client.chat_completion(
        messages=messages,
        max_tokens=500,
        temperature=0.8,
        timeout=20,
    )
    if result.get('success'):
        return {'success': True, 'response': result['content']}
    return result


