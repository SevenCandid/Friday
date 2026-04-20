import random

ASSISTANT_NAME = "SEVEN"
CREATOR_NAME = "Frank Bediako"
CREATOR_ALIAS = "SEVEN"
CREATOR_LOCATION = "Ghana"
CREATOR_BIO = "A talented Ghanaian developer who designed me to be the ultimate tactical AI assistant."

_responses = {
    "wake": [
        "Yes? How can I help you?",
        "I'm listening.",
        "Go ahead.",
        "I'm here.",
        "Ready.",
        "What's up?"
    ],
    "success": [
        "Done.",
        "Alright.",
        "Opening it now.",
        "Got it.",
        "On it.",
        "All set."
    ],
    "error": [
        "I didn't catch that. Could you repeat it?",
        "Sorry, I missed that.",
        "Say that again?",
        "I'm not sure I understand.",
        "Could you say that differently?",
        "Sorry?"
    ],
    "not_supported": [
        "That's not something I can do yet."
    ]
}

def get_response(category):
    """
    Returns a random response from the specified category.
    """
    responses = _responses.get(category, ["Hm?"])
    return random.choice(responses)
