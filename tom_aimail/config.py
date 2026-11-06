"""Configuration for Tom AImail, loaded from a local .env file.

Secrets (mailbox authorization code, DeepSeek API key) live only in .env,
which is gitignored. Never commit real values.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """Minimal .env reader: KEY=VALUE lines, # comments, optional quotes."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass
class Config:
    mail_address: str
    mail_auth_code: str
    deepseek_api_key: str
    imap_host: str = "imap.qq.com"
    smtp_host: str = "smtp.qq.com"
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    poll_seconds: int = 120
    allowed_senders: frozenset[str] = field(default_factory=frozenset)
    max_doc_chars: int = 60000
    state_file: str = ".tom-aimail-state.json"

    @classmethod
    def from_env(cls, env_path: str | Path = ".env") -> "Config":
        _load_dotenv(Path(env_path))
        allowed = {
            addr.strip().lower()
            for addr in os.environ.get("ALLOWED_SENDERS", "").split(",")
            if addr.strip()
        }
        config = cls(
            mail_address=os.environ.get("MAIL_ADDRESS", ""),
            mail_auth_code=os.environ.get("MAIL_AUTH_CODE", ""),
            deepseek_api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
            imap_host=os.environ.get("IMAP_HOST", "imap.qq.com"),
            smtp_host=os.environ.get("SMTP_HOST", "smtp.qq.com"),
            deepseek_base_url=os.environ.get(
                "DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"
            ),
            deepseek_model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
            poll_seconds=int(os.environ.get("POLL_SECONDS", "120")),
            allowed_senders=frozenset(allowed),
            max_doc_chars=int(os.environ.get("MAX_DOC_CHARS", "60000")),
            state_file=os.environ.get("STATE_FILE", ".tom-aimail-state.json"),
        )
        config.validate()
        return config

    def validate(self) -> None:
        missing = [
            name
            for name, value in (
                ("MAIL_ADDRESS", self.mail_address),
                ("MAIL_AUTH_CODE", self.mail_auth_code),
                ("DEEPSEEK_API_KEY", self.deepseek_api_key),
            )
            if not value or value.startswith("replace-with-")
        ]
        if missing:
            raise ValueError(
                "Missing or placeholder configuration: "
                + ", ".join(missing)
                + ". Copy .env.example to .env and fill in your own values."
            )

    def masked_summary(self) -> str:
        def mask(value: str) -> str:
            return value[:2] + "***" if len(value) > 2 else "***"

        return "\n".join(
            [
                f"mail_address     = {self.mail_address}",
                f"mail_auth_code   = {mask(self.mail_auth_code)}",
                f"imap / smtp      = {self.imap_host} / {self.smtp_host}",
                f"deepseek_api_key = {mask(self.deepseek_api_key)}",
                f"deepseek_model   = {self.deepseek_model}",
                f"poll_seconds     = {self.poll_seconds}",
                "allowed_senders  = "
                + (", ".join(sorted(self.allowed_senders)) or "(everyone)"),
                f"max_doc_chars    = {self.max_doc_chars}",
                f"state_file       = {self.state_file}",
            ]
        )
