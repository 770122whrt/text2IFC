"""Pre-transport integrity of the source-turn catalog used by Brief citations."""
from collections.abc import Mapping


def require_brief_conversation(conversation):
    """Validate supplied identities without creating, guessing or renumbering them."""
    def invalid(reason):
        raise ValueError("DESIGN_BRIEF_CONVERSATION_INVALID: " + reason)

    if not isinstance(conversation, (list, tuple)) or not conversation:
        invalid("a non-empty transcript is required")
    seen = set()
    has_user = False
    for index, turn in enumerate(conversation):
        if not isinstance(turn, Mapping):
            invalid(f"turn {index} must be an object")
        identity = turn.get("turn_id")
        if not isinstance(identity, str) or not identity.strip():
            invalid(f"turn {index} needs an explicit non-empty turn_id")
        if identity in seen:
            invalid(f"turn {index} duplicates a turn_id")
        seen.add(identity)
        if turn.get("role") not in {"user", "assistant"}:
            invalid(f"turn {index} has an unsupported role")
        if not isinstance(turn.get("content"), str) or not turn["content"].strip():
            invalid(f"turn {index} needs non-empty text content")
        has_user |= turn["role"] == "user"
    if not has_user:
        invalid("at least one user turn is required")
