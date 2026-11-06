"""The human-facing words of Tom AImail.

Every message a relative or friend receives is warm, short and plain —
in their own language. If their email contains Chinese, we answer in
Chinese; otherwise in English.
"""

from __future__ import annotations

HELP_WORDS = {"help", "帮助", "使用说明", "说明", "怎么用", "如何使用"}


def is_chinese(text: str) -> bool:
    return any("一" <= char <= "鿿" for char in text)


def pick_language(*texts: str) -> str:
    return "zh" if any(is_chinese(text) for text in texts) else "en"


def is_help_request(subject: str, body: str) -> bool:
    candidates = {subject.strip().lower(), body.strip().split("\n")[0].strip().lower()}
    return bool(candidates & HELP_WORDS)


def ack_text(lang: str, subject: str) -> str:
    if lang == "zh":
        return (
            "收到啦！我是 Tom AImail，正在认真看你发的文档和问题。\n"
            "做好之后，我会把完整的文档和回答发回给你，一般几分钟就好，请稍等～"
        )
    return (
        "Got it! I'm Tom AImail, and I'm working on your document and "
        "questions right now.\n"
        "When it's ready I'll email the finished document and the answers "
        "back to you — it usually takes just a few minutes."
    )


def help_text(lang: str, mailbox_address: str) -> str:
    if lang == "zh":
        return (
            "你好！我是 Tom AImail，一个住在邮箱里的 AI 小助手。\n\n"
            "用法特别简单，只有三步：\n"
            f"1. 给这个邮箱发一封邮件：{mailbox_address}\n"
            "2. 把要处理的文档作为附件（支持 Word、PDF、TXT），"
            "并在正文里写清楚你的问题或要求；没有文档也可以，直接在正文里提问就行。\n"
            "3. 等几分钟，我会回信：正文里是回答，附件里是一份完整的 Word 文档。\n\n"
            "比如你可以这样用我：\n"
            "· 把孩子的作业题拍照……不行，照片我看不了——请把题目打成文字或放进 Word 文档；\n"
            "· 把一份 PDF 发我，让我翻译成中文，或者总结成几句话；\n"
            "· 把零散的想法写在正文里，让我帮你写成一封信、一份发言稿、一个通知。\n\n"
            "不用注册、不用装任何软件，会发邮件就会用我。"
        )
    return (
        "Hello! I'm Tom AImail, a little AI helper who lives in this mailbox.\n\n"
        "Using me takes three steps:\n"
        f"1. Send an email to this address: {mailbox_address}\n"
        "2. Attach the document you want help with (Word, PDF or text files), "
        "and write your questions or wishes in the email. No document? Just "
        "ask your question in the email itself.\n"
        "3. Wait a few minutes. I'll reply with the answers in the email and a "
        "complete Word document attached.\n\n"
        "For example, you can ask me to:\n"
        "- translate a PDF, or summarise it in a few sentences;\n"
        "- answer the questions in a Word document;\n"
        "- turn your rough notes into a letter, a speech or a notice.\n\n"
        "No sign-up, no app to install — if you can send an email, you can use me."
    )


def error_text(lang: str) -> str:
    if lang == "zh":
        return (
            "不好意思，我处理你这封邮件时出了点小问题，这次没能完成。\n"
            "请过一会儿把邮件再发一次，我马上处理。给你添麻烦了！"
        )
    return (
        "Sorry — something went wrong while I was working on your email, and "
        "I couldn't finish this time.\n"
        "Please send it once more in a little while, and I'll take care of it "
        "right away."
    )


def welcome_line(lang: str) -> str:
    if lang == "zh":
        return "欢迎你第一次使用 Tom AImail！你的文档和回答都在下面，完整的 Word 文档在附件里。\n"
    return (
        "Welcome — this is your first Tom AImail request! Your answers are "
        "below, and the complete Word document is attached.\n"
    )


def tip_line(lang: str) -> str:
    if lang == "zh":
        return "小提示：下次直接把文档和问题发到这个邮箱就行，不用做任何设置。"
    return "Tip: next time, just email your document and questions to this address — nothing to set up."
