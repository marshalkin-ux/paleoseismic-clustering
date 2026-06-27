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
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
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
        c.drawCentredString(self.box_w / 2, self.height / 2 - 5, self.text)


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(LM, BM - 0.5 * cm, PAGE_W - RM, BM - 0.5 * cm)
    canvas.setFont("Main", 8)
    canvas.setFillColor(MGREY)
    canvas.drawCentredString(
        PAGE_W / 2, BM - 0.9 * cm,
        f"Global Seismic Series  \u00b7  DOI: 10.20542/[placeholder]  \u00b7  {doc.page}"
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

    story.append(Paragraph("DOI: 10.20542/[placeholder]", s["doi"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Global Seismic Series: Statistical Analysis of Spatiotemporal "
        "Clustering in M\u22656.5 Earthquake Catalogs (2150 BCE \u2013 2026 CE)",
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
        "(from 4,418 CSV rows, incl. ~151 NOAA M&lt;6.5; 2150\u00a0BCE\u20132026\u00a0CE) "
        "using the Baiesi\u2013Paczuski metric \u03b7 with tectonic-path distance (Bird\u00a02003). "
        "47 global seismic series are identified (27 modern, 15 early, 5 historical candidates). "
        "Significance: permutation test (n=10,000, p&lt;0.0001, z=\u22126.17); ETAS validation "
        "(FPR=0/100, seed=42); FDR (45/47 at q=0.05). Series detection is a "
        "<b>statistical anomaly</b>, not proof of causal triggering. "
        "Largest series: 1905\u20131910 (193 events, 43 regions); "
        "most extensive modern: S170 (46 events, 12 regions, M<sub>max</sub>=9.1).",
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
        "exist in a four-millennium catalog of M\u22656.5 earthquakes, using an adapted "
        "\u03b7 metric with tectonic distance along Bird (2003) plate boundaries. "
        "<b>Novelty.</b> To our knowledge, this is the first global application of "
        "nearest-neighbor clustering with tectonic-path distance across historical, "
        "early instrumental, and modern catalogs, combined with ETAS validation and FDR correction.",
        s["body"]
    ))

    story += SEC("2. DATA AND METHODS", s)
    story += SSEC("2.1 Catalog compilation", s)
    story.append(Paragraph(
        "Three catalogs were merged: <b>USGS ComCat</b> (1900\u20132026, primary "
        "instrumental); <b>ISC Bulletin</b> (relocated hypocenters); and <b>NOAA NGDC</b> "
        "(historical and paleoseismic records from ~2150 BCE). Duplicates were merged "
        "using \u00b130 days and \u226450 km tolerance; source priority: ISC &gt; USGS &gt; NOAA. "
        "After deduplication (\u00b130 days, \u226450 km), the catalog contains "
        "<b>4,267</b> unique M\u22656.5 events (from <b>4,418</b> CSV rows, incl. ~151 M&lt;6.5 from NOAA). "
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
        "<b>Limitations:</b> 500 km snap and 1.5\u00d7 GC are approximations; "
        "intraplate pairs rely on GC penalty; sensitivity deferred to future work. "
        "Qualitatively improves inter-plate \u03b7 links by ~0.3 log<sub>10</sub>.",
        s["body"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(FormulaBox(
        "\u03b7\u1d62\u2c7c  =  t\u1d62\u2c7c  \u00b7  r\u1d62\u2c7c^1.6  \u00b7  10^(\u2212b\u00b7m\u1d62)",
        w
    ))
    story.append(Paragraph(
        "b=1.0 per Baiesi &amp; Paczuski (2004) for \u03b7 comparability; "
        "catalog b=0.911\u00b10.018 in Monte Carlo null only.",
        s["caption"]
    ))

    story += SSEC("2.3 Analysis pipeline", s)
    story.append(Paragraph(
        "Raw catalogs \u2192 dedup \u2192 GK declustering \u2192 \u03b7 NN forest "
        "\u2192 sliding windows \u2192 series criteria \u2192 MC/ETAS/FDR. "
        "GK: 24 aftershocks (2,017/2,041); ZBZ: 1 dependent (2,040/2,041) \u2014 "
        "sensitivity check, not sequential filter.",
        s["body"]
    ))

    story += SSEC("2.4 Threshold \u03b7\u2080 and series detection", s)
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
    story += SSEC("2.5 Statistical validation", s)
    story.append(Paragraph(
        "<b>Permutation test:</b> n = 10,000, p &lt; 0.0001, z = \u22126.17 (modern). "
        "<b>ETAS validation:</b> \u03bc=0.008, K=0.08, \u03b1=1.0, c=0.005 d, p=1.1; "
        "500 km cutoff; 100 catalogs (seed=42). FPR=0/100; p<sub>ETAS</sub>=0.0000. "
        "<b>Limitation:</b> FPR=0/100 at seed=42 is discrete; multi-seed robustness "
        "recommended; does not prove mechanism. "
        "<b>FDR (q=0.05):</b> 45/47 significant. "
        "<b>Declustering:</b> GK 2,017/2,041; ZBZ 2,040/2,041.",
        s["body"]
    ))

    story += SEC("3. RESULTS", s)
    story += SSEC("3.1 Identified series", s)
    story.append(Paragraph(
        "Full historical analysis yields <b>47 global seismic series</b>: 27 modern "
        "(p &lt; 0.0001), 15 early instrumental (p = 0.007; pre-1960 incompleteness "
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
        "belt (Kamchatka, Kuril Islands, Japan, Tonga, Indonesia). Tectonic distance "
        "lowers the \u03b7<sub>0</sub> threshold by ~0.3 log<sub>10</sub> units compared "
        "with Euclidean distance.",
        s["body"]
    ))

    story += SEC("4. DISCUSSION AND CONCLUSIONS", s)
    story.append(Paragraph(
        "<b>Statistical anomaly (established):</b> series incompatible with Poisson "
        "and local-only ETAS nulls; FDR 45/47. Conclusion about \u03b7 links and "
        "p-values, not causality. <b>Physical mechanism (not established):</b> "
        "series detection does not imply direct triggering; shared loading or "
        "mantle coupling are alternatives. <b>S170:</b> Hill [1993], Brodsky [2006] "
        "provide qualitative plausibility; \u0394CFS deferred. "
        "<b>Limitations:</b> ETAS FPR=0/100 at seed=42; tectonic distance approximations.",
        s["body"]
    ))
    for num, text in [
        ("1.", "4,267 M\u22656.5 events (4,418 CSV records) contain 47 global series; "
               "27 modern significant at p &lt; 0.0001."),
        ("2.", "ETAS validation (\u03bc=0.008, K=0.08, \u03b1=1.0, c=0.005 d, p=1.1, 500 km; "
               "FPR=0/100) and FDR (45/47) confirm non-randomness."),
        ("3.", "Largest series: 1905\u20131910 (193 events, 43 regions, M<sub>max</sub>=8.8); "
               "most spatially extensive modern: S170 (46 events, 12 regions, "
               "2002\u20132023, M<sub>max</sub>=9.1)."),
        ("4.", "Tectonic distance increases \u03b7 sensitivity by ~0.3 log<sub>10</sub>."),
        ("5.", "<b>Interpretive fork:</b> (a) if \u03b7 links are real \u2014 hazard "
               "implications without claiming direct triggering; (b) if artifacts \u2014 "
               "FDR+ETAS remains reproducible null-test. Co-occurrence may reflect "
               "shared tectonic loading."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>&nbsp;&nbsp;{text}", s["enum"]))
        story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "<b>Future work:</b> \u0394CFS for S047, S170, S095; multi-seed ETAS; Zenodo.",
        s["body_ni"]
    ))

    story += SEC("DATA AND CODE AVAILABILITY", s)
    story.append(Paragraph(
        "Data and code: github.com/marshalkin-ux/paleoseismic-clustering "
        "(docs/data_availability.md).",
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
