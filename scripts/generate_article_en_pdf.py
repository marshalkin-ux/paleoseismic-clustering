"""
generate_article_en_pdf.py
Generates article_en.pdf — English scientific article (IMRAD / GRL-style).
Uses reportlab; no external LaTeX required.
"""

import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph as _BaseParagraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable

_FONT_DIR = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont("Main", os.path.join(_FONT_DIR, "arial.ttf")))
pdfmetrics.registerFont(TTFont("MainBold", os.path.join(_FONT_DIR, "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("MainItalic", os.path.join(_FONT_DIR, "ariali.ttf")))
pdfmetrics.registerFont(TTFont("MainBI", os.path.join(_FONT_DIR, "arialbi.ttf")))

DARK = HexColor("#1e3a5f")
ACCENT = HexColor("#2563eb")
TEXT = HexColor("#111111")
LGREY = HexColor("#f4f6f9")
MGREY = HexColor("#9ca3af")
RULE = HexColor("#cbd5e1")
PAGE_W, PAGE_H = A4
LM = RM = 2.5 * cm
TM = BM = 2.5 * cm


def safe_text(s: str) -> str:
    import unicodedata

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
        ("\u00a7", "Sec."),
        ("\u2212", "-"),
        ("\u2264", "<="),
        ("\u2265", ">="),
        ("\u00b1", "+/-"),
        ("\u202f", " "),
        ("\u0301", ""),
    ]
    for old, new in _phrase_subs:
        s = s.replace(old, new)
    _sub_map = str.maketrans({
        "\u2080": "0", "\u2081": "1", "\u2082": "2", "\u2083": "3",
        "\u2084": "4", "\u2085": "5", "\u2086": "6", "\u2087": "7",
        "\u2088": "8", "\u2089": "9",
        "\u1d62": "i", "\u2c7c": "j",
    })
    s = s.translate(_sub_map)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s


class Paragraph(_BaseParagraph):
    def __init__(self, text, style, *args, **kwargs):
        if isinstance(text, str):
            text = safe_text(text)
        super().__init__(text, style, *args, **kwargs)


class FormulaBox(Flowable):
    def __init__(self, text, width=None, height=2.0 * cm):
        super().__init__()
        self.text = text
        self.box_w = width or (PAGE_W - LM - RM)
        self.height = height

    def draw(self):
        c = self.canv
        c.setFillColor(LGREY)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1.2)
        c.roundRect(0, 0, self.box_w, self.height, 5, fill=1, stroke=1)
        c.setFillColor(DARK)
        c.setFont("MainBold", 13)
        c.drawCentredString(self.box_w / 2, self.height / 2 - 5, safe_text(self.text))


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(LM, BM - 0.5 * cm, PAGE_W - RM, BM - 0.5 * cm)
    canvas.setFont("Main", 8)
    canvas.setFillColor(MGREY)
    canvas.drawCentredString(
        PAGE_W / 2, BM - 0.9 * cm,
        f"Global Seismic Series  \u00b7  Yaroslav Marshalkin  \u00b7  {doc.page}"
    )
    canvas.restoreState()


def make_styles():
    s = {}
    s["doi"] = ParagraphStyle("doi", fontName="MainBold", fontSize=9,
                               textColor=DARK, spaceAfter=2)
    s["title"] = ParagraphStyle("title", fontName="MainBold", fontSize=15,
                                 textColor=DARK, alignment=TA_CENTER,
                                 spaceAfter=6, leading=20)
    s["copyright"] = ParagraphStyle("copyright", fontName="MainItalic", fontSize=9,
                                     textColor=MGREY, alignment=TA_CENTER, spaceAfter=8)
    s["meta"] = ParagraphStyle("meta", fontName="Main", fontSize=9,
                                textColor=TEXT, spaceAfter=3, leading=13)
    s["abstract_label"] = ParagraphStyle("abstract_label", fontName="MainBold",
                                          fontSize=10, textColor=DARK, spaceAfter=2)
    s["abstract"] = ParagraphStyle("abstract", fontName="MainItalic", fontSize=9,
                                    textColor=TEXT, alignment=TA_JUSTIFY,
                                    spaceAfter=6, leading=13, leftIndent=10, rightIndent=10)
    s["keywords"] = ParagraphStyle("keywords", fontName="Main", fontSize=9,
                                    textColor=TEXT, spaceAfter=4, leading=13)
    s["section"] = ParagraphStyle("section", fontName="MainBold", fontSize=13,
                                   textColor=DARK, alignment=TA_CENTER,
                                   spaceBefore=14, spaceAfter=6)
    s["subsection"] = ParagraphStyle("subsection", fontName="MainBold", fontSize=11,
                                      textColor=DARK, spaceBefore=8, spaceAfter=4)
    s["subsubsection"] = ParagraphStyle("subsubsection", fontName="MainBI",
                                         fontSize=10, textColor=DARK,
                                         spaceBefore=5, spaceAfter=3)
    s["body"] = ParagraphStyle("body", fontName="Main", fontSize=10,
                                textColor=TEXT, alignment=TA_JUSTIFY,
                                spaceAfter=5, leading=15, firstLineIndent=12)
    s["body_ni"] = ParagraphStyle("body_ni", fontName="Main", fontSize=10,
                                   textColor=TEXT, alignment=TA_JUSTIFY,
                                   spaceAfter=5, leading=15)
    s["enum"] = ParagraphStyle("enum", fontName="Main", fontSize=10,
                                textColor=TEXT, leftIndent=22, spaceAfter=4, leading=14)
    s["ref"] = ParagraphStyle("ref", fontName="Main", fontSize=9,
                               textColor=TEXT, leftIndent=18, firstLineIndent=-18,
                               spaceAfter=3, leading=13)
    s["caption"] = ParagraphStyle("caption", fontName="MainItalic", fontSize=9,
                                   textColor=MGREY, alignment=TA_CENTER, spaceAfter=4)
    s["tbl_hdr"] = ParagraphStyle("tbl_hdr", fontName="MainBold", fontSize=9,
                                   textColor=white, alignment=TA_CENTER)
    s["tbl_cell"] = ParagraphStyle("tbl_cell", fontName="Main", fontSize=9, textColor=TEXT)
    return s


def HR():
    return HRFlowable(width="100%", thickness=0.5, color=RULE, spaceAfter=4, spaceBefore=4)


def SEC(text, s):
    return [HR(), Paragraph(text, s["section"])]


def SSEC(text, s):
    return [Paragraph(text, s["subsection"])]


def SSSEC(text, s):
    return [Paragraph(text, s["subsubsection"])]


def build(s):
    story = []
    w = PAGE_W - LM - RM

    story.append(Paragraph(
        "Global Seismic Series: Statistical Analysis of Spatiotemporal "
        "Clustering in M\u22656.5 Earthquake Catalogs (1973\u20132026 CE)",
        s["title"]
    ))
    story.append(Paragraph("\u00a9 2026  Yaroslav Marshalkin", s["copyright"]))
    story.append(HR())
    story.append(Paragraph(
        "<b>Yaroslav Marshalkin</b><br/>"
        "Corresponding author: marshalkin@gmail.com<br/>"
        "Telegram: @MRSHLKN &nbsp;|&nbsp; "
        "GitHub: github.com/marshalkin-ux/paleoseismic-clustering",
        s["meta"]
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("<b>Abstract.</b>", s["abstract_label"]))
    story.append(Paragraph(
        "We analyse a merged catalog of <b>4,267 unique M\u22656.5 events</b> "
        "(from 4,418 CSV rows; ~151 NOAA M&lt;6.5 excluded from clustering; 2150\u00a0BCE\u20132026\u00a0CE) "
        "using the Baiesi\u2013Paczuski metric eta with tectonic-path distance (Bird\u00a02003). "
        "47 global seismic series are identified (27 modern, 15 early, 5 historical candidates). "
        "Significance: permutation test (n=10,000, p\u22640.0001, z=-6.17); ETAS validation "
        "(n=1000 catalogs, FPR=1000/1000, mean 15.4 \u00b1 1.7; max 24; "
        "p_ETAS=0/1000 for N_obs=27); FDR (45/47 at q=0.05, N=47). "
        "<b>statistical anomaly</b>, not proof of causal triggering. "
        "Largest series: 1905\u20131910 (193 events, 43 regions); "
        "most extensive modern: S170 (46 events, 12 regions, Mmax=9.1).",
        s["abstract"]
    ))
    story.append(Paragraph(
        "<b>Keywords:</b> global seismicity; seismic series; earthquake clustering; "
        "tectonic distance; Baiesi\u2013Paczuski metric; ETAS validation; false discovery "
        "rate; Monte Carlo; paleoseismology; remote triggering",
        s["keywords"]
    ))
    story.append(PageBreak())

    story += SEC("1. INTRODUCTION", s)
    story.append(Paragraph(
        "Large earthquakes do not occur as independent Poisson events. Following the "
        "1992 Landers earthquake (M<sub>w</sub> 7.3), Hill et al. [1993] documented "
        "remotely triggered seismicity at distances exceeding 1,000 km. Brodsky &amp; "
        "Prejean [2006] showed that surface waves can initiate swarms in volcanic "
        "systems thousands of kilometres away. The 2004 Sumatra\u2013Andaman earthquake "
        "(M<sub>w</sub> 9.1) was followed by elevated activity in distant regions "
        "[Pollitz et al., 1998; Freed &amp; Lin, 2001].",
        s["body"]
    ))
    story.append(Paragraph(
        "However, the systematic nature of such correlations remains debated. Michael "
        "[2011] found that M\u22657 clustering in 1995\u20132011 is statistically "
        "indistinguishable from random fluctuations. Shearer &amp; Stark [2012] "
        "reported no increase in global M\u22657 and M\u22658 rates after the 2004 "
        "Sumatra event. Kagan &amp; Jackson [1999] confirmed elevated probability of "
        "paired events at short separation without resolving long-range links.",
        s["body"]
    ))
    story.append(Paragraph(
        "The ETAS model [Ogata, 1988] reproduces regional aftershock clustering but "
        "does not encode inter-plate correlations. The Baiesi\u2013Paczuski [2004] "
        "metric and Zaliapin\u2013Ben-Zion extensions [2008, 2013] provide objective "
        "cluster detection but typically use Euclidean distance, ignoring lithospheric "
        "connectivity.",
        s["body"]
    ))
    story.append(Paragraph(
        "<b>Objective.</b> We test the hypothesis that multi-regional seismic series "
        "exist in a four-millennium catalog of M&gt;=6.5 earthquakes, using an adapted "
        "eta metric with tectonic distance along Bird (2003) plate boundaries. "
        "<b>Scope.</b> We combine nearest-neighbor clustering with tectonic-path distance, "
        "ETAS validation, and FDR correction; this complements global rate tests "
        "(Michael 2011; Shearer &amp; Stark 2012) with a different \u03b7-linkage statistic "
        "but does not supersede their conclusions.",
        s["body"]
    ))

    story += SEC("2. DATA AND METHODS", s)
    story += SSEC("2.1 Catalog compilation", s)
    story.append(Paragraph(
        "Three catalogs were merged: <b>USGS ComCat</b> (1900\u20132026, primary "
        "instrumental); <b>ISC Bulletin</b> (relocated hypocenters); and <b>NOAA NGDC</b> "
        "(historical and paleoseismic records from ~2150 BCE). Duplicates were merged "
        "using \u00b130 days and \u226450 km tolerance; source priority: ISC &gt; USGS &gt; NOAA. "
        "After deduplication, the catalog contains "
        "<b>4,267</b> unique M&gt;=6.5 events (from <b>4,418</b> CSV rows; ~151 M&lt;6.5 "
        "excluded from clustering). "
        "USGS ComCat: <b>2,088</b> raw (1973\u20132026) \u2192 <b>2,041</b> after merge/ISC. "
        "GK: 24 aftershocks (2,017/2,041); ZBZ: 1 dependent (2,040/2,041). "
        "quality_score is metadata, not an inclusion filter. "
        "<b>Final catalog:</b> 4,267 M\u22656.5 events (4,418 CSV rows).",
        s["body"]
    ))
    story += SSSEC("2.1.1 Catalog completeness", s)
    story.append(Paragraph(
        "Maximum-curvature analysis yields M<sub>c</sub> = 6.55. Maximum-likelihood "
        "b-value from 1,688 events above M<sub>c</sub>:",
        s["body"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(FormulaBox("b = 0.911 \u00b1 0.018  (n = 1,688 events)", w))
    story.append(Spacer(1, 0.15 * cm))

    story += SSEC("2.2 Tectonic distance and connectivity metric", s)
    story.append(Paragraph(
        "Tectonic distance r<sub>ij</sub> is the shortest path between hypocenters "
        "along the Bird (2003) plate-boundary graph (20 key segments). Paths are "
        "computed with Dijkstra's algorithm (NetworkX). If either hypocenter lies "
        "&gt;500 km from the nearest boundary node, or no graph path exists, "
        "r<sub>ij</sub> = 1.5 \u00d7 r<sub>GC</sub> (great-circle Haversine). "
        "<b>Fallback audit</b> (analyze_tectonic_fallback.py, fig07): "
        "4987 pairs from 500 events; 98.0% GC fallback, 2.0% Dijkstra "
        "(4015 snap&gt;500 km, 872 no path, 100 Dijkstra; 95 materially different; "
        "examples FE31 Japan, FE35 Philippines). Metric adds value for ~2% "
        "boundary-proximal pairs only. "
        "Tectonic diagnostic: median \u0394log\u2081\u2080\u03b7 = +0.28.",
        s["body"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(FormulaBox(
        "eta_ij  =  t_ij  *  r_ij^1.6  *  10^(-b*mi)",
        w
    ))
    story.append(Paragraph(
        "b=1.0 per Baiesi &amp; Paczuski (2004) for \u03b7 comparability; "
        "catalog b=0.911\u00b10.018 in Monte Carlo null only.",
        s["caption"]
    ))

    story += SSEC("2.3 Analysis pipeline", s)
    story.append(Paragraph(
        "Raw catalogs \u2192 dedup \u2192 exclude M&lt;6.5 (~151 NOAA) \u2192 "
        "GK declustering (primary) \u2192 eta NN forest "
        "\u2192 sliding windows \u2192 merge overlapping \u2192 series criteria \u2192 MC/ETAS/FDR. "
        "GK: 24 aftershocks (2,017/2,041); ZBZ: 1 dependent (2,040/2,041) \u2014 "
        "separate sensitivity check, not sequential filter.",
        s["body"]
    ))

    story += SSEC("2.4 Threshold \u03b7\u2080, series detection, and ETAS parameters", s)
    story.append(Paragraph(
        "Automatic \u03b7<sub>0</sub> from nearest-neighbor \u03b7 distribution: KDE valley "
        "between bimodal log<sub>10</sub>(\u03b7) modes (Zaliapin &amp; Ben-Zion 2013); "
        "default \u03b7<sub>0</sub> = 10<sup>median log10 \u03b7</sup>. Validated against "
        "Poisson permutation null (n = 10,000).",
        s["body"]
    ))
    for num, text in [
        ("1.", "Declustering via Gardner\u2013Knopoff [1974]."),
        ("2.", "Nearest-neighbor forest: parent i* = argmin \u03b7<sub>ij</sub> subject to \u03b7<sub>ij</sub> &lt; \u03b7<sub>0</sub>."),
        ("3.", "Global series: N \u2265 4; M \u2265 6.5; \u2265 3 Flinn\u2013Engdahl regions."),
        ("4.", "Sliding windows (1, 2, 5 yr); overlapping groups merged."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>&nbsp;&nbsp;{text}", s["enum"]))
    story.append(Paragraph(
        "<b>ETAS parameters (not catalog-calibrated):</b> Helmstetter &amp; Sornette 2003 "
        "defaults (mu=0.008, K=0.08, alpha=1.0, c=0.005 d, p=1.1); not refit on 2041 events "
        "(results/etas_calibration_note.md). Optional MLE mu ~0.105 events/day vs default 0.008.",
        s["body"]
    ))
    story += SSEC("2.5 Statistical validation", s)
    story.append(Paragraph(
        "<b>Permutation test:</b> n = 10,000, p \u2264 0.0001, z = -6.17 (modern). "
        "<b>ETAS validation:</b> 1000 catalogs (seed=42); FPR=1000/1000; mean 15.4; max 24; p_ETAS \u2264 0.001. "
        "Previously FPR=0/100 was an API bug (min_regions TypeError). "
        "<b>FDR (q=0.05):</b> 45/47 significant; N=47 series hypotheses. "
        "<b>Declustering:</b> GK 2,017/2,041; ZBZ 2,040/2,041.",
        s["body"]
    ))

    story += SEC("3. RESULTS", s)
    story += SSEC("3.1 Identified series", s)
    story.append(Paragraph(
        "Full historical analysis yields <b>47 global seismic series</b>: 27 modern "
        "(p \u2264 0.0001), 15 early instrumental (p = 0.007; pre-1960 incompleteness "
        "caveat), 5 historical candidates (<b>not significant</b>, p = 0.46; "
        "47 M\u22656.5 events pre-1900). 142 cluster candidates before filtering.",
        s["body"]
    ))

    tbl_cols = [w * f for f in [0.09, 0.07, 0.11, 0.09, 0.20, 0.44]]
    tbl_data = [
        [Paragraph("<b>ID</b>", s["tbl_hdr"]), Paragraph("<b>N</b>", s["tbl_hdr"]),
         Paragraph("<b>Regions</b>", s["tbl_hdr"]), Paragraph("<b>M<sub>max</sub></b>", s["tbl_hdr"]),
         Paragraph("<b>Period</b>", s["tbl_hdr"]), Paragraph("<b>Notes</b>", s["tbl_hdr"])],
        ["1905\u20131910", "193", "43", "8.8", "1905\u20131910", "Largest series; early instrumental"],
        ["S047", "53", "5", "8.0", "1982\u20132024", "Western Pacific subduction corridor"],
        ["S170", "46", "12", "9.1", "2002\u20132023", "Sunda belt; Sumatra 2004 (M 9.1)"],
        ["S095", "25", "4", "7.9", "1989\u20132017", "Western Pacific arc"],
        ["S116", "22", "5", "8.2", "1993\u20132021", "South Pacific multi-arc series"],
    ]
    tbl_data_fmt = [tbl_data[0]] + [
        [Paragraph(c, s["tbl_cell"]) for c in row] for row in tbl_data[1:]
    ]
    tbl = Table(tbl_data_fmt, colWidths=tbl_cols)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LGREY]),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tbl)
    story.append(Paragraph(
        "Table 1. Top five multi-regional series (\u2265 3 Flinn\u2013Engdahl regions).",
        s["caption"]
    ))
    story.append(Spacer(1, 0.2 * cm))

    story += SSEC("3.2 Spatial\u2013temporal distribution", s)
    story.append(Paragraph(
        "Elevated series activity occurs in 1952\u20131965 and 2002\u20132016 "
        "(post-Sumatra period). Spatially, clusters concentrate along the circum-Pacific "
        "belt (Kamchatka, Kuril Islands, Japan, Tonga, Indonesia). Tectonic diagnostic: "
        "median \u0394log\u2081\u2080\u03b7 = +0.28 on random pairs (mostly 1.5\u00d7 GC fallback).",
        s["body"]
    ))

    story += SEC("4. DISCUSSION AND CONCLUSIONS", s)
    story.append(Paragraph(
        "<b>Statistical anomaly (established):</b> series incompatible with Poisson "
        "and local-only ETAS nulls; FDR 45/47. Conclusion about \u03b7 links and "
        "p-values, not causality. <b>Working hypotheses</b> (not claims): viscoelastic "
        "mantle coupling (Pollitz 1998), dynamic triggering (Hill 1993; Brodsky 2006), "
        "shared tectonic loading (Freed &amp; Lin 2001). "
        "<b>Future work / supplement:</b> preliminary Coulomb/dynamic stress tests for S170 "
        "did not reach triggering thresholds (repository). "
        "<b>ETAS note:</b> FPR=1000/1000 at seed=42 (mean 15.4 spurious series); N_obs=27 exceeds ETAS max (24). "
        "<b>Tectonic audit:</b> 98% GC fallback of 4987 pairs (fig07).",
        s["body"]
    ))
    for num, text in [
        ("1.", "4,267 M\u22656.5 events (4,418 CSV records) contain 47 global series; "
               "27 modern significant at p \u2264 0.0001."),
        ("2.", "ETAS validation (1000 catalogs; FPR=1000/1000, p_ETAS \u2264 0.001) and "
               "FDR (45/47, N=47) confirm non-randomness."),
        ("3.", "Largest series: 1905\u20131910 (193 events, 43 regions, M<sub>max</sub>=8.8); "
               "most spatially extensive modern: S170 (46 events, 12 regions, "
               "2002\u20132023, M<sub>max</sub>=9.1)."),
        ("4.", "Tectonic path: 2.0% Dijkstra / 98.0% GC fallback (4987 pairs); "
               "median \u0394log\u2081\u2080\u03b7 = +0.28."),
        ("5.", "<b>Interpretive fork:</b> (a) if \u03b7 links are real \u2014 hazard "
               "implications without claiming direct triggering; (b) if artifacts \u2014 "
               "FDR+ETAS remains reproducible null-test."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>&nbsp;&nbsp;{text}", s["enum"]))
        story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "<b>Future work / supplement:</b> Static \u0394CFS and dynamic stress for "
        "S170, S047, S095; full ETAS MLE and multi-seed robustness.",
        s["body_ni"]
    ))

    story += SEC("DATA AND CODE AVAILABILITY", s)
    story.append(Paragraph(
        "Data and code: github.com/marshalkin-ux/paleoseismic-clustering "
        "(docs/data_availability.md). External DOI deposition (Zenodo) deferred \u2014 GitHub only.",
        s["body_ni"]
    ))

    story += SEC("REFERENCES", s)
    refs = [
        "Baiesi M., Paczuski M. (2004). Scale-free networks of earthquakes and aftershocks. Phys. Rev. E, 69, 066106.",
        "Zaliapin I. et al. (2008). Clustering analysis of seismicity and aftershock identification. Phys. Rev. Lett., 101, 018501.",
        "Zaliapin I., Ben-Zion Y. (2013). Earthquake clusters in southern California I. J. Geophys. Res., 118, 2847\u20132864.",
        "Bird P. (2003). An updated digital model of plate boundaries. Geochem. Geophys. Geosyst., 4(3), 1027.",
        "Hill D.P. et al. (1993). Seismicity remotely triggered by the magnitude 7.3 Landers earthquake. Science, 260, 1617\u20131623.",
        "Brodsky E.E., Prejean S.G. (2006). New constraints on mechanisms of remotely triggered seismicity. J. Geophys. Res., 111, B06312.",
        "Pollitz F.F. et al. (1998). Viscosity of oceanic asthenosphere inferred from remote triggering. Science, 280, 1245\u20131249.",
        "King G.C.P. et al. (1994). Static stress changes and the triggering of earthquakes. BSSA, 84, 935\u2013953.",
        "Stein R.S. (1999). The role of stress transfer in earthquake occurrence. Nature, 402, 605\u2013609.",
        "Michael A.J. (2011). Random variability explains apparent global clustering of large earthquakes. Geophys. Res. Lett., 38, L21301.",
        "Shearer P.M., Stark P.B. (2012). Global risk of big earthquakes has not recently increased. PNAS, 109(3), 717\u2013721.",
        "Ogata Y. (1988). Statistical models for earthquake occurrences and residual analysis. J. Amer. Stat. Assoc., 83, 9\u201327.",
        "Benjamini Y., Hochberg Y. (1995). Controlling the false discovery rate. J. Roy. Stat. Soc. B, 57(1), 289\u2013300.",
        "Gardner J.K., Knopoff L. (1974). Is the sequence of earthquakes in Southern California Poissonian? BSSA, 64, 1363\u20131367.",
        "Woessner J., Wiemer S. (2005). Assessing the quality of earthquake catalogues. BSSA, 95, 684\u2013698.",
        "Young J.B. et al. (1996). The Flinn\u2013Engdahl regionalization scheme: the 1995 revision. Phys. Earth Planet. Int., 96, 223\u2013297.",
    ]
    for i, r in enumerate(refs, 1):
        story.append(Paragraph(f"{i}. {r}", s["ref"]))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "<b>Acknowledgments.</b> The author acknowledges USGS, NOAA NGDC, and the ISC "
        "for maintaining open seismic catalogs. This work received no targeted funding.",
        s["body_ni"]
    ))
    return story


def main():
    out_dir = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "paper")
    )
    out_path = os.path.join(out_dir, "article_en.pdf")
    styles = make_styles()
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=TM, bottomMargin=BM + 0.7 * cm,
        title="Global Seismic Series",
        author="Yaroslav Marshalkin",
        subject="Statistical analysis of M\u22656.5 earthquake clustering",
    )
    doc.build(build(styles), onFirstPage=on_page, onLaterPages=on_page)
    print(f"\nPDF created: {out_path}")
    print(f"File size: {os.path.getsize(out_path) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
