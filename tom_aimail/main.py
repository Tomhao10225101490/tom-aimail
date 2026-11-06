"""Tom AImail command line.

Usage:
  python -m tom_aimail.main --setup          # friendly first-run wizard
  python -m tom_aimail.main --check-config   # load .env and print a masked summary
  python -m tom_aimail.main --once           # process the inbox once, then exit
  python -m tom_aimail.main                  # poll forever (POLL_SECONDS)
"""

from __future__ import annotations

import argparse
import getpass
import os
import time
from datetime import datetime
from pathlib import Path

from .ai_client import ask_ai
from .config import Config
from .mailbox import Mailbox
from .service import process_once
from .state import StateStore

ENV_TEMPLATE = """# Tom AImail configuration — written by the setup wizard. Keep it private.
MAIL_ADDRESS={mail_address}
MAIL_AUTH_CODE={mail_auth_code}
IMAP_HOST=imap.qq.com
SMTP_HOST=smtp.qq.com
DEEPSEEK_API_KEY={deepseek_api_key}
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
POLL_SECONDS=120
ALLOWED_SENDERS={allowed_senders}
MAX_DOC_CHARS=60000
STATE_FILE=.tom-aimail-state.json
"""


def run_setup(env_path: str) -> int:
    path = Path(env_path)
    print("Welcome to Tom AImail / 欢迎使用 Tom AImail")
    print("Three questions and you're done / 回答三个问题就好。\n")
    if path.exists():
        answer = input(f"{env_path} already exists. Overwrite it? / 已经存在，要覆盖吗？[y/N] ")
        if answer.strip().lower() != "y":
            print("Setup cancelled, nothing changed.")
            return 1

    mail_address = input("1. Service mailbox address / 服务邮箱地址 (e.g. you@qq.com): ").strip()
    print("   For QQ Mail, turn on IMAP/SMTP in Settings and use the authorization")
    print("   code it gives you — not your QQ password. / QQ 邮箱请用授权码，不是密码。")
    mail_auth_code = getpass.getpass("2. Mailbox authorization code / 邮箱授权码 (hidden): ").strip()
    deepseek_api_key = getpass.getpass("3. DeepSeek API key / DeepSeek API 密钥 (hidden): ").strip()
    allowed = input(
        "Optional: only serve these senders / 只给这些人用 (comma-separated, empty = everyone): "
    ).strip()

    path.write_text(
        ENV_TEMPLATE.format(
            mail_address=mail_address,
            mail_auth_code=mail_auth_code,
            deepseek_api_key=deepseek_api_key,
            allowed_senders=allowed,
        ),
        encoding="utf-8",
    )
    os.chmod(path, 0o600)
    print(f"\nSaved to {env_path} (readable only by you). Checking it now:\n")
    config = Config.from_env(env_path)
    print(config.masked_summary())
    print("\nAll set. Start the service with:  python -m tom_aimail.main")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="tom-aimail", description="Tom AImail")
    parser.add_argument("--setup", action="store_true", help="run the friendly first-run wizard")
    parser.add_argument("--once", action="store_true", help="process the inbox once and exit")
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="load configuration, print a masked summary, and exit",
    )
    parser.add_argument("--env", default=".env", help="path to the .env file")
    args = parser.parse_args()

    if args.setup:
        return run_setup(args.env)

    config = Config.from_env(args.env)
    if args.check_config:
        print(config.masked_summary())
        return 0

    mailbox = Mailbox(
        address=config.mail_address,
        auth_code=config.mail_auth_code,
        imap_host=config.imap_host,
        smtp_host=config.smtp_host,
    )
    state = StateStore(config.state_file)

    if args.once:
        sent = process_once(config, mailbox, ask_ai, state)
        print(f"done: {sent} email(s) answered")
        return 0

    print(f"Tom AImail watching {config.mail_address} every {config.poll_seconds}s")
    while True:
        try:
            sent = process_once(config, mailbox, ask_ai, state)
            if sent:
                print(f"[{datetime.now().isoformat(timespec='seconds')}] answered {sent}")
        except Exception as error:
            print(f"poll error: {error}")
        time.sleep(config.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
