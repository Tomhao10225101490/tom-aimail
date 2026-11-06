"""DeepSeek (OpenAI-compatible) chat client for Tom AImail."""

from __future__ import annotations

import requests

SYSTEM_PROMPT = (
    "You are Tom AImail, an AI assistant who works over email for the "
    "sender's family and friends. The user emails you a document together "
    "with questions or a task. Do the work completely and write the result "
    "as a finished piece of writing that could be forwarded as-is: answer "
    "every question, and if the task asks for a document, produce the full "
    "document, not an outline or a summary of what it would contain. "
    "Reply in the same language as the user's message. Be clear, warm and "
    "concrete. If the document text was truncated, say so briefly at the "
    "end."
)


def build_user_content(
    instructions: str,
    documents: list[tuple[str, str]],
    unreadable: list[str],
    max_doc_chars: int,
) -> str:
    """Assemble the user message: instructions + document texts (capped)."""
    parts = ["The sender wrote:", instructions.strip() or "(no written message)"]
    remaining = max_doc_chars
    truncated = False
    for name, text in documents:
        if remaining <= 0:
            truncated = True
            break
        excerpt = text[:remaining]
        if len(excerpt) < len(text):
            truncated = True
        remaining -= len(excerpt)
        parts.append(f"\n--- Document: {name} ---\n{excerpt}")
    if unreadable:
        parts.append(
            "\n(Attached but unreadable file types: "
            + ", ".join(unreadable)
            + ". Mention them politely in your reply.)"
        )
    if truncated:
        parts.append("\n(Note: the document text was truncated for length.)")
    return "\n".join(parts)


def ask_ai(
    api_key: str,
    base_url: str,
    model: str,
    user_content: str,
    timeout: int = 300,
) -> str:
    response = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
