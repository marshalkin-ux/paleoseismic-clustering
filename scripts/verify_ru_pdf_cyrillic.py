"""Verify Cyrillic text in article_ru.pdf on pages 5, 7, 8."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "paper" / "article_ru.pdf"

# page index (0-based) -> substrings that must appear
CHECKS: dict[int, list[str]] = {
    4: ["Компонент", "Штраф", "Физический смысл", "временно"],
    6: ["Пространственно", "распределение", "циркум-тихоокеанского", "Камчатка"],
    7: ["Только воспроизводимость", "Компонент", "замкнутая форма", "афтершоках"],
}


def _page_stream(page) -> bytes:
    content = page.get_contents()
    if content is None:
        return b""
    if isinstance(content, list):
        return b"".join(c.get_data() for c in content)
    return content.get_data()


def _helvetica_blocks(data: bytes) -> list[bytes]:
    return [b for b in re.findall(rb"BT(.*?)ET", data, re.DOTALL) if re.search(rb"/F1[\s\n<]", b)]


def main() -> int:
    if not PDF.is_file():
        print(f"Missing PDF: {PDF}", file=sys.stderr)
        return 1

    reader = pypdf.PdfReader(str(PDF))
    failed = False

    for page_idx, needles in CHECKS.items():
        page_no = page_idx + 1
        text = reader.pages[page_idx].extract_text() or ""
        print(f"=== Page {page_no} ===")
        for needle in needles:
            ok = needle in text
            print(f"  {'OK' if ok else 'FAIL'}: {needle!r}")
            if not ok:
                failed = True

        h_blocks = _helvetica_blocks(_page_stream(reader.pages[page_idx]))
        # Footer uses F1/Helvetica; flag if any Helvetica block has high bytes (non-ASCII).
        for block in h_blocks:
            for raw in re.findall(rb"\(([^)]*)\)", block):
                if any(b > 127 for b in raw):
                    sample = raw.decode("latin-1", errors="replace")[:60]
                    print(f"  WARN: Helvetica block non-ASCII: {sample!r}")
                    failed = True

    # Page 4 (index 3): formula box with «событий»
    p4 = reader.pages[3].extract_text() or ""
    ok4 = "событий" in p4
    print("=== Page 4 (formula b-value) ===")
    print(f"  {'OK' if ok4 else 'FAIL'}: 'событий'")
    if not ok4:
        failed = True

    if failed:
        print("\nVERIFICATION FAILED")
        return 1
    print("\nVERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
