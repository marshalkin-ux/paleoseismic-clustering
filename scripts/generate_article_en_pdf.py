"""
generate_article_en_pdf.py
Generates article_en.pdf — English scientific article (IMRAD / GRL-style).
Uses reportlab; no external LaTeX required.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pdf_fonts import register_pdf_fonts, pdf_math_text, build_pdf_table, build_top5_table

register_pdf_fonts()
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable
DARK = HexColor("#1e3a5f")
ACCENT = HexColor("#2563eb")
TEXT = HexColor("#111111")
LGREY = HexColor("#f4f6f9")
MGREY = HexColor("#9ca3af")
RULE = HexColor("#cbd5e1")
PAGE_W, PAGE_H = A4
LM = RM = 2.5 * cm
TM = BM = 2.5 * cm


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
        c.drawCentredString(self.box_w / 2, self.height / 2 - 5, pdf_math_text(self.text))


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
    s["tbl_cell"] = ParagraphStyle("tbl_cell", fontName="Main", fontSize=8, textColor=TEXT, wordWrap="CJK", leading=11)
    s["tbl_wrap"] = ParagraphStyle("tbl_wrap", fontName="Main", fontSize=7, textColor=TEXT, wordWrap="CJK", leading=10)
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
        "Clustering in M\u22656.5 Earthquake Catalogs, 1973\u20132026 CE",
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
        "We analyse an <b>analysis catalog of 4,267 unique M\u22656.5 events</b> "
        "(modern window 1973\u20132026: 2,041 events; provenance: 4,418 CSV rows, "
        "~151 NOAA M&lt;6.5 excluded from clustering) "
        "using the Baiesi\u2013Paczuski metric eta with tectonic-path distance (Bird\u00a02003). "
        "The detector yields <b>47 algorithmic candidates</b> (27 modern); historical NOAA records "
        "(n=47) reported in Appendix A only. <b>Primary ETAS null</b> (literature H&amp;S 2003, "
        "decoupled): mean\u224815.4, p_ETAS\u22640.001 \u2014 deviation from literature ETAS "
        "indicates clustering this null does not fully describe; spatial analysis of ETAS "
        "residuals not conducted; not evidence for global series; circum-Pacific; "
        "<b>not</b> global chains beyond model scope (Sec. 5.4). GK mainshocks: N=27 unchanged. "
        "Global-series hypothesis <b>not supported</b> (Sec. 5.4\u20135.6). Permutation "
        "p=0.0001 (1/10,001) rejects temporal Poisson null only. Limitations \u2014 Sec. 5.6.",
        s["abstract"]
    ))
    story.append(Paragraph(
        "<b>Keywords:</b> global seismicity; seismic series; earthquake clustering; "
        "heuristic metric with tectonic hint; Baiesi\u2013Paczuski metric; ETAS validation; "
        "Monte Carlo; paleoseismology; remote triggering",
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
        "<b>Objective.</b> Test (and if warranted, <b>falsify</b>) the hypothesis that "
        "physically meaningful multi-regional global series exist, with "
        "<b>primary inference on the modern window (1973\u20132026)</b>, using complementary "
        "null tests (permutation vs ETAS) and explicit detector liberalness assessment. "
        "<b>Scope.</b> We combine nearest-neighbor clustering with heuristic tectonic hint "
        "and ETAS validation; this complements global rate tests "
        "(Michael 2011; Shearer &amp; Stark 2012) with a different \u03b7-linkage statistic "
        "but does not supersede their conclusions.",
        s["body"]
    ))
    story.append(Paragraph(
        "<b>§1.1 Research question.</b> Do physically meaningful multi-regional global "
        "series exist in M\u22656.5 (1973\u20132026)? (a) Permutation: p=0.0001 rejects "
        "Poisson times only. (b) ETAS H&amp;S: N=27 &gt; mean\u224815.4. "
        "(c) Global-series hypothesis: <b>not confirmed</b>. "
        "(d) WLS control (App.\u00a0B): p=1.0 \u2014 falsification, not primary null.",
        s["body_ni"]
    ))

    story += SEC("2. DATA AND METHODS", s)
    story += SSEC("2.1 Catalog compilation", s)
    story.append(Paragraph(
        "<b>Magnitude notation.</b> Catalog thresholds and detector gates use "
        "<b>M\u22656.5</b> (USGS ComCat, predominantly M<sub>w</sub>); individual events "
        "are cited with catalog type where relevant (e.g. M<sub>w</sub> 7.3).",
        s["body_ni"]
    ))
    story.append(Paragraph(
        "Three catalogs were merged: <b>USGS ComCat</b> (1900\u20132026, primary "
        "instrumental); <b>ISC Bulletin</b> (relocated hypocenters); and <b>NOAA NGDC</b> "
        "(historical and paleoseismic records pre-1900, 47 events). Duplicates were merged "
        "using \u00b130 days and \u226450 km tolerance; source priority: ISC &gt; USGS &gt; NOAA. "
        "After deduplication, the catalog contains "
        "<b>4,267</b> unique M\u22656.5 events (from <b>4,418</b> CSV rows; ~151 M&lt;6.5 "
        "excluded from clustering). "
        "USGS ComCat: <b>2,088</b> raw (1973\u20132026) \u2192 <b>2,041</b> after merge/ISC. "
        "GK: 24 aftershocks (2,017/2,041); ZBZ: 1 dependent (2,040/2,041). "
        "quality_score is metadata, not an inclusion filter. "
        "<b>Primary analysis set:</b> events 1900\u20132026 (4,218); 47 pre-1900 records "
        "remain in CSV (provenance) but are excluded from the primary detector pipeline "
        "and ETAS calibration window (1973\u20132026 only) \u2014 see Appendix A. "
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

    story += SSEC("2.2 Tectonic heuristic (deprecated)", s)
    story.append(Paragraph(
        "The Bird (2003) tectonic-path heuristic is <b>excluded from primary inference</b> "
        "(Appendix); <b>great-circle only</b>. Failure to validate shows metric "
        "<b>unsuitability</b>, not evidence against global series.",
        s["body"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(FormulaBox(
        "eta_ij  =  t_ij  *  r_ij^1.6  *  10^(-b*mi)",
        w
    ))
    story.append(Paragraph(
        "b=1.0 — deliberate Baiesi &amp; Paczuski (2004) simplification; catalog b=0.911\u00b10.018 "
        "for M<sub>c</sub>/completeness and MC null only — <b>not</b> in the \u03b7 formula. "
        "Equal N=27 <b>does not prove</b> candidate identity (Jaccard=1.0); upstream clusters "
        "at b=0.911 <b>not re-run</b> (~9.8% label mismatch).",
        s["caption"]
    ))

    story += SSEC("2.3 Analysis pipeline", s)
    story.append(Paragraph(
        "Raw catalogs \u2192 dedup \u2192 exclude M&lt;6.5 (~151 NOAA) \u2192 "
        "GK declustering (primary) \u2192 eta NN forest "
        "\u2192 sliding windows \u2192 merge overlapping \u2192 series criteria \u2192 MC/ETAS/FDR. "
        "GK: 24 aftershocks (2,017/2,041); ZBZ: 1 dependent (2,040/2,041) \u2014 "
        "different algorithms (GK: magnitude-dependent windows; ZBZ: \u03b7 NN + KDE threshold). "
        "At global M\u22656.5 scale ZBZ is permissive (sparse events \u2192 high \u03b7). "
        "GK is sole primary for inference; ZBZ sensitivity only, does not replace GK. "
        "If ZBZ were primary, N=27 likely unchanged (untested).",
        s["body"]
    ))
    story.append(Paragraph(
        "<b>Why GK\u2013ZBZ counts differ:</b> not contradictory methods \u2014 GK removes "
        "short-range fore/aftershocks via fixed windows; ZBZ classifies only 1 event with "
        "exceptionally low \u03b7 at global catalog scale. Under fixed gates GK/ZBZ/none "
        "all yield N=27 (sensitivity_declustering.json); different mainshock labels "
        "(24 vs 1) could matter for cluster analysis.",
        s["body"]
    ))
    story.append(Paragraph(
        "<b>Algorithm specification (§3.4.1).</b> GK WINDOWS, T(M)/R(M) interpolation, "
        "magnitude-descending; aftershocks [0,T], foreshocks [\u2212T/2,0); haversine. "
        "find_nearest_neighbor: causal argmin \u03b7, b=1.0, GC km. identify_clusters: "
        "Union\u2013Find, \u03b7\u2080 KDE. global_series: used[] mask, mean GC&gt;1500 km; "
        "merge 142\u219247 across epochs.",
        s["body_ni"]
    ))

    story += SSEC("2.4 Clustering and detector criteria", s)
    for num, text in [
        ("1.", "GK declustering (primary) \u2192 mainshocks for \u03b7 NN forest."),
        ("2.", "\u03b7 NN forest: b=1.0, r<sup>1.6</sup>; tectonic Bird 2003 (1.5\u00d7 GC fallback)."),
        ("3.", "Sliding windows 1, 2, 5 yr (1-yr step); merge 142\u219247."),
        ("4.", "<b>Detector gate:</b> N\u22654; M\u22656.5; mean pairwise GC&gt;1500 km."),
        ("5.", "Flinn\u2013Engdahl zone count \u2014 diagnostic only (not admission criterion)."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>&nbsp;&nbsp;{text}", s["enum"]))

    story += SSEC("2.5 Primary ETAS null", s)
    story.append(Paragraph(
        "<b>Primary ETAS null</b> uses literature H&amp;S 2003 parameters, decoupled "
        "from detector output. Catalog calibration scripts are Appendix reproducibility only.",
        s["body"]
    ))

    story += SSEC("2.6 Statistical validation", s)
    story.append(Paragraph(
        "<b>Permutation statement:</b> p=0.0001 rejects <b>Poisson event times only</b> "
        "(Ogata 1988); does not confirm global series.",
        s["body_ni"]
    ))
    story.append(Paragraph(
        "<b>Permutation test:</b> n = 10,000, p \u2264 0.0001, z = -6.17 (modern). "
        "<b>ETAS (primary):</b> literature H&amp;S: mean \u2248 15.4, p \u2264 0.001, N = 27. "
        "Interpretation \u2014 Sec. 4. GK mainshocks: N = 27. BH post-hoc \u2014 not discovery.",
        s["body"]
    ))

    story += SEC("3. RESULTS", s)
    story += SSEC("3.1 Identified series", s)
    story.append(Paragraph(
        "Full historical analysis yields <b>47 detector candidates</b> (not validated "
        "global series): 27 modern "
        "(p \u2264 0.0001), 15 early instrumental (p = 0.007; pre-1960 incompleteness "
        "caveat), 5 historical candidates (<b>not significant</b>, p = 0.46; "
        "47 M\u22656.5 events pre-1900). 142 cluster candidates before filtering. "
        "<i>Interpretation \u2014 Sec. 4.</i>",
        s["body"]
    ))

    story.append(build_top5_table(s, w, lang="en"))
    story.append(Paragraph(
        "Table 1. Top-5 detector candidates (not ETAS-validated physical series).",
        s["caption"]
    ))
    story.append(Spacer(1, 0.2 * cm))

    story += SSEC("3.2 Spatial\u2013temporal distribution", s)
    story.append(Paragraph(
        "Elevated detector candidate frequency (not validated physical series) "
        "occurs in 1952\u20131965 and 2002\u20132016 "
        "(post-Sumatra period). Spatially, clusters concentrate along the circum-Pacific "
        "belt (Kamchatka, Kuril Islands, Japan, Tonga, Indonesia). Tectonic diagnostic: "
        "median \u0394log\u2081\u2080\u03b7 = +0.28 on random pairs (mostly 1.5\u00d7 GC fallback).",
        s["body"]
    ))

    story += SSEC("3.3 Consolidated sensitivity table (modern window)", s)
    sens_rows = [
        ["Parameter", "Setting", "N_series"],
        ["GC gate", "1000 km", "27"],
        ["GC gate", "1500 km (baseline)", "27"],
        ["GC gate", "2000 km", "27"],
        ["Window", "1 yr", "53"],
        ["Window", "2 yr (baseline)", "27"],
        ["Window", "5 yr", "11"],
        ["Window", "10 yr", "6"],
        ["b in \u03b7", "1.0 (BP 2004)", "27"],
        ["b in \u03b7", "0.911 (catalog)", "27"],
        ["b overlap (series sets)", "Jaccard=1.0; upstream ~9.8%", "27"],
        ["Declustering", "GK / ZBZ / none", "27 / 27 / 27"],
        ["min_events (strict)", "5 / 6 / 8", "27 / 27 / 27"],
        ["Catalog", "GK mainshocks only", "27"],
        ["\u03b7\u2080 \u00b120%", "not_applied", "\u2014"],
    ]
    story.append(build_pdf_table(sens_rows, [0.30, 0.52, 0.18], w, s))
    story.append(Paragraph(
        "Table 2. N_series sensitivity under fixed detector gates "
        "(mean GC &gt; 1500 km, N \u2265 4). Sources: sensitivity_*.json.",
        s["caption"]
    ))
    story.append(Spacer(1, 0.2 * cm))

    story += SEC("4. DISCUSSION", s)
    story.append(Paragraph(
        "<b>WLS negative control (App.\u00a0B):</b> p_ETAS = 1.0, mean = 27 = N_obs \u2014 "
        "detector\u2013calibration coupling; supports negative conclusion; WLS invalid for "
        "inference; literature H&amp;S remains primary null until spatial MLE.",
        s["body_ni"]
    ))
    story.append(Paragraph(
        "The detector is <b>liberal</b>: literature ETAS p \u2264 0.001, N = 27. "
        "Bird tectonic heuristic excluded; failure shows unsuitability, not evidence "
        "against global series. Compatible with Michael (2011) and Shearer &amp; Stark (2012).",
        s["body"]
    ))

    story += SEC("5. CONCLUSIONS", s)
    story.append(Paragraph(
        "The detector is <b>liberal</b>: literature ETAS yields mean \u2248 15.4, "
        "p_ETAS \u2264 0.001. Global-series hypothesis <b>not supported</b>. "
        "WLS control: p = 1.0 \u2014 falsification framing, not primary null. "
        "Permutation rejects Poisson times only (Ogata 1988).",
        s["body"]
    ))
    for num, text in [
        ("1.", "Heuristic with tectonic hint: 98% GC fallback \u2014 failed hypothesis test."),
        ("2.", "47 detector candidates indistinguishable from ETAS null; "
               "\u0394CFS/dynamic stress \u2014 future work only."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>&nbsp;&nbsp;{text}", s["enum"]))
        story.append(Spacer(1, 0.1 * cm))

    story += SSEC("5.5 ETAS null limitations", s)
    story.append(Paragraph(
        "Primary null uses <b>literature H&amp;S 2003 only</b>; spatial Ogata (1998) MLE with "
        "confidence intervals is not implemented. Catalog calibration \u2014 Appendix B "
        "(reproducibility, not inference). The negative outcome also rests on no physical "
        "mechanism, failed tectonic metric (98% GC fallback), and liberal search (142 windows).",
        s["body"]
    ))

    story += SSEC("5.6 Limitations", s)
    lim_rows = [
        ["Limitation", "Affected step", "Impact on main conclusion"],
        [
            "\u03b7\u2080 unverified at global scale",
            "GK/ZBZ identify_clusters",
            "KDE valley \u2248 7.1\u00d710\u207b\u2076; global_series skips \u03b7\u2080 \u2192 N=27; "
            "mis-specified \u03b7\u2080 shifts GK/ZBZ labels only",
        ],
        [
            "b = 1.0 vs 0.911 in \u03b7",
            "\u03b7 upstream",
            "N_series = 27 both; cluster labels not re-run",
        ],
        [
            "No spatial Ogata MLE",
            "ETAS null",
            "Literature null only; not publication-grade catalog fit",
        ],
        [
            "142 windows + merge",
            "Detector",
            "Main source of liberalness",
        ],
        [
            "Literature p \u2264 0.001",
            "ETAS test",
            "ETAS-unexplained clustering; circum-Pacific; not global chains",
        ],
    ]
    story.append(build_pdf_table(lim_rows, [0.24, 0.22, 0.54], w, s, wrap_col=2))
    story.append(Paragraph(
        "Table 3. Limitation \u2192 affected step \u2192 impact on main conclusion (Sec. 5.6).",
        s["caption"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(
        "<b>Impact analysis.</b> N = 27 is computed by global_series() without \u03b7\u2080 "
        "filtering; b = 1.0 vs 0.911 leaves N_series = 27 under fixed gates, but upstream "
        "clusters at b = 0.911 were not re-verified. 142 sliding windows dominate detector "
        "liberalness.",
        s["body_ni"]
    ))

    story += SEC("APPENDIX A. PRE-1900 NOAA RECORDS", s)
    story.append(Paragraph(
        "Forty-seven fragmentary paleoseismic/historical M\u22656.5 records from NOAA NGDC "
        "are retained in data/processed/unified_catalog_full.csv for provenance (not removed). "
        "These 47 events are <b>excluded from the primary detector pipeline and ETAS calibration "
        "window</b>: pipeline_v2.py and calibrate_etas.py use the modern catalog 1973\u20132026 "
        "only (N=2,041). Epoch-stratified counts include pre-1900 descriptively via "
        "run_full_historical_analysis.py but do not enter primary significance claims.",
        s["body"]
    ))

    story += SEC("APPENDIX B. CATALOG-MATCHED WLS NEGATIVE CONTROL", s)
    story.append(Paragraph(
        "<b>Reproducibility negative control only \u2014 not inference.</b> Catalog-matched WLS "
        "(results/etas_calibration.json: \u03bc\u22480.103, K\u22480.495) yields mean=27.0, "
        "p_ETAS=1.0 (n=1000; multiseed stable). Illustrates <b>detector\u2013calibration coupling</b>; "
        "<b>not</b> used for inference. <b>Do not cite</b> p_ETAS=1.0 in abstract, conclusions, "
        "or hero metrics.",
        s["body"]
    ))
    wls_rows = [
        ["Component", "Method"],
        ["\u03bc", "GK mainshocks / T (closed form)"],
        ["c, p", "Omori MLE, Nelder\u2013Mead on 24 delays"],
        ["K, \u03b1", "WLS (numpy.linalg.lstsq) on same 24 GK aftershocks"],
    ]
    story.append(build_pdf_table(wls_rows, [0.22, 0.78], w, s))
    story.append(Spacer(1, 0.15 * cm))

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
