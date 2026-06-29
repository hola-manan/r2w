"""Attachment extraction: docx/xlsx -> text, plus the /extract endpoint contract."""
from __future__ import annotations

import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.db.base import Base
from app.db.session import get_engine, init_db
from app.llm.extract import extract
from tests.fake_llm import FakeLLM


def _make_docx(text: str) -> bytes:
    """Build a minimal valid .docx package containing a single paragraph."""
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)
    return buf.getvalue()


def _make_xlsx(rows: list[list[str]]) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_extract_docx():
    text = extract("brief.docx", _make_docx("Users must export CSV in under 5s"))
    assert "Users must export CSV in under 5s" in text


def test_extract_xlsx():
    text = extract("data.xlsx", _make_xlsx([["Feature", "Priority"], ["Export", "High"]]))
    assert "# Sheet1" in text
    assert "Feature\tPriority" in text
    assert "Export\tHigh" in text


def test_extract_rejects_unsupported():
    with pytest.raises(ValueError):
        extract("notes.pdf", b"%PDF-1.4")


@pytest.fixture
def client():
    init_db()
    Base.metadata.drop_all(bind=get_engine())
    Base.metadata.create_all(bind=get_engine())
    deps.LLM_FACTORY = lambda: FakeLLM()
    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c
    deps.LLM_FACTORY = __import__("app.llm", fromlist=["get_llm"]).get_llm


def test_extract_endpoint_docx(client):
    files = {
        "file": (
            "brief.docx",
            _make_docx("Hello from docx"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    res = client.post("/projects/p1/extract", files=files)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["filename"] == "brief.docx"
    assert "Hello from docx" in body["text"]


def test_extract_endpoint_rejects_txt(client):
    files = {"file": ("notes.txt", b"plain text", "text/plain")}
    res = client.post("/projects/p1/extract", files=files)
    assert res.status_code == 400
