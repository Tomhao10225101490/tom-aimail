import io

from docx import Document

from tom_aimail.document import build_docx


def test_build_docx_contains_request_and_result():
    data = build_docx(
        "My title",
        "please summarise this",
        "## Answer\n- point one",
        sender="friend@example.com",
        attachments=("notes.txt",),
        when="2026-11-06 00:30",
    )
    assert data[:2] == b"PK"  # docx is a zip
    document = Document(io.BytesIO(data))
    text = "\n".join(p.text for p in document.paragraphs)
    assert "please summarise this" in text
    assert "friend@example.com" in text
    assert "notes.txt" in text
    assert "Tom AImail" in text
    headings = [p.text for p in document.paragraphs if p.style.name.startswith("Heading")]
    assert "My title" in headings
    assert "Answer" in headings
