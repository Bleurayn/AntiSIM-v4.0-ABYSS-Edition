def is_jailbreak(text: str) -> bool:
    banned = ["ignore previous", "you are now", "DAN mode"]
    return any(phrase in text.lower() for phrase in banned)
