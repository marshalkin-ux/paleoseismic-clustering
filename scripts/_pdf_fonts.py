"""Register Unicode-capable fonts for ReportLab PDF generators."""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def register_pdf_fonts() -> str:
    """Register Main/MainBold/MainItalic; return family name used."""
    candidates = []
    try:
        import matplotlib

        mpl_fonts = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        candidates.extend(
            [
                (mpl_fonts / "DejaVuSans.ttf", mpl_fonts / "DejaVuSans-Bold.ttf"),
                (mpl_fonts / "DejaVuSansCondensed.ttf", mpl_fonts / "DejaVuSansCondensed-Bold.ttf"),
            ]
        )
    except Exception:
        pass

    win = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    candidates.extend(
        [
            (win / "DejaVuSans.ttf", win / "DejaVuSans-Bold.ttf"),
            (win / "arial.ttf", win / "arialbd.ttf"),
        ]
    )

    for regular, bold in candidates:
        if regular.is_file() and bold.is_file():
            pdfmetrics.registerFont(TTFont("Main", str(regular)))
            pdfmetrics.registerFont(TTFont("MainBold", str(bold)))
            italic = regular.parent / regular.name.replace(".ttf", "Oblique.ttf")
            if not italic.is_file():
                italic = regular.parent / "ariali.ttf"
            pdfmetrics.registerFont(TTFont("MainItalic", str(italic if italic.is_file() else regular)))
            pdfmetrics.registerFont(TTFont("MainBI", str(bold)))
            return "Main"

    raise FileNotFoundError("No suitable TTF fonts found for PDF generation")
