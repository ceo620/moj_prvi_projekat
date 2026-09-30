import json
from pathlib import Path

PROFILE = Path.home() / "FREYA_CORE" / "memory" / "profile.json"

def answer(question):

    with open(PROFILE,"r",encoding="utf-8") as f:
        data=json.load(f)

    q=question.lower()

    if "who am i" in q or "about me" in q:
        return "\n".join(data["about"])

    if "project" in q:
        return "Current projects:\n- " + "\n- ".join(data["projects"])

    if "mission" in q:
        return data["mission"]

    return None
