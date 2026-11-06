"""Mailbox access for Tom AImail: IMAP fetch + SMTP reply.

Defaults target QQ Mail (imap.qq.com / smtp.qq.com, SSL). The password for
both is the QQ Mail authorization code, not the account password.
"""

from __future__ import annotations

import imaplib
import smtplib
from dataclasses import dataclass, field
from email import policy
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import parseaddr


@dataclass
class IncomingEmail:
    uid: str
    sender: str
    subject: str
    body: str
    attachments: list[tuple[str, bytes]] = field(default_factory=list)


def _decode(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


class Mailbox:
    def __init__(self, address: str, auth_code: str, imap_host: str, smtp_host: str):
        self.address = address
        self.auth_code = auth_code
        self.imap_host = imap_host
        self.smtp_host = smtp_host

    # -- receiving -----------------------------------------------------

    def fetch_unseen(self) -> list[IncomingEmail]:
        messages: list[IncomingEmail] = []
        with imaplib.IMAP4_SSL(self.imap_host) as imap:
            imap.login(self.address, self.auth_code)
            imap.select("INBOX")
            status, data = imap.uid("search", None, "UNSEEN")
            if status != "OK":
                return messages
            for raw_uid in data[0].split():
                uid = raw_uid.decode()
                status, fetched = imap.uid("fetch", uid, "(RFC822)")
                if status != "OK" or not fetched or not isinstance(fetched[0], tuple):
                    continue
                messages.append(self._parse(uid, fetched[0][1]))
        return messages

    def _parse(self, uid: str, raw: bytes) -> IncomingEmail:
        message = BytesParser(policy=policy.default).parsebytes(raw)
        sender = parseaddr(str(message.get("From", "")))[1].lower()
        subject = _decode(str(message.get("Subject", "")))
        body_parts: list[str] = []
        attachments: list[tuple[str, bytes]] = []
        if message.is_multipart():
            for part in message.walk():
                disposition = part.get_content_disposition()
                filename = part.get_filename()
                if disposition == "attachment" and filename is not None:
                    payload = part.get_payload(decode=True) or b""
                    attachments.append((_decode(filename), payload))
                elif part.get_content_type() == "text/plain" and disposition != "attachment":
                    payload = part.get_payload(decode=True) or b""
                    charset = part.get_content_charset() or "utf-8"
                    body_parts.append(payload.decode(charset, errors="replace"))
        else:
            payload = message.get_payload(decode=True) or b""
            charset = message.get_content_charset() or "utf-8"
            body_parts.append(payload.decode(charset, errors="replace"))
        return IncomingEmail(
            uid=uid,
            sender=sender,
            subject=subject,
            body="\n".join(body_parts).strip(),
            attachments=attachments,
        )

    def mark_seen(self, uid: str) -> None:
        with imaplib.IMAP4_SSL(self.imap_host) as imap:
            imap.login(self.address, self.auth_code)
            imap.select("INBOX")
            imap.uid("store", uid, "+FLAGS", "(\\Seen)")

    # -- sending --------------------------------------------------------

    def _send(self, message: EmailMessage) -> None:
        with smtplib.SMTP_SSL(self.smtp_host, 465) as smtp:
            smtp.login(self.address, self.auth_code)
            smtp.send_message(message)

    def send_text(self, to: str, subject: str, body: str) -> None:
        """A plain warm email with no attachment (hello, help, apologies)."""
        message = EmailMessage()
        message["From"] = self.address
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        self._send(message)

    def send_reply(
        self,
        to: str,
        subject: str,
        body: str,
        attachment_name: str,
        attachment_bytes: bytes,
    ) -> None:
        message = EmailMessage()
        message["From"] = self.address
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        message.add_attachment(
            attachment_bytes,
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=attachment_name,
        )
        self._send(message)
