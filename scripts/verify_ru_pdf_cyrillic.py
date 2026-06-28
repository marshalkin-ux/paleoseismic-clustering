"""Verify Cyrillic text in article_ru.pdf after round-4 layout."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "paper" / "article_ru.pdf"

# page index (0-based) -> substrings that must appear (round-3 layout)
CHECKS: dict[int, list[str]] = {
    0: ["Временная ETAS-null", "in-sample temporal null"],
    2: ["событий", "полноты"],
    3: ["Jaccard", "Штраф", "Компонент"],
    4: ["Bonferroni", "пуассоновские", "Split"],
    5: ["Параметр", "Сводная", "чувствительности"],
    6: ["Ограничение", "Supplementary"],
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
        for block in h_blocks:
            for raw in re.findall(rb"\(([^)]*)\)", block):
                if any(b > 127 for b in raw):
                    sample = raw.decode("latin-1", errors="replace")[:60]
                    print(f"  WARN: Helvetica block non-ASCII: {sample!r}")
                    failed = True

    if failed:
        print("\nVERIFICATION FAILED")
        return 1
    print("\nVERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
