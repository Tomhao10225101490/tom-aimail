# Tom AImail

**Email in, finished document out.** Tom AImail is a small AI service that lives
inside an ordinary mailbox. Friends and family send an email with a document
and their questions; the AI does the work and replies with the answer plus a
complete, polished Word document attached.

No app to install, no account to register, no chat window to learn — just
email, the one tool everybody already knows.

> 给亲戚朋友用的高级 AI 服务：把要处理的文档和问题发到邮箱，AI 做好之后，
> 把完整的文档加回答直接回信发给你。

## For the people who write to it: you only need the address

If someone runs a Tom AImail for you, **the only thing you need is the email
address.** Nothing to install, nothing to set up, no password of yours is
ever involved.

1. Write an email to the Tom AImail address.
2. Attach the document you want help with (Word, PDF or text) and write your
   questions in the email — or skip the attachment and just ask in the email.
3. You'll get a short "收到啦 / Got it!" reply right away so you know it
   worked, and a few minutes later the real answer, with a complete Word
   document attached.

New here? Send an email with the subject **help** (or **帮助**) and Tom
AImail will write back with friendly instructions in your own language.

Things people use it for:

- "Here is my child's homework document — please answer every question."
- "Translate this PDF into Chinese, keep the formatting sensible."
- "My notes are messy; turn them into a proper letter I can send."
- "Summarise this long document in five sentences my mother can understand."

## How it works

```
friend emails document + questions ──► QQ mailbox (IMAP)
                                            │  Tom AImail polls
                                            ▼
                     instant warm acknowledgement: "Got it, working on it"
                                            │
                              extract text (Word / PDF / text)
                                            │
                                            ▼
                                 DeepSeek AI does the work
                                            │
                                            ▼
              reply email: answer in the body + finished .docx attached
```

Human touches, on purpose: acknowledgements so nobody waits in silence, a
welcome line for first-time senders, help-by-email, answers in the sender's
own language (Chinese or English), and — if something goes wrong — a warm
apology asking them to send it once more, never silence.

## For the person running it: three answers and you're live

```bash
git clone https://github.com/Tomhao10225101490/tom-aimail.git
cd tom-aimail
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m tom_aimail.main --setup    # friendly wizard, asks 3 things
python -m tom_aimail.main            # start serving
```

The wizard asks only for: the service mailbox address, its QQ Mail
**authorization code** (QQ Mail → Settings → Account → IMAP/SMTP service;
it is *not* your QQ password), and a DeepSeek API key. Everything else has
sensible defaults. It writes `.env` for you (permission 600, gitignored —
secrets never enter this repo).

Useful commands:

```bash
python -m tom_aimail.main --check-config   # is my .env sane? (secrets masked)
python -m tom_aimail.main --once           # process the inbox once, then exit
python -m tom_aimail.main                  # poll forever
```

## Configuration (`.env`, written by the wizard or by hand)

| Key | What it is |
| --- | --- |
| `MAIL_ADDRESS` | The mailbox that receives requests, e.g. `you@qq.com` |
| `MAIL_AUTH_CODE` | The mailbox **authorization code** (see above) |
| `DEEPSEEK_API_KEY` | Your DeepSeek API key |
| `DEEPSEEK_BASE_URL` | Default `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | Default `deepseek-chat` |
| `POLL_SECONDS` | How often to check for new mail (default `120`) |
| `ALLOWED_SENDERS` | Optional comma-separated allowlist. Empty = serve everyone (fine for a family mailbox, risky for a public one). |
| `MAX_DOC_CHARS` | Max extracted characters sent to the AI (default `60000`) |
| `STATE_FILE` | Remembers who has written before, for the welcome line |

## What senders can attach

`.docx`, `.pdf`, `.txt`, `.md`, `.csv`. Photos of documents can't be read
yet — the help email says so kindly, and suggests typing the text or putting
it in a Word file.

## Project layout

```
tom_aimail/
  config.py    # .env loading and validation
  mailbox.py   # IMAP fetch + SMTP replies (QQ Mail defaults)
  extract.py   # attachment -> plain text
  ai_client.py # DeepSeek (OpenAI-compatible) chat call + prompt assembly
  document.py  # build the reply .docx
  messages.py  # every human-facing text: ack, help, error, welcome (中文/EN)
  state.py     # remembers senders, for the first-time welcome
  service.py   # one pass: greet -> think -> reply -> mark done
  main.py      # CLI: --setup wizard, --once, --check-config, polling loop
tests/         # offline tests with fakes (no real mail, no real API)
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## License

MIT — see `LICENSE`.
