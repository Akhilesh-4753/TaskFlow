"""
TaskFlow AI — Centralized Groq AI Service.
Responsible for client initialization, API communication, error handling,
and executing chatbot, task suggestion, and learning roadmap workflows.
"""

import os
from pathlib import Path
import logging
import requests
from dotenv import load_dotenv
from django.conf import settings

from .prompts import (
    get_chatbot_system_prompt,
    get_task_suggestion_prompt,
    get_learning_roadmap_prompt,
    get_technical_assistance_prompt,
)

logger = logging.getLogger('assistant')

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env', override=False)

GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
DEFAULT_GROQ_MODEL = 'openai/gpt-oss-20b'
MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY_MESSAGES = 10

PLACEHOLDER_KEYS = {
    '',
    'your-groq-api-key-here',
    'your_groq_api_key_here',
    'gsk_your_groq_api_key_here',
    'your_api_key_here',
}


def get_groq_api_key() -> str:
    """Retrieve GROQ_API_KEY from settings or .env securely, stripping whitespace and quotes."""
    key = getattr(settings, 'GROQ_API_KEY', None)
    if key is None or not str(key).strip():
        load_dotenv(BASE_DIR / '.env')
        key = os.getenv('GROQ_API_KEY', '')
    return str(key or '').strip().strip('\'"')


def get_groq_model() -> str:
    """Retrieve GROQ_MODEL from settings or .env, defaulting to an active supported model."""
    m = getattr(settings, 'GROQ_MODEL', None)
    if m is None or not str(m).strip() or str(m).strip() == 'llama3-8b-8192':
        load_dotenv(BASE_DIR / '.env')
        m = os.getenv('GROQ_MODEL', DEFAULT_GROQ_MODEL)
    cleaned = str(m or DEFAULT_GROQ_MODEL).strip().strip('\'"')
    # Gracefully upgrade decommissioned llama3-8b-8192 model
    if cleaned == 'llama3-8b-8192':
        cleaned = DEFAULT_GROQ_MODEL
    return cleaned


def is_groq_configured() -> bool:
    """Check if Groq API is properly configured with a real API key."""
    import sys
    # Honor mock patches on legacy assistant.services.is_groq_configured if active in tests
    asst_mod = sys.modules.get('assistant.services')
    if asst_mod and hasattr(asst_mod, 'is_groq_configured') and asst_mod.is_groq_configured is not is_groq_configured:
        try:
            return bool(asst_mod.is_groq_configured())
        except Exception:
            pass

    key = get_groq_api_key()
    if not key or key.lower() in PLACEHOLDER_KEYS:
        return False
    return True


class GroqClient:
    """
    Groq AI Client wrapper.
    Securely manages Groq API credentials loaded via os.getenv() / django settings,
    manages HTTP communication, and provides centralized logging and error handling.
    """

    def __init__(self, api_key: str = None, model: str = None, api_url: str = None):
        self._custom_api_key = str(api_key).strip().strip('\'"') if api_key is not None else None
        self._custom_model = str(model).strip().strip('\'"') if model is not None else None
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
        return get_groq_api_key()

    @property
    def model(self) -> str:
        if self._custom_model is not None:
            return self._custom_model
        return get_groq_model()

    def is_configured(self) -> bool:
        """Check if client has a valid, non-placeholder API key."""
        if self._custom_api_key is not None:
            return bool(self._custom_api_key and self._custom_api_key.lower() not in PLACEHOLDER_KEYS)
        return is_groq_configured()

    def get_headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

    def chat_completion(
        self,
        messages: list,
        max_tokens: int = 600,
        temperature: float = 0.7,
        timeout: int = 25
    ) -> dict:
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
            elif response.status_code == 400:
                data = response.json() if response.text else {}
                err_msg = data.get('error', {}).get('message', '')
                if 'decommissioned' in err_msg.lower():
                    logger.warning("Groq model decommissioned: %s. Falling back to %s", self.model, DEFAULT_GROQ_MODEL)
                    # Retry once with default model
                    payload['model'] = DEFAULT_GROQ_MODEL
                    retry_res = requests.post(self.api_url, headers=self.get_headers(), json=payload, timeout=timeout)
                    if retry_res.status_code == 200:
                        content = retry_res.json()['choices'][0]['message']['content'].strip()
                        return {'success': True, 'content': content}

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
    """Return an initialized GroqClient instance, refreshing if credentials changed."""
    global _client_instance
    current_key = get_groq_api_key()
    if _client_instance is None or _client_instance.api_key != current_key:
        _client_instance = GroqClient()
    return _client_instance


def generate_chat_response(user_message: str, conversation_history: list = None, user=None) -> dict:
    """
    Get a chat response from Groq AI using the centralized learning mentor
    and productivity assistant instruction architecture.
    """
    if not is_groq_configured():
        return {'success': False, 'error': 'AI service is not configured. Please add your GROQ_API_KEY.'}

    if not user_message or len(user_message.strip()) < 1:
        return {'success': False, 'error': 'Please enter a message.'}

    if len(user_message) > MAX_MESSAGE_LENGTH:
        return {'success': False, 'error': f'Message is too long (max {MAX_MESSAGE_LENGTH} characters).'}

    system_prompt = get_chatbot_system_prompt(user=user)

    # Process and sanitize conversation history
    safe_history = []
    if conversation_history and isinstance(conversation_history, list):
        for msg in conversation_history[-MAX_HISTORY_MESSAGES:]:
            if isinstance(msg, dict):
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
        max_tokens=800,
        temperature=0.7,
        timeout=25,
    )
    if result.get('success'):
        return {'success': True, 'response': result['content']}
    return result


def generate_task_suggestion(topic: str, user=None) -> dict:
    """
    Generate a simple, meaningful, actionable task description from a user-provided topic.
    Returns {'success': True, 'description': '...', 'title': '...'} or {'success': False, 'error': '...'}
    """
    if not is_groq_configured():
        return {'success': False, 'error': 'AI service is not configured. Please add your GROQ_API_KEY.'}

    cleaned_topic = (topic or '').strip()
    if not cleaned_topic or len(cleaned_topic) < 2:
        return {'success': False, 'error': 'Please enter a topic or title first.'}

    messages = get_task_suggestion_prompt(cleaned_topic)
    client = get_groq_client()
    result = client.chat_completion(
        messages=messages,
        max_tokens=500,
        temperature=0.5,
        timeout=15,
    )

    if result.get('success'):
        raw = result['content'].strip()
        # Clean any accidental outer quotes or markdown artifacts
        cleaned = raw.strip('\'"`').strip()
        if cleaned.lower().startswith('task:'):
            cleaned = cleaned[5:].strip()

        # Generate a short sensible title fallback if needed
        words = cleaned_topic.split()
        if len(words) <= 4:
            suggested_title = f"Practice {cleaned_topic.title()}" if not cleaned_topic.lower().startswith(('practice', 'build', 'create', 'learn')) else cleaned_topic.capitalize()
        else:
            suggested_title = " ".join(words[:4]).capitalize()

        return {
            'success': True,
            'description': cleaned,
            'title': suggested_title,
        }
    return result


def generate_learning_roadmap(topic: str) -> dict:
    """
    Generate a structured 3-level learning roadmap for a technology or skill.
    """
    if not is_groq_configured():
        return {'success': False, 'error': 'AI service is not configured. Please add your GROQ_API_KEY.'}

    cleaned_topic = (topic or '').strip()
    if not cleaned_topic or len(cleaned_topic) < 2:
        return {'success': False, 'error': 'Please provide a valid technology or topic.'}

    messages = get_learning_roadmap_prompt(cleaned_topic)
    client = get_groq_client()
    result = client.chat_completion(
        messages=messages,
        max_tokens=900,
        temperature=0.7,
        timeout=25,
    )
    if result.get('success'):
        return {'success': True, 'roadmap': result['content']}
    return result


def generate_technical_assistance(query: str) -> dict:
    """
    Generate step-by-step technical problem solving with code examples.
    """
    if not is_groq_configured():
        return {'success': False, 'error': 'AI service is not configured. Please add your GROQ_API_KEY.'}

    cleaned_query = (query or '').strip()
    if not cleaned_query:
        return {'success': False, 'error': 'Please enter a technical question.'}

    messages = get_technical_assistance_prompt(cleaned_query)
    client = get_groq_client()
    result = client.chat_completion(
        messages=messages,
        max_tokens=750,
        temperature=0.7,
        timeout=25,
    )
    if result.get('success'):
        return {'success': True, 'response': result['content']}
    return result
