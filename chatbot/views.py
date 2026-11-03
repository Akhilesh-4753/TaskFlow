"""
Chatbot Views.
Integrates with the centralized ai.services module to handle AI chat requests.
"""

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from ai.services import generate_chat_response


@login_required
@require_POST
@csrf_protect
def chat_view(request):
    """
    Handle AI chat requests from users.
    Delegates to the centralized ai.services.generate_chat_response.
    """
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

