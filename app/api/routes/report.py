"""PDF Case Report generation API route."""

import io
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["report"])


class ReportRequest(BaseModel):
    """Request body for PDF report generation."""
    title: str = Field(default="Legal Consultation Report", max_length=200)
    language: str = Field(default="en", max_length=10)
    messages: list[dict] = Field(..., min_length=1)
    # Each message: {"role": "user"|"assistant", "content": "..."}


@router.post("/report/pdf")
async def generate_pdf_report(req: ReportRequest):
    """Generate a PDF case report from conversation history."""
    try:
        pdf_bytes = _build_pdf(req.title, req.messages, req.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"dharma_nyaya_report_{timestamp}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_pdf(title: str, messages: list[dict], language: str) -> bytes:
    """Build a PDF document from chat messages using minimal PDF generation."""
    buf = io.BytesIO()

    # ── Minimal PDF writer (no external dependencies) ──────────────────
    objects = []
    # We'll build raw PDF bytes

    def obj(content):
        objects.append(content)
        return len(objects)

    # Fonts
    font_ref = obj("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_bold_ref = obj("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    # Build pages content
    pages = []
    page_contents = _build_pages_content(title, messages, language)

    pages_ref_num = len(objects) + 1  # reserve

    for page_text in page_contents:
        stream = page_text.encode('latin-1', errors='replace')
        stream_obj = obj(
            f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream"
        )
        page_ref = obj(
            f"<< /Type /Page /Parent {pages_ref_num} 0 R "
            f"/MediaBox [0 0 595 842] "
            f"/Contents {stream_obj} 0 R "
            f"/Resources << /Font << /F1 {font_ref} 0 R /F2 {font_bold_ref} 0 R >> >> >>"
        )
        pages.append(page_ref)

    kids = " ".join(f"{p} 0 R" for p in pages)
    pages_obj = obj(
        f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>"
    )

    catalog = obj(f"<< /Type /Catalog /Pages {pages_obj} 0 R >>")

    # Write PDF
    buf.write(b"%PDF-1.4\n")
    offsets = []
    for i, o in enumerate(objects):
        offsets.append(buf.tell())
        num = i + 1
        if isinstance(o, bytes):
            buf.write(f"{num} 0 obj\n".encode())
            buf.write(o)
            buf.write(b"\nendobj\n")
        else:
            buf.write(f"{num} 0 obj\n{o}\nendobj\n".encode())

    xref_offset = buf.tell()
    buf.write(b"xref\n")
    buf.write(f"0 {len(objects) + 1}\n".encode())
    buf.write(b"0000000000 65535 f \n")
    for off in offsets:
        buf.write(f"{off:010d} 00000 n \n".encode())

    buf.write(b"trailer\n")
    buf.write(f"<< /Size {len(objects) + 1} /Root {catalog} 0 R >>\n".encode())
    buf.write(b"startxref\n")
    buf.write(f"{xref_offset}\n".encode())
    buf.write(b"%%EOF")

    return buf.getvalue()


def _build_pages_content(title: str, messages: list[dict], language: str) -> list[str]:
    """Build PDF page stream content. Returns list of page content streams."""
    pages = []
    y = 800
    lines = []

    def flush_page():
        nonlocal lines, y
        if lines:
            pages.append("\n".join(lines))
        lines = []
        y = 800

    def add_line(text, font="F1", size=11, indent=50):
        nonlocal y
        if y < 60:
            flush_page()
        safe = _safe_text(text)
        lines.append(f"BT /{font} {size} Tf {indent} {y} Td ({safe}) Tj ET")
        y -= size + 6

    def add_gap(gap=15):
        nonlocal y
        y -= gap

    # Title page header
    add_line(title, "F2", 18, 50)
    add_gap(5)
    add_line(f"Generated: {datetime.utcnow().strftime('%d %B %Y, %H:%M UTC')}", "F1", 9, 50)
    add_line(f"Platform: DHARMA-NYAYA AI Legal Empowerment", "F1", 9, 50)
    add_gap(5)

    # Horizontal line
    lines.append(f"0.8 0.8 0.8 RG 50 {y} m 545 {y} l 0.5 w S")
    y -= 20

    # Messages
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if y < 100:
            flush_page()

        label = "YOU:" if role == "user" else "DHARMA-NYAYA AI:"
        add_line(label, "F2", 11, 50)
        add_gap(2)

        # Wrap text to lines of ~85 chars
        for para in content.split("\n"):
            wrapped = _wrap_text(para, 85)
            for wl in wrapped:
                add_line(wl, "F1", 10, 60)

        add_gap(10)
        lines.append(f"0.9 0.9 0.9 RG 50 {y+5} m 545 {y+5} l 0.3 w S")
        y -= 10

    # Footer on last page
    if y > 40:
        y = 40
        add_line("This report is AI-generated for informational purposes. Consult a lawyer for legal advice.", "F1", 7, 50)

    flush_page()
    return pages


def _wrap_text(text: str, width: int) -> list[str]:
    """Word-wrap text to specified character width."""
    if not text.strip():
        return [""]
    words = text.split()
    wrapped = []
    line = ""
    for word in words:
        if len(line) + len(word) + 1 > width:
            wrapped.append(line)
            line = word
        else:
            line = f"{line} {word}" if line else word
    if line:
        wrapped.append(line)
    return wrapped or [""]


def _safe_text(text: str) -> str:
    """Escape special PDF characters and strip non-latin chars for Type1 font."""
    text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    # Replace non-ASCII with '?' for Type1 Helvetica compatibility
    return text.encode('latin-1', errors='replace').decode('latin-1')
