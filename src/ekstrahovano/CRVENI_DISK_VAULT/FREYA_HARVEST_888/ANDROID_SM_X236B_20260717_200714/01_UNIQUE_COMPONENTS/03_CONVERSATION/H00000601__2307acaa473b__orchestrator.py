"""
FREYA ORCHESTRATOR v1.0
"""

def route(question: str):

    q = question.lower()

    if any(x in q for x in [
        "who are you",
        "what do you know",
        "remember",
        "about me",
        "yesterday"
    ]):
        return "memory"

    elif any(x in q for x in [
        "book",
        "pdf",
        "document",
        "chapter",
        "library"
    ]):
        return "library"

    elif any(x in q for x in [
        "learn",
        "study",
        "lesson",
        "explain"
    ]):
        return "learning"

    elif any(x in q for x in [
        "internet",
        "research",
        "search"
    ]):
        return "research"

    elif any(x in q for x in [
        "script",
        "python",
        "bash",
        "adapter"
    ]):
        return "scripts"

    elif any(x in q for x in [
        "tablet",
        "device",
        "folder",
        "file",
        "documents"
    ]):
        return "device"

    return "conversation"
