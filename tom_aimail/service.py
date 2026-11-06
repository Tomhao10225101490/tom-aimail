"""One Tom AImail pass: fetch -> greet -> ask the AI -> reply -> mark done.

The mailbox, the AI call and the sender state are injected, so tests run
fully offline with fakes.

The flow is built to feel human to the sender:
1. A "help" email gets friendly instructions, no AI involved.
2. Any other request gets an instant acknowledgement, so nobody stares at
   a silent inbox wondering whether it worked.
3. The result arrives as an email whose body is the answer, with a
   complete Word document attached. A first-time sender gets a welcome.
4. If the AI fails, the sender still hears from us — a warm apology
   asking them to send it once more — instead of silence.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Callable

from . import messages
from .ai_client import build_user_content
from .config import Config
from .document import build_docx
from .extract import extract_text
from .mailbox import Mailbox
from .state import StateStore

AskAi = Callable[[str, str, str, str], str]


def _reply_filename(subject: str) -> str:
    slug = re.sub(r"[^\w\- ]+", "", subject, flags=re.UNICODE).strip()
    slug = re.sub(r"\s+", "-", slug)[:40].strip("-")
    return f"TomAImail-{slug or 'result'}.docx"


def _reply_subject(incoming_subject: str) -> str:
    return f"Re: {incoming_subject}" if incoming_subject else "Tom AImail result"


def process_once(
    config: Config, mailbox: Mailbox, ask: AskAi, state: StateStore
) -> int:
    """Process every unseen email once. Returns how many emails were answered."""
    answered = 0
    for incoming in mailbox.fetch_unseen():
        if config.allowed_senders and incoming.sender not in config.allowed_senders:
            print(f"skip {incoming.uid}: sender not allowed: {incoming.sender}")
            mailbox.mark_seen(incoming.uid)
            continue

        lang = messages.pick_language(incoming.subject, incoming.body)
        subject = _reply_subject(incoming.subject)

        if messages.is_help_request(incoming.subject, incoming.body):
            mailbox.send_text(
                incoming.sender,
                subject,
                messages.help_text(lang, config.mail_address),
            )
            mailbox.mark_seen(incoming.uid)
            answered += 1
            print(f"sent instructions to {incoming.sender}")
            continue

        # Acknowledge first, think second — nobody waits in silence.
        try:
            mailbox.send_text(incoming.sender, subject, messages.ack_text(lang, incoming.subject))
        except Exception as error:
            print(f"ack failed for {incoming.uid}: {error}")

        try:
            documents: list[tuple[str, str]] = []
            unreadable: list[str] = []
            for name, data in incoming.attachments:
                text = extract_text(name, data)
                if text.strip():
                    documents.append((name, text))
                else:
                    unreadable.append(name)
            user_content = build_user_content(
                instructions=incoming.body,
                documents=documents,
                unreadable=unreadable,
                max_doc_chars=config.max_doc_chars,
            )
            result = ask(
                config.deepseek_api_key,
                config.deepseek_base_url,
                config.deepseek_model,
                user_content,
            )
        except Exception as error:
            print(f"error processing {incoming.uid} from {incoming.sender}: {error}")
            try:
                mailbox.send_text(incoming.sender, subject, messages.error_text(lang))
            except Exception as send_error:
                print(f"error reply failed for {incoming.uid}: {send_error}")
            mailbox.mark_seen(incoming.uid)
            continue

        first_time = state.is_new_sender(incoming.sender)
        body = result
        if first_time:
            body = messages.welcome_line(lang) + "\n" + body
        body += "\n\n— Tom AImail\n" + messages.tip_line(lang)

        docx_bytes = build_docx(
            title=subject,
            request_text=incoming.body,
            result_text=result,
            sender=incoming.sender,
            attachments=tuple(name for name, _ in incoming.attachments),
            when=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        mailbox.send_reply(
            to=incoming.sender,
            subject=subject,
            body=body,
            attachment_name=_reply_filename(incoming.subject),
            attachment_bytes=docx_bytes,
        )
        state.remember_sender(incoming.sender)
        mailbox.mark_seen(incoming.uid)
        answered += 1
        print(f"replied to {incoming.sender} about '{incoming.subject}'")
    return answered
