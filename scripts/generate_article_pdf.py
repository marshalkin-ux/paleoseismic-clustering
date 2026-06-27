"""
generate_article_pdf.py
Генерирует article_ru.pdf — научная статья по шаблону российского журнала.
Использует reportlab для Cyrillic-safe PDF без внешнего LaTeX.
"""

import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus.flowables import Flowable

# ── Font registration (Cyrillic) ─────────────────────────────────────────────
_FONT_DIR = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont("Main",       os.path.join(_FONT_DIR, "arial.ttf")))
pdfmetrics.registerFont(TTFont("MainBold",   os.path.join(_FONT_DIR, "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("MainItalic", os.path.join(_FONT_DIR, "ariali.ttf")))
pdfmetrics.registerFont(TTFont("MainBI",     os.path.join(_FONT_DIR, "arialbi.ttf")))


# ── Unicode → ASCII safety filter (Arial TTF lacks many specialty glyphs) ────
def safe_text(s: str) -> str:
    """Replace chars unsupported by Arial with ASCII equivalents."""
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
        ("m\u1d62", "m_i"),
        ("\u03bc", "mu"),
        ("\u03b1", "alpha"),
        ("\u03b7", "eta"),
        ("\u0394", "Delta"),
        ("\u00d7", "x"),
        ("\u00b7", " "),
        ("\u00a7", "Sec."),
        ("\u2192", "->"),
        ("\u2193", "v"),
        ("\u2212", "-"),
        ("\u2264", "<="),
        ("\u2265", ">="),
        ("\u00b1", "+/-"),
        ("\u202f", " "),
        ("\u2047", "?"),
        ("\u0301", ""),
        ("\u0305", ""),
    ]
    for old, new in _phrase_subs:
        s = s.replace(old, new)

    _sub_map = str.maketrans({
        "\u2080": "0", "\u2081": "1", "\u2082": "2", "\u2083": "3",
        "\u2084": "4", "\u2085": "5", "\u2086": "6", "\u2087": "7",
        "\u2088": "8", "\u2089": "9",
        "\u2090": "a", "\u2091": "e", "\u2092": "o", "\u2093": "x",
        "\u2098": "m", "\u2099": "n", "\u209b": "s", "\u209c": "t",
        "\u1d62": "i", "\u2c7c": "j",
    })
    s = s.translate(_sub_map)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s


_BaseParagraph = Paragraph


class Paragraph(_BaseParagraph):  # type: ignore[misc]
    def __init__(self, text, style, *args, **kwargs):
        if isinstance(text, str):
            text = safe_text(text)
        super().__init__(text, style, *args, **kwargs)


# ── Palette ───────────────────────────────────────────────────────────────────
DARK      = HexColor("#1e3a5f")
ACCENT    = HexColor("#2563eb")
TEXT      = HexColor("#111111")
LGREY     = HexColor("#f4f6f9")
MGREY     = HexColor("#9ca3af")
RULE      = HexColor("#cbd5e1")
PAGE_W, PAGE_H = A4
LM = RM = 2.5 * cm
TM = BM = 2.5 * cm


# ── Formula box ───────────────────────────────────────────────────────────────
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


# ── Page template ─────────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(LM, BM - 0.5 * cm, PAGE_W - RM, BM - 0.5 * cm)
    canvas.setFont("Main", 8)
    canvas.setFillColor(MGREY)
    canvas.drawCentredString(
        PAGE_W / 2, BM - 0.9 * cm,
        safe_text(f"Глобальные сейсмические серии  \u00b7  Yaroslav Marshalkin  \u00b7  {doc.page}")
    )
    canvas.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    s = {}

    s["doi"] = ParagraphStyle("doi", fontName="MainBold", fontSize=9,
                               textColor=DARK, spaceAfter=2)
    s["title_ru"] = ParagraphStyle("title_ru", fontName="MainBold", fontSize=16,
                                    textColor=DARK, alignment=TA_CENTER,
                                    spaceAfter=6, leading=22)
    s["title_en"] = ParagraphStyle("title_en", fontName="MainBold", fontSize=13,
                                    textColor=DARK, alignment=TA_CENTER,
                                    spaceAfter=6, leading=18)
    s["copyright"] = ParagraphStyle("copyright", fontName="MainItalic", fontSize=9,
                                     textColor=MGREY, alignment=TA_CENTER,
                                     spaceAfter=8)
    s["meta"] = ParagraphStyle("meta", fontName="Main", fontSize=9,
                                textColor=TEXT, spaceAfter=3, leading=13)
    s["abstract_label"] = ParagraphStyle("abstract_label", fontName="MainBold",
                                          fontSize=10, textColor=DARK, spaceAfter=2)
    s["abstract"] = ParagraphStyle("abstract", fontName="MainItalic", fontSize=9,
                                    textColor=TEXT, alignment=TA_JUSTIFY,
                                    spaceAfter=6, leading=13, leftIndent=10,
                                    rightIndent=10)
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
    s["bullet"] = ParagraphStyle("bullet", fontName="Main", fontSize=10,
                                  textColor=TEXT, leftIndent=18,
                                  spaceAfter=3, leading=14)
    s["enum"] = ParagraphStyle("enum", fontName="Main", fontSize=10,
                                textColor=TEXT, leftIndent=22,
                                spaceAfter=4, leading=14)
    s["ref"] = ParagraphStyle("ref", fontName="Main", fontSize=9,
                               textColor=TEXT, leftIndent=18, firstLineIndent=-18,
                               spaceAfter=3, leading=13)
    s["caption"] = ParagraphStyle("caption", fontName="MainItalic", fontSize=9,
                                   textColor=MGREY, alignment=TA_CENTER,
                                   spaceAfter=4)
    s["tbl_hdr"] = ParagraphStyle("tbl_hdr", fontName="MainBold", fontSize=9,
                                   textColor=white, alignment=TA_CENTER)
    s["tbl_cell"] = ParagraphStyle("tbl_cell", fontName="Main", fontSize=9,
                                    textColor=TEXT)
    return s


def HR():
    return HRFlowable(width="100%", thickness=0.5, color=RULE,
                      spaceAfter=4, spaceBefore=4)


def SEC(text, s):
    return [HR(), Paragraph(text, s["section"])]


def SSEC(text, s):
    return [Paragraph(text, s["subsection"])]


def SSSEC(text, s):
    return [Paragraph(text, s["subsubsection"])]


# ── Story builder ─────────────────────────────────────────────────────────────
def build(s):
    story = []

    # === PAGE 1: Header ========================================================
    story.append(Paragraph(
        "Глобальные сейсмические серии: статистический анализ "
        "пространственно-временно\u0301й кластеризации землетрясений "
        "M\u22656.5 за 1973\u20132026\u00a0гг.",
        s["title_ru"]
    ))
    story.append(Paragraph("\u00a9 2026\u00a0г.\u00a0\u00a0Ярослав Маршалкин",
                            s["copyright"]))
    story.append(HR())
    story.append(Spacer(1, 0.2 * cm))

    # --- RU metadata ---
    story.append(Paragraph(
        "<b>Ярослав Маршалкин</b><br/>"
        "e-mail: marshalkin@gmail.com<br/>"
        "Telegram: @MRSHLKN &nbsp;|&nbsp; "
        "GitHub: github.com/marshalkin-ux/paleoseismic-clustering",
        s["meta"]
    ))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("<b>Аннотация.</b>", s["abstract_label"]))
    story.append(Paragraph(
        "Статья посвящена статистическому анализу пространственно-временно\u0301й "
        "кластеризации землетрясений M\u22656.5 по объединённому каталогу "
        "4418\u00a0записей CSV (вкл. ~151\u00a0M&lt;6.5 из NOAA), "
        "4267\u00a0уникальных событий M\u22656.5 (4418\u00a0строк CSV; анализ M\u22656.5; "
        "2041\u00a0событие в современном окне 1973\u20132026). "
        "Обнаружение серий\u00a0\u2014 статистическая аномалия (eta-связи, p-values); "
        "причинный механизм не установлен. "
        "Источники: USGS\u00a0ComCat, ISC\u00a0Bulletin, NOAA\u00a0NGDC "
        "(M<sub>c</sub>=6.55, b=0.911+/-0.018). "
        "На основе метрики Байеси\u2013Пачуски с тектоническим расстоянием "
        "(граф Bird\u00a02003) выявлено 47\u00a0глобальных серий в трёх эпохах "
        "(27\u00a0современных, 15\u00a0ранних, 5\u00a0исторических). "
        "Трёхуровневая валидация: перестановочный тест (n=10\u202f000, "
        "p=0.0001 (1/10,001), z=-6.17); ETAS-нулевая модель (1000\u00a0синтетических "
        "каталогов, FPR=1000/1000; калибр. null: mean 27,0, p_ETAS=1,0; "
        "лит. \u03bc=0,008: mean 15,4, p\u22640,001); "
        "коррекция FDR Бенджамини\u2013Хохберга (q=0.05, 45/47\u00a0серий значимы). "
        "Крупнейшая серия по числу событий\u00a0\u2014 1905\u20131910 (193\u00a0события, "
        "43\u00a0региона, Mmax=8.8); наиболее масштабная современная\u00a0\u2014 "
        "S170 (46\u00a0событий, 12\u00a0регионов, Mmax=9.1, 2002\u20132023).",
        s["abstract"]
    ))

    story.append(Paragraph(
        "<b>Ключевые слова:</b> глобальная сейсмичность; сейсмические серии; "
        "тектоническое расстояние; кластеризация землетрясений; метрика Байеси\u2013Пачуски; "
        "Монте-Карло; Флинн\u2013Энгдал; палеосейсмология; статистический триггеринг; "
        "Gutenberg\u2013Richter",
        s["keywords"]
    ))

    story.append(Paragraph(
        "<b>Благодарность.</b> Авторы выражают признательность USGS, NOAA NGDC и ISC "
        "за поддержание открытых сейсмологических каталогов. "
        "Работа выполнена без целевого финансирования.",
        s["body_ni"]
    ))
    story.append(HR())
    story.append(Spacer(1, 0.3 * cm))

    # --- EN metadata ---
    story.append(Paragraph(
        "Global Seismic Series: Statistical Analysis of Spatiotemporal "
        "Clustering in M\u22656.5 Earthquake Catalogs, 1973\u20132026 CE",
        s["title_en"]
    ))
    story.append(Paragraph(
        "<b>Ярослав Маршалкин (Yaroslav Marshalkin)</b><br/>"
        "e-mail: marshalkin@gmail.com &nbsp;|&nbsp; Telegram: @MRSHLKN",
        s["meta"]
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("<b>Abstract.</b>", s["abstract_label"]))
    story.append(Paragraph(
        "Whether large earthquakes cluster in space and time beyond chance is a "
        "foundational question in seismic hazard assessment. We analyse a merged "
        "catalog of <b>4,267 unique M&gt;=6.5 events</b> (from 4,418 CSV rows; "
        "~151 NOAA M&lt;6.5 rows excluded from clustering; 47\u00a0historical NOAA records pre-1900), "
        "identifying 47 global seismic series in three temporal windows. "
        "Significance is assessed by a three-level framework: permutation test "
        "(n=10,000, p=0.0001 (1/10,001), z=-6.17), ETAS null-model validation "
        "(1000 synthetic catalogs, FPR=1000/1000; catalog-calibrated null: mean 27.0, "
        "p_ETAS=1.0; literature defaults \u03bc=0.008: mean 15.4, p\u22640.001; "
        "N_obs=27), "
        "and Benjamini\u2013Hochberg FDR correction (q=0.05, N=47; 45/47 significant). "
        "The largest series by event count is 1905\u20131910 (193 events, 43 regions, "
        "Mmax=8.8); the most spatially extensive modern series is S170 "
        "(46 events, 12 Flinn\u2013Engdahl regions, 2002\u20132023, Mmax=9.1), "
        "including the 2004 Indian Ocean earthquake. Tectonic-path diagnostic "
        "(scripts/generate_grl_figures.py): median \u0394log\u2081\u2080\u03b7 = +0.28 "
        "vs great-circle on random pairs (mostly 1.5\u00d7 GC fallback).",
        s["abstract"]
    ))
    story.append(Paragraph(
        "<b>Keywords:</b> global seismicity; seismic series; tectonic distance; "
        "earthquake clustering; Baiesi\u2013Paczuski metric; Monte Carlo; Flinn\u2013Engdahl; "
        "paleoseismology; statistical triggering; Gutenberg\u2013Richter",
        s["keywords"]
    ))
    story.append(Paragraph(
        "<b>About the author:</b> Yaroslav Marshalkin \u2014 independent researcher. "
        "Contact: marshalkin@gmail.com, Telegram @MRSHLKN.",
        s["body_ni"]
    ))
    story.append(PageBreak())

    # === SECTION: ВВЕДЕНИЕ =====================================================
    story += SEC("ВВЕДЕНИЕ (ПОСТАНОВКА ПРОБЛЕМЫ)", s)
    story.append(Paragraph(
        "Одним из фундаментальных вопросов современной сейсмологии является вопрос о том, "
        "образуют ли крупные землетрясения (M\u22656.5) систематические "
        "пространственно-временны\u0301е серии, выходящие за рамки локальных афтершоковых зон, "
        "или наблюдаемая группировка является случайной флуктуацией пуассоновского процесса. "
        "Практическое значение ответа трудно переоценить: если мультирегиональные серии "
        "реальны, условная вероятность крупного события в удалённых тектонических зонах "
        "существенно меняется\u00a0\u2014 что напрямую влияет на вероятностный анализ "
        "сейсмической опасности [Cornell, 1968].",
        s["body"]
    ))
    story.append(Paragraph(
        "Первые систематические свидетельства дистанционного триггеринга получили "
        "Hill et al. [1993] после землетрясения Ланделс-Хиллс (Landers, Mw 7.3, "
        "1992\u00a0г.): сейсмическая активность возникла на расстояниях свыше 1000\u00a0км. "
        "Brodsky & Prejean [2006] показали, что поверхностные волны способны инициировать "
        "рои в вулканических зонах на тысячи километров. Землетрясение Суматра\u2013Андаман "
        "2004\u00a0г. (Mw 9.1) активировало ряд удалённых сегментов, что ряд "
        "авторов объясняет долгосрочным глобальным возмущением поля напряжений "
        "[Freed, Lin, 2001; Pollitz et al., 1998].",
        s["body"]
    ))
    story.append(Paragraph(
        "Тем не менее систематичность подобных связей оспаривается. Michael [2011] "
        "показал, что кластеризация M\u22657 в 1995\u20132011\u00a0гг. статистически "
        "неотличима от случайных флуктуаций. Shearer & Stark [2012] подтвердили, "
        "что глобальные частоты M\u22657 и M\u22658 не возросли после Суматры 2004. "
        "Дискуссию дополнили работы по дублетам [Kagan, Jackson, 1999]: "
        "повышенная вероятность второго события вблизи эпицентра первого "
        "подтверждает локальные корреляции, не исчерпывая дальнодействующих связей.",
        s["body"]
    ))
    story.append(Paragraph(
        "Модель ETAS [Ogata, 1988] откалибрована для региональных сетей и "
        "не описывает межплитные корреляции. Метрика Байеси\u2013Пачуски [2004] и "
        "её обобщение Зализяпина\u2013Бен-Зиона [2008, 2013] позволяют объективно "
        "выявлять кластеры, но используют евклидово расстояние, игнорируя "
        "плитно-тектоническую геометрию литосферы.",
        s["body"]
    ))
    story.append(Paragraph(
        "<b>Цель работы</b>\u00a0\u2014 проверить гипотезу о наличии мультирегиональных серий "
        "в инструментальном каталоге 1973\u20132026\u00a0гг. с применением адаптированной "
        "метрики eta с тектоническим расстоянием вдоль границ плит Bird (2003). "
        "<b>Охват</b>: кластеризация с тектоническим расстоянием, ETAS и FDR; "
        "дополняет тесты частот Michael (2011) и Shearer &amp; Stark (2012), "
        "не отменяя их выводы.",
        s["body"]
    ))

    # === SECTION: СОДЕРЖАНИЕ ==================================================
    story += SEC("СОДЕРЖАНИЕ ПРОВЕДЁННОГО ИССЛЕДОВАНИЯ", s)

    # --- 1. Данные ---
    story += SSEC("1. Данные", s)
    story += SSSEC("1.1 Источники и формирование каталога", s)
    story.append(Paragraph(
        "Исследование основано на трёх каталогах: <b>USGS ComCat</b>\u00a0\u2014 "
        "инструментальный, с 1900\u00a0г., M\u22654.5, использованы записи M\u22656.5 "
        "за 1973\u20132026\u00a0гг.; <b>ISC Bulletin</b>\u00a0\u2014 переопределённые "
        "гипоцентры для верификации; <b>NOAA NGDC</b>\u00a0\u2014 исторические и "
        "палеосейсмические события до 1900\u00a0г. (47\u00a0записей). "
        "Дублирующие записи: допуск \u00b130\u00a0сут., \u226450\u00a0км; "
        "ранг надёжности ISC\u00a0>\u00a0USGS\u00a0>\u00a0NOAA. "
        "После дедупликации (допуск \u00b130\u00a0сут., \u226450\u00a0км) каталог содержит "
        "4267\u00a0уникальных событий M\u22656.5 (из 4418\u00a0CSV-строк, вкл. ~151\u00a0M&lt;6.5 из NOAA). "
        "USGS\u00a0ComCat: <b>2088</b> сырых M\u22656.5 (1973\u20132026) \u2192 "
        "<b>2041</b> после merge/ISC. GK удаляет ~24\u00a0афтершока "
        "(2017\u00a0независимых, 98.8\u00a0%). "
        "quality_score 0.30\u20130.95 \u2014 метаданные по эпохе и фазовым отсчётам "
        "(Woessner\u00a0&amp;\u00a0Wiemer\u00a02005), не критерий отбора. "
        "Итоговый каталог: <b>4267</b> событий M\u22656.5 (<b>4418</b> записей CSV); "
        "2041\u00a0\u2014 современный (1973\u20132026), "
        "2179\u00a0\u2014 ранний (1900\u20131972), "
        "47\u00a0\u2014 исторический (фрагментарные палеосейсмические записи).",
        s["body"]
    ))
    story += SSSEC("1.2 Анализ полноты каталога", s)
    story.append(Paragraph(
        "Метод максимальной кривизны даёт M\u2090=6.55. Оценка b-значения методом "
        "максимального правдоподобия по 1688 событиям выше M\u2090:",
        s["body"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(FormulaBox("b = 0.911 \u00b1 0.018  (n = 1688 событий)",
                             PAGE_W - LM - RM))
    story.append(Spacer(1, 0.15 * cm))

    # --- 2. Методология ---
    story += SSEC("2. Методология", s)
    story += SSSEC("2.1 Тектоническое расстояние", s)
    story.append(Paragraph(
        "Нами введена метрика тектонического расстояния r_ij — "
        "длина кратчайшего пути между гипоцентрами вдоль глобального графа границ плит "
        "Bird (2003), включающего 20\u00a0сегментов (субдукционные зоны, трансформные "
        "разломы, срединно-океанические хребты). Кратчайший путь находится алгоритмом "
        "Дейкстры (пакет NetworkX). Если гипоцентр удалён &gt;500\u00a0км от ближайшего "
        "узла границы или путь по графу отсутствует, применяется фолбэк: "
        "r_ij = 1.5 x r_GC (дуга большого круга). "
        "<b>Аудит фолбэка</b> (analyze_tectonic_fallback.py, fig07): "
        "4987 пар из 500 событий; 98.0% GC-фолбэк 1.5×, 2.0% Dijkstra "
        "(4015 snap&gt;500 km, 872 нет пути, 100 Dijkstra; 95 существенно "
        "отличаются; примеры FE31 Япония, FE35 Филиппины). "
        "Метрика значима только для ~2% пар у границ. "
        "Диагностика (generate_grl_figures.py): "
        "медиана Δlog₁₀η = +0.28 (~98% — GC-фолбэк 1.5×).",
        s["body"]
    ))
    story += SSSEC("2.2 Метрика связности eta", s)
    story.append(Paragraph(
        "Вслед за Baiesi & Paczuski [2004] и Zaliapin et al. [2008] определим "
        "метрику связности между претендентом-родителем i и последующим событием j:",
        s["body"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(FormulaBox(
        "eta_ij  =  t_ij  *  r_ij^1.6  *  10^(-b*mi)",
        PAGE_W - LM - RM
    ))
    story.append(Paragraph(
        "b=1.0 — конвенция Baiesi &amp; Paczuski (2004) для сопоставимости eta; "
        "эмпирическое b=0.911+/-0.018 — только в Monte Carlo-нуле и оценке полноты.",
        s["caption"]
    ))
    story.append(Spacer(1, 0.1 * cm))
    comp_data = [
        [Paragraph("<b>Компонент</b>", s["tbl_hdr"]),
         Paragraph("<b>Обозначение</b>", s["tbl_hdr"]),
         Paragraph("<b>Физический смысл</b>", s["tbl_hdr"])],
        [Paragraph("Время", s["tbl_cell"]),
         Paragraph("t\u1d62\u2c7c (лет)", s["tbl_cell"]),
         Paragraph("Штраф за большой временно\u0301й разрыв", s["tbl_cell"])],
        [Paragraph("Расстояние", s["tbl_cell"]),
         Paragraph("r\u1d62\u2c7c^1.6 (км)", s["tbl_cell"]),
         Paragraph("Штраф за большое тектоническое расстояние", s["tbl_cell"])],
        [Paragraph("Магнитуда", s["tbl_cell"]),
         Paragraph("10^(\u2212b\u00b7m\u1d62)", s["tbl_cell"]),
         Paragraph("Усиление связи при большой магнитуде родителя", s["tbl_cell"])],
    ]
    cw = [(PAGE_W - LM - RM) * f for f in [0.18, 0.22, 0.60]]
    comp_tbl = Table(comp_data, colWidths=cw)
    comp_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR",  (0, 0), (-1, 0), white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LGREY]),
        ("BOX",       (0, 0), (-1, -1), 0.5, RULE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, RULE),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(comp_tbl)
    story.append(Spacer(1, 0.2 * cm))

    story += SSSEC("2.3 Конвейер анализа", s)
    story.append(Paragraph(
        "Сырые каталоги \u2192 дедупликация \u2192 исключить M&lt;6.5 (~151 NOAA) "
        "\u2192 GK-декластеризация (основной) \u2192 eta NN-лес "
        "\u2192 скользящие окна \u2192 объединение перекрывающихся \u2192 критерии серии "
        "\u2192 MC/ETAS/FDR. GK: 24 афтершока (2017/2041, 98.8%). "
        "ZBZ: 1 зависимое (2040/2041) \u2014 отдельная проверка чувствительности, "
        "не последовательный фильтр. run_full_historical_analysis.py: global_series() "
        "без GK-префильтра.",
        s["body"]
    ))

    story += SSSEC("2.4 Порог \u03b7\u2080, поиск серий и параметры ETAS", s)
    story.append(Paragraph(
        "Порог \u03b7\u2080 выбирается автоматически из распределения \u03b7 ближайших соседей: "
        "KDE-детекция долины между модами log\u2081\u2080(\u03b7) (Zaliapin\u00a0&amp;\u00a0Ben-Zion\u00a02013); "
        "по умолчанию \u03b7\u2080 = 10<sup>median log\u2081\u2080 \u03b7</sup>. "
        "Валидация против пуассоновского перестановочного нуля (Monte Carlo, n=10\u202f000).",
        s["body"]
    ))
    steps = [
        ("1.", "Декластеризация Gardner\u2013Knopoff [1974] для удаления локальных афтершоков."),
        ("2.", "Лес ближайших соседей: для j\u00a0\u2014 родитель i* = argmin \u03b7\u1d62\u2c7c при \u03b7\u1d62\u2c7c < \u03b7\u2080."),
        ("3.", "Критерий глобальной серии: N\u22654; M\u22656.5; \u22653 зон Флинна\u2013Энгдала."),
        ("4.", "Скользящие окна: 1, 2, 5\u00a0лет; перекрывающиеся группы объединяются."),
    ]
    for num, text in steps:
        story.append(Paragraph(f"<b>{num}</b>\u00a0\u00a0{text}", s["enum"]))
    story.append(Paragraph(
        "<b>ETAS-параметры (калибровка на каталоге):</b> "
        "MLE на 2041 событии (scripts/calibrate_etas.py, results/etas_calibration.json): "
        "\u03bc\u22480,103, K\u22480,495, \u03b1\u22480,063, c\u224810\u207b\u2074 сут., p\u22481,36. "
        "Литературные defaults (Helmstetter &amp; Sornette 2003: \u03bc=0,008, K=0,08) "
        "сохранены для сравнения. Multiseed — перспектива.",
        s["body"]
    ))

    story += SSSEC("2.5 Статистическая валидация", s)
    story.append(Paragraph(
        "<b>Тест Монте-Карло.</b> n\u209b\u1d62\u2098=10\u202f000 перестановок: "
        "p=0.0001 (1/10,001), z=\u22126.17 для современного периода. "
        "<b>ETAS-валидация.</b> Калиброванные параметры из etas_calibration.json; "
        "1000 синтетических каталогов (seed=42); порог 500 km. "
        "FPR=1000/1000; mean 27,0 (max 27); N_obs=27; p_ETAS=1,0 — неотличимо от null. "
        "Для сравнения, лит. \u03bc=0,008: mean 15,4, max 24, p_ETAS\u22640,001. "
        "<b>Ограничение:</b> детектор либерален (FPR=1000/1000); ужесточение критериев — перспектива. "
        "<b>FDR</b> (q=0.05): 45/47 значимы. "
        "<b>Декластеризация:</b> GK 2017/2041 (24 афтершока); "
        "ZBZ 2040/2041 (1 зависимое) \u2014 разные критерии, не последовательный фильтр.",
        s["body"]
    ))

    # --- 3. Результаты ---
    story += SSEC("3. Результаты", s)
    story += SSSEC("3.1 Идентифицированные серии", s)
    story.append(Paragraph(
        "Полный анализ выявил <b>47 глобальных серий</b>: 27\u00a0современных "
        "(p=0.0001, 1/10,001), 15\u00a0ранних (p=0.007, но quality_score&lt;0.7 до 1960\u00a0г. "
        "ограничивает интерпретацию), 5\u00a0исторических кандидатов "
        "(<b>статистически не значимы</b>, p=0.46; только 47\u00a0событий M\u22656.5 "
        "до 1900\u00a0г., фрагментарные палеосейсмические записи). "
        "142 кластера-кандидата до фильтрации. Топ-5 серий \u2014 в таблице ниже.",
        s["body"]
    ))

    tbl_cols = [(PAGE_W - LM - RM) * f for f in [0.09, 0.07, 0.11, 0.09, 0.20, 0.44]]
    tbl_data = [
        [Paragraph("<b>ID</b>", s["tbl_hdr"]),
         Paragraph("<b>N</b>", s["tbl_hdr"]),
         Paragraph("<b>Регионов</b>", s["tbl_hdr"]),
         Paragraph("<b>M\u2098\u2090\u2093</b>", s["tbl_hdr"]),
         Paragraph("<b>Период</b>", s["tbl_hdr"]),
         Paragraph("<b>Примечание</b>", s["tbl_hdr"])],
        [Paragraph("1905\u20131910", s["tbl_cell"]), Paragraph("193", s["tbl_cell"]),
         Paragraph("43", s["tbl_cell"]), Paragraph("8.8", s["tbl_cell"]),
         Paragraph("1905\u20131910", s["tbl_cell"]),
         Paragraph("Крупнейшая серия; ранний инструментальный период", s["tbl_cell"])],
        [Paragraph("S047", s["tbl_cell"]), Paragraph("53", s["tbl_cell"]),
         Paragraph("5", s["tbl_cell"]), Paragraph("8.0", s["tbl_cell"]),
         Paragraph("1982\u20132024", s["tbl_cell"]),
         Paragraph("Западная Пацифика, циркум-субдукц. коридор", s["tbl_cell"])],
        [Paragraph("S170", s["tbl_cell"]), Paragraph("46", s["tbl_cell"]),
         Paragraph("12", s["tbl_cell"]), Paragraph("9.1", s["tbl_cell"]),
         Paragraph("2002\u20132023", s["tbl_cell"]),
         Paragraph("Зондский пояс, Суматра 2004 (M\u00a09.1)", s["tbl_cell"])],
        [Paragraph("S095", s["tbl_cell"]), Paragraph("25", s["tbl_cell"]),
         Paragraph("4", s["tbl_cell"]), Paragraph("7.9", s["tbl_cell"]),
         Paragraph("1989\u20132017", s["tbl_cell"]),
         Paragraph("Западно-тихоокеанская дуга", s["tbl_cell"])],
        [Paragraph("S116", s["tbl_cell"]), Paragraph("22", s["tbl_cell"]),
         Paragraph("5", s["tbl_cell"]), Paragraph("8.2", s["tbl_cell"]),
         Paragraph("1993\u20132021", s["tbl_cell"]),
         Paragraph("Южная Пацифика, многодуговая серия", s["tbl_cell"])],
    ]
    main_tbl = Table(tbl_data, colWidths=tbl_cols)
    main_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR",  (0, 0), (-1, 0), white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LGREY]),
        ("BOX",       (0, 0), (-1, -1), 0.5, RULE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, RULE),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
    ]))
    story.append(main_tbl)
    story.append(Paragraph(
        "Таблица\u00a01. Топ-5 мультирегиональных серий (\u22653 регионов Флинна\u2013Энгдала).",
        s["caption"]
    ))
    story.append(Spacer(1, 0.2 * cm))

    story += SSSEC("3.2 Статистическая значимость", s)
    story.append(Paragraph(
        "Перестановочный тест (n\u209b\u1d62\u2098=10\u202f000):",
        s["body"]
    ))
    story.append(FormulaBox(
        "p \u2264 0.0001   (z = \u22126.17,  современный период 1973\u20132026)",
        PAGE_W - LM - RM
    ))
    story.append(FormulaBox(
        "p\u2091\u209c\u2090\u209b = 1,0   (ETAS калибр., 1000 кат., FPR=1000/1000, mean=27,0)",
        PAGE_W - LM - RM
    ))
    story.append(FormulaBox(
        "лит. \u03bc=0,008: mean 15,4, max 24, p\u2091\u209c\u2090\u209b \u2264 0,001   (сравнение)",
        PAGE_W - LM - RM
    ))
    story.append(Paragraph(
        "Коррекция FDR (q=0.05): 45 из 47 кандидатов остаются значимыми. "
        "Permutation test p=0,0001 (1/10 001) подтверждает структуру кластеризации; "
        "при калиброванном ETAS число серий неотличимо от локального null.",
        s["body_ni"]
    ))

    story += SSSEC("3.3 Пространственно-временно\u0301е распределение", s)
    story.append(Paragraph(
        "Повышенная активность серий: 1952\u20131965\u00a0гг. и 2002\u20132016\u00a0гг. "
        "(пост-суматранский период). Пространственно\u00a0\u2014 вдоль "
        "циркум-тихоокеанского пояса (Камчатка, Курилы, Япония, Тонга, Индонезия). "
        "Диагностика тектоники vs евклидовой метрики: медиана \u0394log\u2081\u2080\u03b7 = +0.28 "
        "на случайных парах (в основном GC-фолбэк 1.5\u00d7).",
        s["body"]
    ))
    story += SSEC("3.4 Обсуждение", s)
    story.append(Paragraph(
        "<b>Статистическая аномалия (установлено):</b> серии несовместимы с пуассоновским "
        "нулём (p=0,0001, 1/10 001); FDR 45/47. ETAS при калибровке: mean=27,0, p_ETAS=1,0 "
        "(детектор либерален, FPR=1000/1000). Это вывод об \u03b7-связях и p-values, "
        "не о причинности. <b>Физический механизм (не установлен):</b> обнаружение серий "
        "не подразумевает прямой триггеринг; возможны общая нагрузка и мантийное сцепление. "
        "Предварительные тесты Coulomb/динамического стресса S170 не достигли порогов "
        "(дополнение в репозитории). "
        "Michael [2011] и Shearer &amp; Stark [2012] тестировали дополнительные null-модели "
        "частот; наш η-тест добавляет иную статистику, не отменяя их выводы. "
        "<b>Ограничения:</b> ETAS FPR=1000/1000 при seed=42; тектоника: 98% GC-фолбэк "
        "из 4987 пар (fig07_tectonic_path_usage.png).",
        s["body"]
    ))
    story.append(PageBreak())

    # === SECTION: ВЫВОДЫ =======================================================
    story += SEC("РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ (ВЫВОДЫ)", s)
    conclusions = [
        ("1.", "Каталог 4267\u00a0событий M\u22656.5 (4418\u00a0записей CSV) "
               "содержит 47\u00a0глобальных серий; 27\u00a0современных значимы "
               "при p=0.0001 (Monte Carlo, n=10\u202f000, 1/10\u202f001 permutations)."),
        ("2.", "ETAS-валидация (1000 кат.; FPR=1000/1000; калибр. null: mean=27,0, "
               "p_ETAS=1,0) и FDR (45/47\u00a0при q=0.05) — permutation test "
               "подтверждает структуру; калиброванный ETAS не отвергается."),
        ("3.", "Крупнейшая серия по числу событий\u00a0\u2014 1905\u20131910 (193\u00a0события, "
               "43\u00a0региона, M\u2098\u2090\u2093=8.8); наиболее масштабная современная\u00a0\u2014 "
               "S170 (46\u00a0событий, 12\u00a0регионов, M\u2098\u2090\u2093=9.1, "
               "2002\u20132023)."),
        ("4.", "Тектоника: 2.0% Dijkstra / 98.0% GC-фолбэк из 4987 пар "
               "(500 событий; analyze_tectonic_fallback.py); значима для ~2% пар у границ."),
        ("5.", "<b>Интерпретационная вилка:</b> (a)\u00a0если \u03b7-связи реальны \u2014 "
               "последствия для опасности (без утверждения прямого триггеринга); "
               "(b)\u00a0если артефакты \u2014 FDR+ETAS остаётся воспроизводимым null-test."),
    ]
    for num, text in conclusions:
        story.append(Paragraph(f"<b>{num}</b>\u00a0\u00a0{text}", s["enum"]))
        story.append(Spacer(1, 0.1 * cm))

    story.append(Paragraph(
        "<b>Доступность данных:</b> github.com/marshalkin-ux/paleoseismic-clustering "
        "(docs/data_availability.md). Внешний DOI (Zenodo) отложен \u2014 GitHub only. "
        "<b>Перспективы / дополнение:</b> статический \u0394CFS и динамический стресс "
        "для S170, S047, S095; полный ETAS MLE; multiseed.",
        s["body_ni"]
    ))

    # === REFERENCES ============================================================
    story += SEC("СПИСОК ЛИТЕРАТУРЫ", s)
    refs = [
        "1. Baiesi\u00a0M., Paczuski\u00a0M. Scale-free networks of earthquakes and aftershocks // Physical Review\u00a0E. 2004. Vol.\u00a069. P.\u00a0066106. DOI: 10.1103/PhysRevE.69.066106",
        "2. Zaliapin\u00a0I. et\u00a0al. Clustering analysis of seismicity and aftershock identification // Physical Review Letters. 2008. Vol.\u00a0101. P.\u00a0018501. DOI: 10.1103/PhysRevLett.101.018501",
        "3. Zaliapin\u00a0I., Ben-Zion\u00a0Y. Earthquake clusters in southern California\u00a0I // J.\u00a0Geophys.\u00a0Res. 2013. Vol.\u00a0118. P.\u00a02847\u20132864. DOI: 10.1002/jgrb.50179",
        "4. Bird\u00a0P. An updated digital model of plate boundaries // Geochem. Geophys. Geosyst. 2003. Vol.\u00a04. \u21963. P.\u00a01027. DOI: 10.1029/2001GC000252",
        "5. Hill\u00a0D.P. et\u00a0al. Seismicity remotely triggered by the magnitude 7.3 Landers earthquake // Science. 1993. Vol.\u00a0260. P.\u00a01617\u20131623. DOI: 10.1126/science.260.5114.1617",
        "6. Brodsky\u00a0E.E., Prejean\u00a0S.G. New constraints on mechanisms of remotely triggered seismicity at Long Valley Caldera // J.\u00a0Geophys.\u00a0Res. 2006. Vol.\u00a0111. P.\u00a0B06312. DOI: 10.1029/2005JB003869",
        "7. Pollitz\u00a0F.F. et\u00a0al. Viscosity of oceanic asthenosphere inferred from remote triggering of earthquakes // Science. 1998. Vol.\u00a0280. P.\u00a01245\u20131249. DOI: 10.1126/science.280.5367.1245",
        "8. Freed\u00a0A.M., Lin\u00a0J. Delayed triggering of the 1999 Hector Mine earthquake by viscoelastic stress transfer // Nature. 2001. Vol.\u00a0411. P.\u00a0180\u2013183. DOI: 10.1038/35075548",
        "9. Michael\u00a0A.J. Random variability explains apparent global clustering of large earthquakes // Geophys. Res. Lett. 2011. Vol.\u00a038. P.\u00a0L21301. DOI: 10.1029/2011GL049443",
        "10. Shearer\u00a0P.M., Stark\u00a0P.B. Global risk of big earthquakes has not recently increased // PNAS. 2012. Vol.\u00a0109. \u21963. P.\u00a0717\u2013721. DOI: 10.1073/pnas.1118525109",
        "11. Ogata\u00a0Y. Statistical models for earthquake occurrences and residual analysis // J.\u00a0Amer. Stat. Assoc. 1988. Vol.\u00a083. P.\u00a09\u201327. DOI: 10.1080/01621459.1988.10478560",
        "12. Gutenberg\u00a0B., Richter\u00a0C.F. Earthquake magnitude, intensity, energy, and acceleration // Bull. Seismol. Soc. Am. 1956. Vol.\u00a046. P.\u00a0105\u2013145",
        "13. Woessner\u00a0J., Wiemer\u00a0S. Assessing the quality of earthquake catalogues // Bull. Seismol. Soc. Am. 2005. Vol.\u00a095. P.\u00a0684\u2013698. DOI: 10.1785/0120040007",
        "14. Aki\u00a0K. Maximum likelihood estimate of b in log\u00a0N\u00a0=\u00a0a\u00a0\u2212\u00a0bM // Bull. Earthq. Res. Inst. 1965. Vol.\u00a043. P.\u00a0237\u2013239",
        "15. Shi\u00a0Y., Bolt\u00a0B.A. The standard error of the magnitude-frequency b value // Bull. Seismol. Soc. Am. 1982. Vol.\u00a072. P.\u00a01677\u20131687",
        "16. Gardner\u00a0J.K., Knopoff\u00a0L. Is the sequence of earthquakes in Southern California Poissonian? // Bull. Seismol. Soc. Am. 1974. Vol.\u00a064. P.\u00a01363\u20131367",
        "17. Benjamini\u00a0Y., Hochberg\u00a0Y. Controlling the false discovery rate // J.\u00a0Roy. Stat. Soc.\u00a0B. 1995. Vol.\u00a057. \u21961. P.\u00a0289\u2013300",
        "18. King\u00a0G.C.P. et\u00a0al. Static stress changes and the triggering of earthquakes // Bull. Seismol. Soc. Am. 1994. Vol.\u00a084. P.\u00a0935\u2013953",
        "19. Stein\u00a0R.S. The role of stress transfer in earthquake occurrence // Nature. 1999. Vol.\u00a0402. P.\u00a0605\u2013609",
        "20. Young\u00a0J.B. et\u00a0al. The Flinn\u2013Engdahl regionalization scheme: the 1995 revision // Phys. Earth Planet. Int. 1996. Vol.\u00a096. P.\u00a0223\u2013297. DOI: 10.1016/0031-9201(96)03141-X",
        "21. Storchak\u00a0D.A. et\u00a0al. Public release of the ISC-GEM Global Instrumental Earthquake Catalogue // Seismol. Res. Lett. 2013. Vol.\u00a084. P.\u00a0810\u2013815. DOI: 10.1785/0220130034",
        "22. Kagan\u00a0Y.Y. Fractal dimension of brittle fracture // J.\u00a0Nonlinear Sci. 1991. Vol.\u00a01. P.\u00a01\u201316. DOI: 10.1007/BF01209146",
    ]
    for r in refs:
        story.append(Paragraph(r, s["ref"]))

    story += SEC("ДРУГИЕ ИСТОЧНИКИ", s)
    sources = [
        "1. USGS Earthquake Hazards Program. ComCat\u00a0API. URL: https://earthquake.usgs.gov/fdsnws/event/1/ (дата обращения: 27.06.2026)",
        "2. NOAA National Geophysical Data Center. Significant Earthquake Database. URL: https://www.ngdc.noaa.gov/ (дата обращения: 27.06.2026)",
        "3. ISC. International Seismological Centre Bulletin. URL: http://www.isc.ac.uk/ (дата обращения: 27.06.2026)",
    ]
    for src in sources:
        story.append(Paragraph(src, s["ref"]))

    return story


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "paper")
    out_dir = os.path.normpath(out_dir)
    out_path = os.path.join(out_dir, "article_ru.pdf")

    styles = make_styles()

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=TM, bottomMargin=BM + 0.7 * cm,
        title="Глобальные сейсмические серии",
        author="Ярослав Маршалкин",
        subject="Статистический анализ кластеризации землетрясений M\u22656.5",
    )

    story = build(styles)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"\nPDF создан: {out_path}")
    print(f"Размер файла: {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
