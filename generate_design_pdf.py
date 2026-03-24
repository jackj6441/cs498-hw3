from pathlib import Path
import math
import re


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT_MARGIN = 50
TOP_MARGIN = 740
FONT_SIZE = 10
LINE_HEIGHT = 14
MAX_CHARS = 88


def normalize_markdown_to_lines(markdown: str) -> list[str]:
    lines: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("#"):
            line = re.sub(r"^#+\s*", "", line).upper()
        if line.startswith("- "):
            line = "* " + line[2:]
        if re.match(r"^\d+\.\s", line):
            pass
        if line == "":
            lines.append("")
            continue

        while len(line) > MAX_CHARS:
            split_at = line.rfind(" ", 0, MAX_CHARS)
            if split_at == -1:
                split_at = MAX_CHARS
            lines.append(line[:split_at])
            line = line[split_at:].lstrip()
        lines.append(line)
    return lines


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_stream(lines: list[str], start_index: int) -> tuple[str, int]:
    max_lines_per_page = math.floor((TOP_MARGIN - 60) / LINE_HEIGHT)
    page_lines = lines[start_index : start_index + max_lines_per_page]
    y = TOP_MARGIN
    commands = ["BT", f"/F1 {FONT_SIZE} Tf"]

    for line in page_lines:
        commands.append(f"1 0 0 1 {LEFT_MARGIN} {y} Tm")
        commands.append(f"({escape_pdf_text(line)}) Tj")
        y -= LINE_HEIGHT

    commands.append("ET")
    return "\n".join(commands) + "\n", start_index + len(page_lines)


def add_object(objects: list[bytes], content: bytes) -> int:
    objects.append(content)
    return len(objects)


def main() -> None:
    markdown = Path("Design.md").read_text(encoding="utf-8")
    lines = normalize_markdown_to_lines(markdown)

    objects: list[bytes] = []
    font_id = add_object(objects, b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    page_ids: list[int] = []
    content_ids: list[int] = []
    next_index = 0

    while next_index < len(lines):
        stream, next_index = build_stream(lines, next_index)
        stream_bytes = stream.encode("ascii", errors="replace")
        content_id = add_object(
            objects,
            f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
            + stream_bytes
            + b"endstream",
        )
        content_ids.append(content_id)
        page_id = add_object(objects, b"")
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    pages_id = add_object(
        objects,
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii"),
    )

    for page_id, content_id in zip(page_ids, content_ids):
        objects[page_id - 1] = (
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("ascii")

    catalog_id = add_object(objects, f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii"))

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{i} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
            "ascii"
        )
    )

    Path("Design.pdf").write_bytes(pdf)


if __name__ == "__main__":
    main()
