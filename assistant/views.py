import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from .services import get_chat_response, get_task_description_suggestion


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

    # Validate history is a list of valid dicts
    if not isinstance(conversation_history, list):
        conversation_history = []

    result = get_chat_response(
        user_message=user_message,
        conversation_history=conversation_history,
        user=request.user,
    )

    if result['success']:
        return JsonResponse({'success': True, 'response': result['response']})
    else:
        return JsonResponse({'success': False, 'error': result['error']}, status=503)


@login_required
@require_POST
@csrf_protect
def suggest_description_view(request):
    """Generate AI task description suggestion."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON request.'}, status=400)

    title = data.get('title', '').strip()

    if not title:
        return JsonResponse({'success': False, 'error': 'Task title is required.'}, status=400)

    result = get_task_description_suggestion(title=title, user=request.user)

    if result['success']:
        return JsonResponse({'success': True, 'description': result['description']})
    else:
        return JsonResponse({'success': False, 'error': result['error']}, status=503)

