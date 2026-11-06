import io

from docx import Document

from tom_aimail.extract import extract_text


def _docx_bytes() -> bytes:
    document = Document()
    document.add_paragraph("Hello from a Word file.")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "left"
    table.rows[0].cells[1].text = "right"
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_extract_txt():
    assert extract_text("note.txt", "你好，世界".encode("utf-8")) == "你好，世界"


def test_extract_docx_paragraphs_and_tables():
    text = extract_text("homework.docx", _docx_bytes())
    assert "Hello from a Word file." in text
    assert "left | right" in text


def test_extract_unsupported_returns_empty():
    assert extract_text("photo.png", b"\x89PNG") == ""
