"""
TaskFlow AI Prompts Module.
Dynamically loads centralized instructions from ai_instructions.md and constructs
specialized prompts for chatbot, task suggestions, learning roadmaps, and technical assistance.
"""

from pathlib import Path

# Path to the centralized markdown instructions
INSTRUCTIONS_PATH = Path(__file__).resolve().parent / 'ai_instructions.md'

_cached_instructions = None
_cached_mtime = None


def load_core_instructions() -> str:
    """
    Dynamically load the centralized AI instructions from ai_instructions.md.
    Caches content based on file modification time for high performance while
    allowing dynamic updates without server restarts.
    """
    global _cached_instructions, _cached_mtime
    try:
        if INSTRUCTIONS_PATH.exists():
            current_mtime = INSTRUCTIONS_PATH.stat().st_mtime
            if _cached_instructions is None or current_mtime != _cached_mtime:
                _cached_instructions = INSTRUCTIONS_PATH.read_text(encoding='utf-8').strip()
                _cached_mtime = current_mtime
            return _cached_instructions
    except Exception as e:
        # Fallback in case of disk read error
        if _cached_instructions:
            return _cached_instructions

    return (
        "You are TaskFlow AI, a practical learning mentor and productivity assistant. "
        "Provide concise, actionable advice. Generate 3-level roadmaps for learning topics, "
        "practical step-by-step solutions for technical questions, and 1-2 sentence actionable "
        "descriptions for task suggestions. Avoid unnecessary theoretical explanations."
    )


def get_chatbot_system_prompt(user=None) -> str:
    """
    Construct the chatbot system prompt by combining core instructions from
    ai_instructions.md with optional dynamic user context.
    """
    instructions = load_core_instructions()

    user_context = ""
    if user and getattr(user, 'is_authenticated', False):
        try:
            from tasks.models import Task
            total_tasks = Task.objects.filter(user=user).count()
            pending_tasks = Task.objects.filter(user=user, completed=False).count()
            user_name = user.get_full_name() or user.username
            user_context = (
                f"\n\n### Current User Context\n"
                f"- Name: {user_name}\n"
                f"- Total Tasks in TaskFlow: {total_tasks}\n"
                f"- Pending Tasks: {pending_tasks}\n"
                f"Refer to their tasks generally if relevant, encouraging completion."
            )
        except Exception:
            pass

    return f"{instructions}{user_context}"


def get_task_suggestion_prompt(topic: str) -> list:
    """
    Build messages for generating a simple, meaningful, actionable task description
    from a user-provided topic or description draft.
    Output is strictly the task description text (15-30 words, 1-2 sentences).
    """
    system_prompt = (
        "You are TaskFlow AI, a practical learning mentor and productivity assistant.\n"
        "### Task Generation\n"
        "Your job is to generate exactly ONE simple, meaningful, actionable task description "
        "related to the user's input topic that can be directly saved to their task list.\n\n"
        "Requirements:\n"
        "- Generate a relevant and actionable task (15 to 30 words, 1-2 sentences).\n"
        "- Focus on practical implementation (e.g., 'Practice...', 'Build...', 'Create...', 'Write...').\n"
        "- Keep descriptions concise, practical, and clear.\n"
        "- Avoid lengthy theoretical explanations or conversational filler.\n"
        "- Do NOT include quotes, headings, bullet points, or markdown formatting.\n"
        "- Output ONLY the final task description text.\n\n"
        "Reference Examples:\n"
        "- Input: JavaScript -> Output: Practice JavaScript variables, data types, operators, and basic functions by writing simple programs.\n"
        "- Input: Python -> Output: Create a Python program using conditional statements and loops to solve three basic programming problems.\n"
        "- Input: Django -> Output: Build a basic Django application with URL routing, function-based views, and HTML templates.\n"
        "- Input: React -> Output: Build an interactive React counter component utilizing state, props, and event handlers.\n"
        "- Input: SQL -> Output: Write SQL queries using SELECT, WHERE, GROUP BY, and JOIN to analyze a sample relational database."
    )

    user_prompt = f"Topic: {topic.strip()}"

    return [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt},
    ]


def get_learning_roadmap_prompt(topic: str) -> list:
    """
    Build messages for generating a structured 3-level learning roadmap
    (Beginner, Intermediate, Advanced) for a technology or skill.
    """
    core_instructions = load_core_instructions()

    system_prompt = (
        f"{core_instructions}\n\n"
        "### Specific Mode Override: Learning Roadmap\n"
        "Generate a structured, practical 3-level learning roadmap (Beginner, Intermediate, Advanced) "
        "for the requested technology. Ensure topics are strictly in sequential learning order, "
        "and each level includes essential topics, practical exercises, mini-projects, and expected outcomes. "
        "Keep it concise, direct, and beginner-friendly without textbook monologues."
    )

    user_prompt = f"How can I learn {topic.strip()}? Give me a structured learning roadmap."

    return [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt},
    ]


def get_technical_assistance_prompt(query: str) -> list:
    """
    Build messages for answering a specific technical, coding, or architecture question.
    """
    core_instructions = load_core_instructions()

    system_prompt = (
        f"{core_instructions}\n\n"
        "### Specific Mode Override: Technical Assistance\n"
        "Provide a direct, step-by-step solution with clean code examples, exact implementation "
        "locations, and common mistakes to avoid. Avoid unnecessary theoretical discourse."
    )

    return [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': query.strip()},
    ]
