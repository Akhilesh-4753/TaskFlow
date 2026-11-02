"""
Groq AI service module.
All API communication is done server-side. Never expose the API key to the browser.
"""

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY_MESSAGES = 10


def is_groq_configured():
    """Check if Groq API is properly configured."""
    return bool(getattr(settings, 'GROQ_API_KEY', ''))


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

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                'Authorization': f'Bearer {settings.GROQ_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': settings.GROQ_MODEL,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f'Write a description for this task: {title.strip()}'},
                ],
                'max_tokens': 300,
                'temperature': 0.7,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        description = data['choices'][0]['message']['content'].strip()
        return {'success': True, 'description': description}

    except requests.exceptions.Timeout:
        logger.error('Groq API timeout for task description')
        return {'success': False, 'error': 'AI service timed out. Please try again.'}
    except requests.exceptions.RequestException as e:
        logger.error(f'Groq API request error: {e}')
        return {'success': False, 'error': 'AI service is currently unavailable.'}
    except (KeyError, IndexError) as e:
        logger.error(f'Groq API response parsing error: {e}')
        return {'success': False, 'error': 'Unexpected response from AI service.'}


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

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                'Authorization': f'Bearer {settings.GROQ_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': settings.GROQ_MODEL,
                'messages': messages,
                'max_tokens': 500,
                'temperature': 0.8,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        reply = data['choices'][0]['message']['content'].strip()
        return {'success': True, 'response': reply}

    except requests.exceptions.Timeout:
        logger.error('Groq API chat timeout')
        return {'success': False, 'error': 'AI service timed out. Please try again.'}
    except requests.exceptions.RequestException as e:
        logger.error(f'Groq API chat error: {e}')
        return {'success': False, 'error': 'AI service is currently unavailable.'}
    except (KeyError, IndexError) as e:
        logger.error(f'Groq API chat response parsing error: {e}')
        return {'success': False, 'error': 'Unexpected response from AI service.'}

