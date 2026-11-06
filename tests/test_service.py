from tom_aimail.ai_client import build_user_content
from tom_aimail.config import Config
from tom_aimail.mailbox import IncomingEmail
from tom_aimail.service import process_once
from tom_aimail.state import StateStore


class FakeMailbox:
    def __init__(self, emails):
        self._emails = emails
        self.seen = []
        self.replies = []
        self.texts = []

    def fetch_unseen(self):
        return list(self._emails)

    def mark_seen(self, uid):
        self.seen.append(uid)

    def send_text(self, to, subject, body):
        self.texts.append({"to": to, "subject": subject, "body": body})

    def send_reply(self, to, subject, body, attachment_name, attachment_bytes):
        self.replies.append(
            {
                "to": to,
                "subject": subject,
                "body": body,
                "attachment_name": attachment_name,
                "attachment_bytes": attachment_bytes,
            }
        )


def _config(**overrides):
    values = dict(
        mail_address="tom@qq.com",
        mail_auth_code="authcode",
        deepseek_api_key="sk-test",
    )
    values.update(overrides)
    return Config(**values)


def _email(**overrides):
    values = dict(
        uid="1",
        sender="friend@example.com",
        subject="help with homework",
        body="please answer the questions in the file",
        attachments=[("questions.txt", b"What is 2 + 2?")],
    )
    values.update(overrides)
    return IncomingEmail(**values)


def _fake_ai(api_key, base_url, model, user_content):
    assert "What is 2 + 2?" in user_content
    return "The answer is 4."


def _state(tmp_path):
    return StateStore(tmp_path / "state.json")


def test_process_once_acks_then_replies_with_docx(tmp_path):
    mailbox = FakeMailbox([_email()])
    answered = process_once(_config(), mailbox, _fake_ai, _state(tmp_path))
    assert answered == 1
    assert mailbox.seen == ["1"]
    # First a warm acknowledgement with no attachment...
    assert len(mailbox.texts) == 1
    assert "Got it" in mailbox.texts[0]["body"]
    # ...then the real reply with the document.
    reply = mailbox.replies[0]
    assert reply["to"] == "friend@example.com"
    assert reply["subject"] == "Re: help with homework"
    assert "The answer is 4." in reply["body"]
    assert reply["attachment_bytes"][:2] == b"PK"
    assert reply["attachment_name"].endswith(".docx")


def test_first_time_sender_gets_a_welcome_second_time_does_not(tmp_path):
    state = _state(tmp_path)
    first = FakeMailbox([_email()])
    process_once(_config(), first, _fake_ai, state)
    assert "Welcome" in first.replies[0]["body"]

    second = FakeMailbox([_email(uid="2")])
    process_once(_config(), second, _fake_ai, state)
    assert "Welcome" not in second.replies[0]["body"]


def test_chinese_sender_gets_chinese_messages(tmp_path):
    mailbox = FakeMailbox([_email(subject="帮我看看", body="请回答文件里的问题")])
    process_once(_config(), mailbox, _fake_ai, _state(tmp_path))
    assert "收到啦" in mailbox.texts[0]["body"]
    assert "欢迎" in mailbox.replies[0]["body"]


def test_help_email_gets_instructions_without_ai(tmp_path):
    def no_ai(*args):
        raise AssertionError("AI must not be called for help emails")

    mailbox = FakeMailbox([_email(subject="help", body="", attachments=[])])
    answered = process_once(_config(), mailbox, no_ai, _state(tmp_path))
    assert answered == 1
    assert mailbox.replies == []
    assert len(mailbox.texts) == 1
    assert "three steps" in mailbox.texts[0]["body"]
    assert mailbox.seen == ["1"]


def test_allowlist_skips_strangers_but_marks_seen(tmp_path):
    mailbox = FakeMailbox([_email(sender="stranger@example.com")])
    config = _config(allowed_senders=frozenset({"friend@example.com"}))
    answered = process_once(config, mailbox, _fake_ai, _state(tmp_path))
    assert answered == 0
    assert mailbox.replies == []
    assert mailbox.texts == []
    assert mailbox.seen == ["1"]


def test_ai_failure_sends_a_warm_apology_not_silence(tmp_path):
    def broken_ai(*args):
        raise RuntimeError("api down")

    mailbox = FakeMailbox([_email()])
    answered = process_once(_config(), mailbox, broken_ai, _state(tmp_path))
    assert answered == 0
    assert mailbox.replies == []
    # ack + apology: the sender hears from us twice, never silence
    assert len(mailbox.texts) == 2
    assert "Sorry" in mailbox.texts[1]["body"]
    assert mailbox.seen == ["1"]


def test_user_content_truncates_long_documents():
    content = build_user_content(
        instructions="do it",
        documents=[("big.txt", "x" * 5000)],
        unreadable=["photo.png"],
        max_doc_chars=100,
    )
    assert "truncated" in content
    assert "photo.png" in content
    assert "x" * 100 in content
    assert "x" * 101 not in content
