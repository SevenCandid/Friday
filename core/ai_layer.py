"""
ai_layer.py — Friday's Lightweight AI Post-Processor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Uses Ollama (phi3) ONLY as a post-processing tool.

STRICT RULES:
  ✅ Summarize provided text
  ✅ Explain provided text in plain language
  ✅ Rewrite text to sound more natural
  ❌ Never fetch facts
  ❌ Never search the web
  ❌ Never invent or guess information
"""

import requests
from . import config

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

OLLAMA_URL   = config.get("ai", "ollama_url")
MODEL        = config.get("ai", "model")
TIMEOUT      = 20  # seconds — keeps Friday responsive

# Injected into every prompt to prevent hallucination
_SAFETY_HEADER = (
    "You are a helpful assistant. "
    "Your ONLY job is to process the TEXT according to the TASK. "
    "Do not add any new facts or guess. "
    "Just fulfill the TASK using only the information in the TEXT.\n\n"
)

# ─────────────────────────────────────────────
# CORE REQUEST
# ─────────────────────────────────────────────

def _query(prompt: str) -> str | None:
    """
    Sends a prompt to the local Ollama instance.
    Returns the response text, or None if Ollama is unavailable.
    """
    try:
        payload = {
            "model":  MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": config.get("ai", "temperature"),
                "num_predict": 150,   # Short responses only
            }
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        print("[AI Layer] Ollama is offline. Skipping AI post-processing.")
        return None
    except Exception as e:
        print(f"[AI Layer Error] {e}")
        return None


def is_available() -> bool:
    """Quick check to see if Ollama is running before attempting a query."""
    try:
        r = requests.get("http://localhost:11434", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────

def summarize(text: str) -> str:
    """
    Returns a short, clear summary of the provided text.
    Falls back to the original text if Ollama is unavailable.

    Use case: Wikipedia paragraphs, long news descriptions.
    """
    if not text or not text.strip():
        return text

    prompt = (
        f"{_SAFETY_HEADER}"
        f"TEXT:\n{text}\n\n"
        f"TASK: Write a 1–2 sentence summary of the text above. "
        f"Be concise and factual. Do not add anything not in the text."
    )

    result = _query(prompt)
    return result if result else text


def explain(text: str) -> str:
    """
    Returns a plain-language explanation of the provided text.
    Falls back to the original text if Ollama is unavailable.

    Use case: Technical Wikipedia articles, complex news topics.
    """
    if not text or not text.strip():
        return text

    prompt = (
        f"{_SAFETY_HEADER}"
        f"TEXT:\n{text}\n\n"
        f"TASK: Explain the text above in simple, clear language "
        f"that anyone can understand. Use 2–3 short sentences. "
        f"Only use information from the text."
    )

    result = _query(prompt)
    return result if result else text


def rewrite(text: str) -> str:
    """
    Rewrites the text to sound more natural and conversational.
    Falls back to the original text if Ollama is unavailable.

    Use case: Raw RSS news descriptions that sound robotic.
    """
    if not text or not text.strip():
        return text

    prompt = (
        f"{_SAFETY_HEADER}"
        f"TEXT:\n{text}\n\n"
        f"TASK: Rewrite the text above so it sounds natural and conversational, "
        f"as if a knowledgeable person is speaking. "
        f"Keep it to 1–2 sentences. "
        f"Do not change any facts. Do not add anything new."
    )

    result = _query(prompt)
    return result if result else text


def extract_fact(command: str) -> str:
    """
    Extracts the core fact from a user's command to save to memory.
    Example: "Remember that my favorite color is blue" -> "User's favorite color is blue"
    """
    if not command or not command.strip():
        return ""
        
    prompt = (
        f"{_SAFETY_HEADER}"
        f"TEXT:\n{command}\n\n"
        f"TASK: Extract the core fact from the text above that the user wants you to remember. "
        f"Rephrase it as a direct factual statement about the user (e.g. 'User likes dogs', 'User's wife is Sarah'). "
        f"Do not include conversational filler like 'Got it' or 'I will remember'. Just output the fact."
    )
    
    result = _query(prompt)
    return result if result else ""


def answer_from_memory(question: str, facts: list) -> str:
    """
    Uses the provided list of facts to answer the user's question.
    """
    if not facts:
        return "I don't have any facts stored in my memory yet."
        
    facts_str = "\n".join([f"- {f}" for f in facts])
    
    prompt = (
        f"You are a helpful assistant with a memory database.\n"
        f"Your ONLY job is to answer the QUESTION using the provided FACTS.\n"
        f"Do not guess or add new facts.\n\n"
        f"FACTS:\n{facts_str}\n\n"
        f"QUESTION:\n{question}\n\n"
        f"TASK: Answer the question using ONLY the FACTS provided above. "
        f"If the answer is not contained in the FACTS, reply exactly with: 'I don't know that yet based on my memory.' "
        f"Keep the answer short, natural, and conversational."
    )
    
    result = _query(prompt)
    return result if result else "I'm having trouble accessing my memory right now."


def process_with_context(command: str, active_window: str) -> str:
    """
    Processes a general command while taking the currently focused window into account.
    """
    if not command:
        return "I'm here. How can I help you?"
        
    prompt = (
        f"You are Friday, an AI assistant. "
        f"The user is currently using the application: '{active_window}'. "
        f"COMMAND: {command}\n\n"
        f"TASK: Respond to the user's command. Use the current application context ONLY if it is relevant to the request. "
        f"If the user says 'this' or 'here', they are likely referring to the current application. "
        f"Keep the response short, conversational, and helpful."
    )
    result = _query(prompt)
    return result if result else "I'm here, but I couldn't process that request right now."
