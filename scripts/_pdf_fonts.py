"""Register Unicode-capable fonts for ReportLab PDF generators."""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle

RULE = HexColor("#cbd5e1")
LGREY = HexColor("#f4f6f9")
DARK = HexColor("#1e3a5f")


def _font_tuples() -> list[tuple[Path, Path, Path, Path]]:
    """Return (regular, bold, italic, bold_italic) candidate paths."""
    candidates: list[tuple[Path, Path, Path, Path]] = []

    script_fonts = Path(__file__).resolve().parent / "fonts"
    candidates.append(
        (
            script_fonts / "DejaVuSans.ttf",
            script_fonts / "DejaVuSans-Bold.ttf",
            script_fonts / "DejaVuSans-Oblique.ttf",
            script_fonts / "DejaVuSans-BoldOblique.ttf",
        )
    )

    try:
        import matplotlib

        mpl_fonts = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        candidates.append(
            (
                mpl_fonts / "DejaVuSans.ttf",
                mpl_fonts / "DejaVuSans-Bold.ttf",
                mpl_fonts / "DejaVuSans-Oblique.ttf",
                mpl_fonts / "DejaVuSans-BoldOblique.ttf",
            )
        )
    except Exception:
        pass

    win = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    candidates.extend(
        [
            (
                win / "DejaVuSans.ttf",
                win / "DejaVuSans-Bold.ttf",
                win / "DejaVuSans-Oblique.ttf",
                win / "DejaVuSans-BoldOblique.ttf",
            ),
            (
                win / "NotoSans-Regular.ttf",
                win / "NotoSans-Bold.ttf",
                win / "NotoSans-Italic.ttf",
                win / "NotoSans-BoldItalic.ttf",
            ),
            (
                win / "segoeui.ttf",
                win / "segoeuib.ttf",
                win / "segoeuii.ttf",
                win / "segoeuiz.ttf",
            ),
            (
                win / "arial.ttf",
                win / "arialbd.ttf",
                win / "ariali.ttf",
                win / "arialbi.ttf",
            ),
        ]
    )

    for base in (
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/TTF"),
        Path("/usr/local/share/fonts"),
    ):
        candidates.append(
            (
                base / "DejaVuSans.ttf",
                base / "DejaVuSans-Bold.ttf",
                base / "DejaVuSans-Oblique.ttf",
                base / "DejaVuSans-BoldOblique.ttf",
            )
        )
        candidates.append(
            (
                base / "NotoSans-Regular.ttf",
                base / "NotoSans-Bold.ttf",
                base / "NotoSans-Italic.ttf",
                base / "NotoSans-BoldItalic.ttf",
            )
        )

    return candidates


def register_pdf_fonts() -> str:
    """Register Main/MainBold/MainItalic/MainBI; return path to regular TTF."""
    for regular, bold, italic, bold_italic in _font_tuples():
        if regular.is_file() and bold.is_file():
            pdfmetrics.registerFont(TTFont("Main", str(regular)))
            pdfmetrics.registerFont(TTFont("MainBold", str(bold)))
            pdfmetrics.registerFont(
                TTFont("MainItalic", str(italic if italic.is_file() else regular))
            )
            pdfmetrics.registerFont(
                TTFont("MainBI", str(bold_italic if bold_italic.is_file() else bold))
            )
            return str(regular)

    raise FileNotFoundError(
        "No suitable TTF fonts found for PDF generation "
        "(install DejaVu Sans, Noto Sans, or matplotlib)"
    )


def pdf_math_text(s: str) -> str:
    """ASCII-safe substitutions for formula boxes only (not body Cyrillic)."""
    _phrase_subs = [
        ("\u03b7\u2080", "eta_0"),
        ("\u03b7\u1d62\u2c7c", "eta_ij"),
        ("log\u2081\u2080", "log10"),
        ("\u0394log\u2081\u2080\u03b7", "Delta log10 eta"),
        ("\u0394CFS", "Delta CFS"),
        ("M\u2098\u2090\u2093", "Mmax"),
        ("n\u209b\u1d62\u2098", "n_sim"),
        ("p\u2091\u209c\u2090\u209b", "p_ETAS"),
        ("t\u1d62\u2c7c", "t_ij"),
        ("r\u1d62\u2c7c", "r_ij"),
        ("\u03bc", "mu"),
        ("\u03b1", "alpha"),
        ("\u03b7", "eta"),
        ("\u0394", "Delta"),
        ("\u00d7", "x"),
        ("\u2212", "-"),
        ("\u2264", "<="),
        ("\u2265", ">="),
        ("\u00b1", "+/-"),
    ]
    for old, new in _phrase_subs:
        s = s.replace(old, new)
    return s


def default_table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LGREY]),
            ("BOX", (0, 0), (-1, -1), 0.5, RULE),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, RULE),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
    )


def build_pdf_table(
    rows: list[list[str]],
    col_fracs: list[float],
    total_width: float,
    styles: dict,
    *,
    wrap_col: int | None = None,
) -> Table:
    """Build a wrapped Paragraph table; wrap_col uses tbl_wrap style if present."""
    cw = [total_width * f for f in col_fracs]
    hdr_style = styles["tbl_hdr"]
    cell_style = styles["tbl_cell"]
    wrap_style = styles.get("tbl_wrap", cell_style)
    data: list[list[Paragraph]] = []
    for ri, row in enumerate(rows):
        row_cells: list[Paragraph] = []
        for ci, text in enumerate(row):
            if ri == 0:
                st = hdr_style
                content = f"<b>{text}</b>"
            else:
                st = wrap_style if wrap_col is not None and ci == wrap_col else cell_style
                content = text
            row_cells.append(Paragraph(content, st))
        data.append(row_cells)
    tbl = Table(data, colWidths=cw, repeatRows=1)
    tbl.setStyle(default_table_style())
    return tbl
