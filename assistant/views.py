"""
Assistant Views.
Delegates AI operations to the centralized ai.services module.
"""

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from ai.services import generate_chat_response, generate_task_suggestion


@login_required
@require_POST
@csrf_protect
def chat_view(request):
    """Handle AI chat messages. Authentication and CSRF required."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON request.'}, status=400)

    user_message = data.get('message', '').strip()
    conversation_history = data.get('history', [])

    if not user_message:
        return JsonResponse({'success': False, 'error': 'Message cannot be empty.'}, status=400)

    if not isinstance(conversation_history, list):
        conversation_history = []

    result = generate_chat_response(
        user_message=user_message,
        conversation_history=conversation_history,
        user=request.user,
    )

    if result.get('success'):
        return JsonResponse({'success': True, 'response': result['response']})
    else:
        return JsonResponse({'success': False, 'error': result.get('error', 'AI service error.')}, status=503)


@login_required
@require_POST
@csrf_protect
def suggest_description_view(request):
    """
    Generate an actionable AI task suggestion from a topic entered in the
    Description or Title field.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON request.'}, status=400)

    # Support topic from description field, topic field, or title field
    topic = data.get('topic') or data.get('description') or data.get('title', '')
    cleaned_topic = str(topic).strip()

    if not cleaned_topic:
        return JsonResponse({'success': False, 'error': 'Please enter a topic or title.'}, status=400)

    result = generate_task_suggestion(topic=cleaned_topic, user=request.user)

    if result.get('success'):
        return JsonResponse({
            'success': True,
            'description': result['description'],
            'title': result.get('title', ''),
        })
    else:
        return JsonResponse({'success': False, 'error': result.get('error', 'Failed to generate task suggestion.')}, status=503)
