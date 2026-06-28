"""
generate_article_pdf.py
Генерирует article_ru.pdf — научная статья по шаблону российского журнала.
Использует reportlab для Cyrillic-safe PDF без внешнего LaTeX.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pdf_fonts import (
    register_pdf_fonts,
    pdf_math_text,
    pdf_safe_text,
    build_pdf_table,
    build_top5_table,
)

register_pdf_fonts()
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus.flowables import Flowable


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
    def __init__(self, text, style, width=None, height=2.0 * cm):
        super().__init__()
        self.text = text
        self.style = style
        self.box_w = width or (PAGE_W - LM - RM)
        self.height = height

    def wrap(self, availWidth, availHeight):
        return self.box_w, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(LGREY)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1.2)
        c.roundRect(0, 0, self.box_w, self.height, 5, fill=1, stroke=1)
        para = Paragraph(pdf_math_text(self.text), self.style)
        pw, ph = para.wrap(self.box_w - 16, self.height)
        para.drawOn(c, (self.box_w - pw) / 2, (self.height - ph) / 2)


# ── Page template ─────────────────────────────────────────────────────────────
_FOOTER_STYLE = None


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(LM, BM - 0.5 * cm, PAGE_W - RM, BM - 0.5 * cm)
    footer = Paragraph(
        pdf_safe_text(
            f"Глобальные сейсмические серии  ·  Yaroslav Marshalkin  ·  {doc.page}"
        ),
        _FOOTER_STYLE,
    )
    fw, fh = footer.wrap(PAGE_W - LM - RM, 1.0 * cm)
    footer.drawOn(canvas, LM + (PAGE_W - LM - RM - fw) / 2, BM - 0.9 * cm - fh / 2)
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
    s["tbl_cell"] = ParagraphStyle("tbl_cell", fontName="Main", fontSize=8,
                                    textColor=TEXT, wordWrap="CJK", leading=11)
    s["tbl_wrap"] = ParagraphStyle("tbl_wrap", fontName="Main", fontSize=7,
                                    textColor=TEXT, wordWrap="CJK", leading=10)
    s["formula"] = ParagraphStyle("formula", fontName="MainBold", fontSize=13,
                                    textColor=DARK, alignment=TA_CENTER, leading=16)
    s["footer"] = ParagraphStyle("footer", fontName="Main", fontSize=8,
                                  textColor=MGREY, alignment=TA_CENTER, leading=10)
    return s


def P(text, style):
    """Paragraph with DejaVu-safe text (no Helvetica fallback beside Cyrillic)."""
    return Paragraph(pdf_safe_text(text), style)


def HR():
    return HRFlowable(width="100%", thickness=0.5, color=RULE,
                      spaceAfter=4, spaceBefore=4)


def SEC(text, s):
    return [HR(), P(text, s["section"])]


def SSEC(text, s):
    return [P(text, s["subsection"])]


def SSSEC(text, s):
    return [P(text, s["subsubsection"])]


# ── Story builder ─────────────────────────────────────────────────────────────
def build(s):
    story = []

    # === PAGE 1: Header ========================================================
    story.append(P(
        "Глобальные сейсмические серии: статистический анализ "
        "пространственно-временно\u0301й кластеризации землетрясений "
        "M\u22656.5 за 1973\u20132026\u00a0гг.",
        s["title_ru"]
    ))
    story.append(P("\u00a9 2026\u00a0г.\u00a0\u00a0Ярослав Маршалкин",
                            s["copyright"]))
    story.append(HR())
    story.append(Spacer(1, 0.2 * cm))

    # --- RU metadata ---
    story.append(P(
        "<b>Ярослав Маршалкин</b><br/>"
        "e-mail: marshalkin@gmail.com<br/>"
        "Telegram: @MRSHLKN &nbsp;|&nbsp; "
        "GitHub: github.com/marshalkin-ux/paleoseismic-clustering",
        s["meta"]
    ))
    story.append(Spacer(1, 0.3 * cm))

    story.append(P("<b>Аннотация.</b>", s["abstract_label"]))
    story.append(P(
        "В <b>анализ-каталоге 4267 уникальных M\u22656.5</b> (современное окно "
        "1973\u20132026: 2041); 47 записей NOAA \u2014 Приложение\u00a0A. Детектор "
        "(\u03b7, great-circle) выдаёт <b>27 кандидатов</b> в современном окне. "
        "<b>Калиброванная temporal ETAS</b> (GK mainshocks): mean=27,0, "
        "<b>p_ETAS=1,0</b>. "
        "<b>Мы не обнаружили аномалий временной кластеризации сверх калиброванной ETAS. "
        "Пространственная компонента не моделировалась, поэтому вопрос о физической "
        "связанности удалённых событий остаётся открытым для будущих исследований.</b>",
        s["abstract"]
    ))

    story.append(P(
        "<b>Ключевые слова:</b> глобальная сейсмичность; сейсмические серии; "
        "эвристическая метрика с тектонической подсказкой; кластеризация землетрясений; метрика Байеси\u2013Пачуски; "
        "Монте-Карло; Флинн\u2013Энгдал; палеосейсмология; статистический триггеринг; "
        "Gutenberg\u2013Richter",
        s["keywords"]
    ))

    story.append(P(
        "<b>Благодарность.</b> Авторы выражают признательность USGS, NOAA NGDC и ISC "
        "за поддержание открытых сейсмологических каталогов. "
        "Работа выполнена без целевого финансирования.",
        s["body_ni"]
    ))
    story.append(HR())
    story.append(Spacer(1, 0.3 * cm))

    # --- EN metadata ---
    story.append(P(
        "Global Seismic Series: Statistical Analysis of Spatiotemporal "
        "Clustering in M\u22656.5 Earthquake Catalogs, 1973\u20132026 CE",
        s["title_en"]
    ))
    story.append(P(
        "<b>Ярослав Маршалкин (Yaroslav Marshalkin)</b><br/>"
        "e-mail: marshalkin@gmail.com &nbsp;|&nbsp; Telegram: @MRSHLKN",
        s["meta"]
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(P("<b>Abstract.</b>", s["abstract_label"]))
    story.append(P(
        "We analyze <b>4,267 unique M\u22656.5 events</b> (modern window 1973\u20132026: "
        "2,041); NOAA pre-1900 records in Appendix\u00a0A. "
        "Baiesi\u2013Paczuski \u03b7 detector (great-circle) yields <b>27 candidates</b> "
        "in the modern window. <b>Catalog-calibrated temporal ETAS</b> (GK mainshocks): "
        "mean=27.0, <b>p_ETAS=1.0</b>. "
        "<b>We found no anomalous temporal clustering beyond catalog-calibrated ETAS. "
        "The spatial component was not modeled; the question of physical linkage among "
        "geographically remote events remains open for future work.</b>",
        s["abstract"]
    ))
    story.append(P(
        "<b>Keywords:</b> global seismicity; seismic series; earthquake clustering; "
        "heuristic metric with tectonic hint; Baiesi\u2013Paczuski metric; ETAS validation; Monte Carlo; "
        "Flinn\u2013Engdahl; paleoseismology; statistical triggering; Gutenberg\u2013Richter",
        s["keywords"]
    ))
    story.append(P(
        "<b>About the author:</b> Yaroslav Marshalkin \u2014 independent researcher. "
        "Contact: marshalkin@gmail.com, Telegram @MRSHLKN.",
        s["body_ni"]
    ))
    story.append(PageBreak())

    # === SECTION: Introduction =================================================
    story += SEC("1. Введение", s)
    story.append(P(
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
    story.append(P(
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
    story.append(P(
        "Тем не менее систематичность подобных связей оспаривается. Michael [2011] "
        "показал, что кластеризация M\u22657 в 1995\u20132011\u00a0гг. статистически "
        "неотличима от случайных флуктуаций. Shearer & Stark [2012] подтвердили, "
        "что глобальные частоты M\u22657 и M\u22658 не возросли после Суматры 2004. "
        "Дискуссию дополнили работы по дублетам [Kagan, Jackson, 1999]: "
        "повышенная вероятность второго события вблизи эпицентра первого "
        "подтверждает локальные корреляции, не исчерпывая дальнодействующих связей.",
        s["body"]
    ))
    story.append(P(
        "Модель ETAS [Ogata, 1988] откалибрована для региональных сетей и "
        "не описывает межплитные корреляции. Метрика Байеси\u2013Пачуски [2004] и "
        "её обобщение Зализяпина\u2013Бен-Зиона [2008, 2013] позволяют объективно "
        "выявлять кластеры, но используют евклидово расстояние, игнорируя "
        "плитно-тектоническую геометрию литосферы.",
        s["body"]
    ))
    story.append(P(
        "<b>Цель работы</b>\u00a0\u2014 проверить гипотезу о наличии мультирегиональных серий "
        "в инструментальном каталоге 1973\u20132026\u00a0гг. с применением адаптированной "
        "метрики eta с тектоническим расстоянием вдоль границ плит Bird (2003). "
        "<b>Охват</b>: кластеризация с тектоническим расстоянием и ETAS; "
        "дополняет тесты частот Michael (2011) и Shearer &amp; Stark (2012), "
        "не отменяя их выводы.",
        s["body"]
    ))
    story.append(P(
        "<b>§1.1 Исследовательский вопрос.</b> Существуют ли физически значимые "
        "мультирегиональные глобальные серии в каталоге M\u22656.5 (1973\u20132026)? "
        "(a) Permutation: H\u2080 независимые времена \u2192 p=0,0001 (не тест глобальных серий). "
        "(b) ETAS MLE: mean=27,0, p_ETAS=1,0 \u2014 N_obs согласован с null. "
        "(c) Гипотеза глобальных серий: <b>не тестируется</b> temporal-only ETAS; spatial null открыт. "
        "(d) WLS-контроль (Прил.\u00a0B): p=1,0 \u2014 coupling illustration, не первичная null.",
        s["body_ni"]
    ))

    # === SECTION: Methods =======================================================
    story += SEC("2. Методы", s)

    # --- 1. Данные ---
    story += SSEC("1. Данные", s)
    story += SSSEC("1.1 Источники и формирование каталога", s)
    story.append(P(
        "<b>Обозначение магнитуды.</b> Пороги каталога и критерии детектора \u2014 "
        "<b>M\u22656.5</b> (USGS ComCat, преимущественно M<sub>w</sub>); отдельные события "
        "цитируются с типом из каталога (напр. M<sub>w</sub> 7.3).",
        s["body_ni"]
    ))
    story.append(P(
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
        "<b>Основной набор анализа:</b> события 1900\u20132026 (4218); "
        "47\u00a0записей до 1900\u00a0г. остаются в CSV (провенанс), но "
        "исключены из первичного конвейера детектора и окна калибровки ETAS "
        "(1973\u20132026) \u2014 см. Приложение\u00a0A. "
        "Итоговый каталог: <b>4267</b> событий M\u22656.5 (<b>4418</b> записей CSV); "
        "2041\u00a0\u2014 современный (1973\u20132026), "
        "2179\u00a0\u2014 ранний (1900\u20131972), "
        "47\u00a0\u2014 исторический (фрагментарные палеосейсмические записи).",
        s["body"]
    ))
    story += SSSEC("1.2 Анализ полноты каталога", s)
    story.append(P(
        "Метод максимальной кривизны даёт M\u2090=6.55. Оценка b-значения методом "
        "максимального правдоподобия по 1688 событиям выше M\u2090:",
        s["body"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(FormulaBox(
        "b = 0.911 \u00b1 0.018  (n = 1688 \u0441\u043e\u0431\u044b\u0442\u0438\u0439)",
        s["formula"],
        PAGE_W - LM - RM,
    ))
    story.append(Spacer(1, 0.15 * cm))

    # --- 2. Методология ---
    story += SSEC("2. Методология", s)
    story += SSSEC("2.1 Эвристическая метрика с тектонической подсказкой", s)
    story.append(P(
        "Эвристика Bird (2003) — <b>исключена из первичного анализа</b> (только приложение); "
        "первичный анализ использует <b>только great-circle</b>. Провал валидации "
        "показывает непригодность метрики, <b>не</b> доказательство против глобальных серий.",
        s["body"]
    ))
    story += SSSEC("2.2 Метрика связности eta", s)
    story.append(P(
        "Вслед за Baiesi & Paczuski [2004] и Zaliapin et al. [2008] определим "
        "метрику связности между претендентом-родителем i и последующим событием j:",
        s["body"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(FormulaBox(
        "eta_ij  =  t_ij  *  r_ij^1.6  *  10^(-b*mi)",
        s["formula"],
        PAGE_W - LM - RM,
    ))
    story.append(P(
        "b=1.0 — намеренное упрощение Baiesi &amp; Paczuski (2004); каталожное b=0.911±0.018 — "
        "только Mc/полнота и MC-null, <b>не</b> в формуле η. Совпадение N=27 <b>не доказывает</b> "
        "идентичность кандидатов (Jaccard=1,0; global_series не использует b); upstream-кластеры "
        "при b=0,911 <b>не пересчитаны</b> (~9,8% смена меток).",
        s["caption"]
    ))
    story.append(Spacer(1, 0.1 * cm))
    comp_rows = [
        ["Компонент", "Обозначение", "Физический смысл"],
        ["Время", "t<sub>ij</sub> (лет)", "Штраф за большой временной разрыв"],
        ["Расстояние", "r<sub>ij</sub><sup>1.6</sup> (км)", "Штраф за большое расстояние (эвристика)"],
        ["Магнитуда", "10<sup>(-b*m<sub>i</sub>)</sup>", "Усиление связи при большой магнитуде родителя"],
    ]
    story.append(build_pdf_table(comp_rows, [0.18, 0.22, 0.60], PAGE_W - LM - RM, s, wrap_col=2))
    story.append(Spacer(1, 0.2 * cm))

    story += SSSEC("2.3 Конвейер анализа", s)
    story.append(P(
        "Сырые каталоги \u2192 дедупликация \u2192 исключить M&lt;6.5 (~151 NOAA) "
        "\u2192 GK-декластеризация (основной) \u2192 eta NN-лес "
        "\u2192 скользящие окна \u2192 объединение перекрывающихся \u2192 критерии серии "
        "\u2192 MC/ETAS/FDR. GK: 24 афтершока (2017/2041, 98.8%). "
        "ZBZ: 1 зависимое (2040/2041) \u2014 разные алгоритмы (GK: окна T(M)/R(M); "
        "ZBZ: \u03b7 NN + KDE-порог); при глобальном M\u22656.5 ZBZ либерален. "
        "GK \u2014 единственный основной метод; ZBZ не заменяет GK. "
        "ZBZ-primary для N=27 не тестировался (вероятно незначительно). "
        "run_full_historical_analysis.py: global_series() без GK-префильтра.",
        s["body"]
    ))
    story.append(P(
        "<b>Почему GK\u2013ZBZ различаются:</b> не противоречие \u2014 GK удаляет "
        "локальные фор/афтершоки в окнах; ZBZ помечает 1 событие с аномально низким \u03b7. "
        "Минимальное удаление ZBZ не доказывает декластеризацию несущественной: "
        "при фиксированных воротах GK/ZBZ/none дают N=27 (sensitivity_declustering.json), "
        "но алгоритмы назначают разные метки главных толчков (24 vs 1).",
        s["body"]
    ))
    story += SSSEC("2.3.1 Спецификация алгоритмов", s)
    story.append(P(
        "GK: WINDOWS, интерполяция T(M)/R(M), убывание M; афтершоки [0,T], форшоки "
        "[\u2212T/2,0); гаверсинус. find_nearest_neighbor: argmin \u03b7, b=1.0, GC\u00a0км. "
        "identify_clusters: Union\u2013Find, \u03b7\u2080 KDE. global_series: used[], "
        "окно [t<sub>i</sub>, t<sub>i</sub>+\u0394t), mean GC&gt;1500\u00a0км; merge 142\u219247.",
        s["body"]
    ))

    story += SSSEC("2.4 Критерии кластеризации и детектора", s)
    for num, text in [
        ("1.", "GK-декластеризация (основной) \u2192 главные толчки для \u03b7 NN-леса."),
        ("2.", "\u03b7 NN-лес: b=1.0, r<sup>1.6</sup>; тектоника Bird 2003 (фолбэк 1.5\u00d7GC)."),
        ("3.", "Скользящие окна 1, 2, 5\u00a0лет (шаг 1\u00a0год); merge 142\u219247."),
        ("4.", "<b>Ворота детектора:</b> N\u22654; M\u22656.5; mean pairwise GC&gt;1500\u00a0km."),
        ("5.", "Число зон FE \u2014 только диагностика (не критерий допуска)."),
    ]:
        story.append(P(f"<b>{num}</b>\u00a0\u00a0{text}", s["enum"]))

    story += SSSEC("2.5 Порог η₀ и ETAS-null", s)
    story.append(P(
        "Порог η₀: KDE-долина log₁₀(η) (Zaliapin &amp; Ben-Zion 2013). "
        "<b>Первичная ETAS-null</b> — temporal MLE на GK mainshocks "
        "(calibrate_etas_mle.py). WLS — Приложение B (negative control).",
        s["body"]
    ))
    story += SSSEC("2.6 Статистическая валидация", s)
    story.append(P(
        "<b>Заявление (permutation):</b> p=0,0001 отвергает <b>только</b> пуассоновские "
        "времена (Ogata, 1988); не подтверждает глобальные серии.",
        s["body_ni"]
    ))
    story.append(P(
        "<b>Тест Монте-Карло.</b> n=10\u202f000 перестановок: "
        "p=0.0001 (1/10,001), z=\u22126.17 для современного периода. "
        "<b>ETAS (первичная MLE).</b> mean=27,0, p_ETAS=1,0, N_obs=27. "
        "Интерпретация \u2014 §4. GK mainshocks: N=27. BH post-hoc N=47 \u2014 не discovery.",
        s["body"]
    ))

    # --- 3. Results ---
    story += SEC("3. Результаты", s)
    story += SSEC("3.1 Кандидаты детектора", s)
    story.append(P(
        "Полный анализ выдаёт <b>47 кандидатов детектора</b> (не «открытые серии»): 27\u00a0современных "
        "(p=0.0001, 1/10,001), 15\u00a0ранних (p=0.007, но quality_score&lt;0.7 до 1960\u00a0г. "
        "ограничивает интерпретацию), 5\u00a0исторических кандидатов "
        "(<b>статистически не значимы</b>, p=0.46; только 47\u00a0событий M\u22656.5 "
        "до 1900\u00a0г., фрагментарные палеосейсмические записи). "
        "142 кластера-кандидата до фильтрации. Топ-5 серий \u2014 в таблице ниже. "
        "<i>Интерпретация permutation/ETAS \u2014 §4.</i>",
        s["body"]
    ))

    story.append(build_top5_table(s, PAGE_W - LM - RM, lang="ru"))
    story.append(P(
        "Таблица 1. Сырые кандидаты детектора — НЕ валидированные серии; только иллюстрация.",
        s["caption"]
    ))
    story.append(Spacer(1, 0.2 * cm))

    story += SSSEC("3.2 Статистическая значимость", s)
    story.append(P(
        "Перестановочный тест (n\u209b\u1d62\u2098=10\u202f000):",
        s["body"]
    ))
    story.append(FormulaBox(
        "p \u2264 0.0001   (z = \u22126.17,  \u0441\u043e\u0432\u0440\u0435\u043c\u0435\u043d\u043d\u044b\u0439 \u043f\u0435\u0440\u0438\u043e\u0434 1973\u20132026)",
        s["formula"],
        PAGE_W - LM - RM,
    ))
    story.append(FormulaBox(
        "primary MLE ETAS: mean 27,0, p_ETAS = 1,0   (N_obs=27)",
        s["formula"],
        PAGE_W - LM - RM,
    ))
    story.append(P(
        "Коррекция BH (q=0.05) на N=47 — post-hoc, не discovery. "
        "Permutation p=0,0001 отвергает пуассоновские времена. "
        "Primary ETAS MLE: mean=27,0, p_ETAS=1,0.",
        s["body_ni"]
    ))

    story += SSSEC("3.3 Пространственно-временно\u0301е распределение", s)
    story.append(P(
        "Повышенная частота кандидатов детектора (не валидированные физические серии): "
        "1952\u20131965\u00a0гг. и 2002\u20132016\u00a0гг. "
        "(пост-суматранский период). Пространственно\u00a0\u2014 вдоль "
        "циркум-тихоокеанского пояса (Камчатка, Курилы, Япония, Тонга, Индонезия). "
        "Диагностика тектоники vs евклидовой метрики: медиана \u0394log\u2081\u2080\u03b7 = +0.28 "
        "на случайных парах (в основном GC-фолбэк 1.5\u00d7).",
        s["body"]
    ))

    story += SSSEC("3.4 Сводная таблица чувствительности (современное окно)", s)
    sens_w = PAGE_W - LM - RM
    sens_rows = [
        ["Параметр", "Значение", "N_series"],
        ["GC-порог", "1000\u00a0км", "27"],
        ["GC-порог", "1500\u00a0км (базовый)", "27"],
        ["GC-порог", "2000\u00a0км", "27"],
        ["Окно", "1\u00a0год", "53"],
        ["Окно", "2\u00a0года (базовое)", "27"],
        ["Окно", "5\u00a0лет", "11"],
        ["Окно", "10\u00a0лет", "6"],
        ["b в \u03b7", "1.0 (BP 2004)", "27"],
        ["b в \u03b7", "0.911 (каталог)", "27"],
        ["b overlap (наборы серий)", "Jaccard=1,0; upstream ~9,8%", "27"],
        ["Декластеризация", "GK / ZBZ / none", "27 / 27 / 27"],
        ["min_events (strict)", "5 / 6 / 8", "27 / 27 / 27"],
        ["Каталог", "только GK-главные", "27"],
        ["\u03b7\u2080 \u00b120%", "not_applied", "\u2014"],
    ]
    story.append(build_pdf_table(sens_rows, [0.30, 0.52, 0.18], sens_w, s))
    story.append(P(
        "Таблица 2. Чувствительность N_series при фиксированных воротах детектора "
        "(mean GC&gt;1500\u00a0км, N\u22654). Источники: sensitivity_*.json.",
        s["caption"]
    ))
    story.append(Spacer(1, 0.2 * cm))

    story += SEC("4. Обсуждение и выводы", s)
    story.append(P(
        "<b>Temporal ETAS (primary):</b> нет аномалий временной кластеризации сверх null "
        "(§3.1: N_obs=27, mean=27,0, p_ETAS=1,0). Spatial linkage не тестировалась. "
        "Permutation — только пуассоновские времена. Детектор либерален (142 окна). "
        "Bird/WLS — supplementary only.",
        s["body"]
    ))
    story.append(PageBreak())

    # === APPENDICES ==============================================================
    story.append(P(
        "<b>Использована только temporal ETAS; пространственный компонент не моделировался; "
        "выводы строго ограничены временной кластеризацией.</b> "
        "Отверждение «глобальных серий» как протестированной null потребовало бы spatial ETAS; "
        "мы <b>не</b> заявляем такого отвержения здесь.",
        s["body"]
    ))
    lim_rows = [
        ["Ограничение", "Затронутый шаг", "Влияние на главный вывод"],
        [
            "\u03b7\u2080 не верифицирована глобально",
            "GK/ZBZ identify_clusters",
            "KDE-долина \u22487,1\u00d710\u207b\u2076; global_series без \u03b7\u2080 \u2192 N=27; "
            "ошибка \u03b7\u2080 сместит только GK/ZBZ-метки",
        ],
        [
            "b=1.0 vs 0.911",
            "\u03b7 upstream",
            "N_series=27 оба; метки кластеров не пересчитаны",
        ],
        [
            "Нет spatial Ogata MLE",
            "ETAS-null",
            "Temporal MLE primary; spatial MLE future work",
        ],
        [
            "142 окна + merge",
            "Детектор",
            "Главный источник либеральности",
        ],
        [
            "Calibrated p_ETAS=1,0",
            "ETAS-тест",
            "Согласован с null; поддерживает отрицательный вывод",
        ],
    ]
    story.append(build_pdf_table(lim_rows, [0.24, 0.22, 0.54], sens_w, s, wrap_col=2))
    story.append(P(
        "Таблица 3. Ограничение \u2192 затронутый шаг \u2192 влияние на главный вывод (§5.6).",
        s["caption"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(P(
        "<b>Анализ влияния.</b> N=27 считается через global_series() без фильтра \u03b7\u2080; "
        "b=1,0 vs 0,911 при фиксированных воротах \u2192 N=27 в обоих случаях, но upstream-кластеры "
        "при b=0,911 не пересчитаны. 142 скользящих окна \u2014 главный источник либеральности.",
        s["body_ni"]
    ))

    story += SEC("ПРИЛОЖЕНИЕ A. ЗАПИСИ NOAA ДО 1900 Г.", s)
    story.append(P(
        "47 фрагментарных палеосейсмических/исторических записей M\u22656.5 из NOAA NGDC "
        "сохранены в data/processed/unified_catalog_full.csv для провенанса (не удалялись). "
        "Эти 47 событий <b>исключены из первичного конвейера детектора и окна калибровки ETAS</b>: "
        "pipeline_v2.py и calibrate_etas.py используют только современный каталог 1973\u20132026 "
        "(N=2041). Эпохальные подсчёты включают до 1900\u00a0г. описательно через "
        "run_full_historical_analysis.py, но не входят в первичные заявления о значимости.",
        s["body"]
    ))

    story += SEC("ПРИЛОЖЕНИЕ B. НЕГАТИВНЫЙ КОНТРОЛЬ WLS (ВОСПРОИЗВОДИМОСТЬ)", s)
    story.append(P(
        "<b>\u0422\u043e\u043b\u044c\u043a\u043e \u0432\u043e\u0441\u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0438\u043c\u043e\u0441\u0442\u044c \u2014 \u043d\u0435 inference.</b> "
        "Каталог-калиброванная WLS (results/etas_calibration.json: "
        "\u03bc\u22480,103, K\u22480,495) даёт mean=27,0, p_ETAS=1,0 "
        "(n=1000, multiseed стабилен). <b>Артефакт связки детектор+калибровка</b> "
        "на 24 GK-афтершоках; <b>не</b> для выводов. "
        "Иллюстрирует coupling детектора и калибровки; <b>не</b> первичная null.",
        s["body"]
    ))
    wls_rows = [
        ["\u041a\u043e\u043c\u043f\u043e\u043d\u0435\u043d\u0442", "\u041c\u0435\u0442\u043e\u0434"],
        ["\u03bc (\u043c\u044e)", "GK mainshocks / T (\u0437\u0430\u043c\u043a\u043d\u0443\u0442\u0430\u044f \u0444\u043e\u0440\u043c\u0430)"],
        ["c, p", "Omori MLE, Nelder\u2013Mead \u043d\u0430 24 \u0437\u0430\u0434\u0435\u0440\u0436\u043a\u0430\u0445"],
        ["K, \u03b1", "WLS (numpy.linalg.lstsq) \u043d\u0430 \u0442\u0435\u0445 \u0436\u0435 24 GK-\u0430\u0444\u0442\u0435\u0440\u0448\u043e\u043a\u0430\u0445"],
    ]
    story.append(build_pdf_table(wls_rows, [0.22, 0.78], PAGE_W - LM - RM, s))
    story.append(Spacer(1, 0.15 * cm))

    story.append(P(
        "<b>Доступность данных:</b> github.com/marshalkin-ux/paleoseismic-clustering "
        "(docs/data_availability.md). Внешний DOI (Zenodo) отложен \u2014 GitHub only. "
        "<b>Перспективы / дополнение:</b> статический \u0394CFS и динамический стресс "
        "для S170, S047, S095; полный ETAS MLE; ZBZ-primary re-run.",
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
        story.append(P(r, s["ref"]))

    story += SEC("ДРУГИЕ ИСТОЧНИКИ", s)
    sources = [
        "1. USGS Earthquake Hazards Program. ComCat\u00a0API. URL: https://earthquake.usgs.gov/fdsnws/event/1/ (дата обращения: 27.06.2026)",
        "2. NOAA National Geophysical Data Center. Significant Earthquake Database. URL: https://www.ngdc.noaa.gov/ (дата обращения: 27.06.2026)",
        "3. ISC. International Seismological Centre Bulletin. URL: http://www.isc.ac.uk/ (дата обращения: 27.06.2026)",
    ]
    for src in sources:
        story.append(P(src, s["ref"]))

    return story


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global _FOOTER_STYLE
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "paper")
    out_dir = os.path.normpath(out_dir)
    out_path = os.path.join(out_dir, "article_ru.pdf")

    styles = make_styles()
    _FOOTER_STYLE = styles["footer"]

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
