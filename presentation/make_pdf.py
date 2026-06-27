"""Generate overview.pdf — scientific overview of the paleoseismic-clustering project."""

import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable

# ── TTF font registration (Cyrillic support) ────────────────────────────────
_FONT_DIR = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont("MainFont",        os.path.join(_FONT_DIR, "arial.ttf")))
pdfmetrics.registerFont(TTFont("MainFont-Bold",   os.path.join(_FONT_DIR, "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("MainFont-Italic", os.path.join(_FONT_DIR, "ariali.ttf")))


# ── Unicode → ASCII safety filter (Arial TTF lacks many specialty glyphs) ────
def safe_text(s: str) -> str:
    """Replace chars unsupported by Arial with ASCII equivalents."""
    _subs = {
        '\u1d46': 'w',  '\u1d62': 'i',  '\u2c7c': 'j',   # modifier/subscript letters
        '\u2090': 'a',  '\u209c': 't',  '\u2098': 'm',
        '\u2093': 'x',  '\u2091': 'e',  '\u2099': 'n',
        '\u2080': '0',  '\u2081': '1',  '\u2082': '2',    # subscript digits
        '\u2083': '3',  '\u2084': '4',  '\u2085': '5',
        '\u2086': '6',  '\u2087': '7',  '\u2088': '8',  '\u2089': '9',
        '\u0305': '',                                       # combining overline → drop
        '\u2047': '?',  '\u202f': '\u00a0',                # ⁇ / narrow NBSP
        '\u2605': '***', '\u2606': '*',                    # ★ ☆
        '\u2713': 'OK',  '\u2717': 'X',                   # ✓ ✗
        '\u2212': '-',                                     # minus sign
    }
    for ch, rep in _subs.items():
        s = s.replace(ch, rep)
    return s


# Wrap Paragraph so every instance auto-applies safe_text
_BaseParagraph = Paragraph


class Paragraph(_BaseParagraph):  # type: ignore[misc]
    def __init__(self, text, style, *args, **kwargs):
        if isinstance(text, str):
            text = safe_text(text)
        super().__init__(text, style, *args, **kwargs)


# ── Colour palette ──────────────────────────────────────────────────────────
DARK_BLUE  = HexColor("#1e3a5f")
ACCENT     = HexColor("#2563eb")
TEXT       = HexColor("#1a1a1a")
LIGHT_GREY = HexColor("#f0f2f5")
MID_GREY   = HexColor("#9ca3af")
RULE_GREY  = HexColor("#cbd5e1")

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


# ── Custom flowable: formula box ─────────────────────────────────────────────
class FormulaBox(Flowable):
    def __init__(self, formula_text, width=None):
        super().__init__()
        self.formula_text = formula_text
        self.box_width = width or (PAGE_W - 2 * MARGIN)
        self.height = 2.2 * cm

    def draw(self):
        self.canv.setFillColor(LIGHT_GREY)
        self.canv.setStrokeColor(ACCENT)
        self.canv.setLineWidth(1.5)
        self.canv.roundRect(0, 0, self.box_width, self.height, 6, fill=1, stroke=1)
        self.canv.setFillColor(DARK_BLUE)
        self.canv.setFont("MainFont-Bold", 16)
        self.canv.drawCentredString(
            self.box_width / 2,
            self.height / 2 - 6,
            safe_text(self.formula_text)
        )


# ── Page template (numbers + header rule) ────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE_GREY)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 1.3 * cm, PAGE_W - MARGIN, 1.3 * cm)
    canvas.setFont("MainFont", 8)
    canvas.setFillColor(MID_GREY)
    canvas.drawCentredString(
        PAGE_W / 2, 0.8 * cm,
        safe_text(f"Глобальные сейсмические серии  \u00b7  Июнь 2026  \u00b7  {doc.page}")
    )
    canvas.restoreState()


# ── Style helpers ─────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["title_main"] = ParagraphStyle(
        "title_main",
        fontName="MainFont-Bold",
        fontSize=28,
        textColor=DARK_BLUE,
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=34,
    )
    styles["title_sub"] = ParagraphStyle(
        "title_sub",
        fontName="MainFont",
        fontSize=14,
        textColor=ACCENT,
        alignment=TA_CENTER,
        spaceAfter=6,
        leading=20,
    )
    styles["meta"] = ParagraphStyle(
        "meta",
        fontName="MainFont",
        fontSize=10,
        textColor=MID_GREY,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles["section"] = ParagraphStyle(
        "section",
        fontName="MainFont-Bold",
        fontSize=14,
        textColor=DARK_BLUE,
        spaceBefore=14,
        spaceAfter=6,
    )
    styles["body"] = ParagraphStyle(
        "body",
        fontName="MainFont",
        fontSize=10,
        textColor=TEXT,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leading=15,
    )
    styles["body_center"] = ParagraphStyle(
        "body_center",
        fontName="MainFont",
        fontSize=10,
        textColor=TEXT,
        alignment=TA_CENTER,
        spaceAfter=6,
        leading=15,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet",
        fontName="MainFont",
        fontSize=10,
        textColor=TEXT,
        leftIndent=16,
        spaceAfter=4,
        leading=15,
        bulletIndent=4,
    )
    styles["formula_caption"] = ParagraphStyle(
        "formula_caption",
        fontName="MainFont",
        fontSize=9,
        textColor=MID_GREY,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles["step"] = ParagraphStyle(
        "step",
        fontName="MainFont",
        fontSize=10,
        textColor=TEXT,
        leftIndent=20,
        spaceAfter=5,
        leading=15,
    )
    styles["ref"] = ParagraphStyle(
        "ref",
        fontName="MainFont",
        fontSize=9,
        textColor=TEXT,
        leftIndent=14,
        spaceAfter=4,
        leading=13,
    )
    return styles


def hr():
    return HRFlowable(width="100%", thickness=0.5, color=RULE_GREY, spaceAfter=6, spaceBefore=4)


def section(text, styles):
    return [hr(), Paragraph(text, styles["section"])]


# ── Build story ───────────────────────────────────────────────────────────────
def build_story(styles):
    S = styles
    story = []

    # ── PAGE 1: Title ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("Глобальные сейсмические серии", S["title_main"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "Поиск скрытых паттернов в палеосейсмологических<br/>и инструментальных данных",
        S["title_sub"]
    ))
    story.append(Spacer(1, 1.5 * cm))

    # metadata table
    meta_data = [[
        Paragraph("Период", S["meta"]),
        Paragraph("Порог", S["meta"]),
        Paragraph("Дата", S["meta"]),
    ], [
        Paragraph("<b>2150 BCE — 2026 CE</b>", S["body_center"]),
        Paragraph("<b>M ≥ 6.5</b>", S["body_center"]),
        Paragraph("<b>Июнь 2026</b>", S["body_center"]),
    ]]
    meta_table = Table(meta_data, colWidths=[(PAGE_W - 2 * MARGIN) / 3] * 3)
    meta_table.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 0.5, RULE_GREY),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, RULE_GREY),
        ("BACKGROUND", (0, 0), (-1, 0),  LIGHT_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(PageBreak())

    # ── PAGE 2: Problem & Motivation ──────────────────────────────────────────
    story += section("1. Проблема и мотивация", S)
    story.append(Paragraph(
        "Землетрясения не являются независимыми случайными событиями — они образуют "
        "пространственно-временны́е кластеры, связанные передачей напряжений в литосфере. "
        "<b>Hill et al. (1993)</b> впервые задокументировали динамический тригеринг на "
        "расстояниях свыше 1000 км после землетрясения Ланделс-Хиллс (M7.3). "
        "<b>Brodsky &amp; Prejean (2005)</b> показали, что поверхностные сейсмические волны "
        "могут запускать роевую активность в вулканических зонах на расстоянии тысяч километров.",
        S["body"]
    ))
    story.append(Paragraph(
        "Три исторических примера поднимают ключевой вопрос:",
        S["body"]
    ))
    examples = [
        "• <b>1960 Чили M9.5 + 1964 Аляска M9.2</b> — два крупнейших зафиксированных "
        "землетрясения разделены ~3.5 годами и ~8000 км вдоль субдукционного пояса "
        "Тихого океана.",
        "• <b>2004 Суматра M9.1</b> спровоцировала серию событий M8+ (Симёлуэ 2005, "
        "Яванская дуга 2006, Бенгкулу 2007) — беспрецедентная региональная активация "
        "за трёхлетний период.",
        "• <b>Турция 2023 (Kahramanmaraş M7.8+7.7) + Япония 2024 (Нотo M7.5)</b> — "
        "воспринятые публикой как «эхо» нарастания глобальной активности.",
    ]
    for e in examples:
        story.append(Paragraph(e, S["bullet"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Нерешённый вопрос: является ли пространственно-временна́я группировка "
        "крупных землетрясений (M≥6.5) случайной флуктуацией пуассоновского процесса "
        "или свидетельством систематических геодинамических связей на масштабах, "
        "превосходящих традиционно изучаемые афтершоковые зоны? Настоящий проект "
        "разрабатывает количественный инструментарий для ответа на этот вопрос.",
        S["body"]
    ))
    story.append(PageBreak())

    # ── PAGE 3: Data ───────────────────────────────────────────────────────────
    story += section("2. Данные", S)
    story.append(Paragraph(
        "Проект интегрирует три независимых каталога, перекрывающих различные "
        "временны́е диапазоны и обеспечивающих взаимную верификацию.",
        S["body"]
    ))
    col_w = [(PAGE_W - 2 * MARGIN) * f for f in [0.28, 0.26, 0.46]]
    tbl_data = [
        [
            Paragraph("<b>Источник</b>", S["body"]),
            Paragraph("<b>Период</b>", S["body"]),
            Paragraph("<b>Охват</b>", S["body"]),
        ],
        [
            Paragraph("USGS ComCat API", S["body"]),
            Paragraph("1900–2026", S["body"]),
            Paragraph("~80 000 событий M≥6.5", S["body"]),
        ],
        [
            Paragraph("ISC Bulletin", S["body"]),
            Paragraph("1900–2023", S["body"]),
            Paragraph("~75 000 событий", S["body"]),
        ],
        [
            Paragraph("NOAA NGDC", S["body"]),
            Paragraph("2150 BCE–2026", S["body"]),
            Paragraph("~6 000 значимых событий", S["body"]),
        ],
    ]
    tbl = Table(tbl_data, colWidths=col_w)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("TEXTCOLOR",  (0, 0), (-1, 0), white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_GREY]),
        ("BOX",       (0, 0), (-1, -1), 0.5, RULE_GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, RULE_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "<b>Проблема полноты каталога.</b> До 1960-х гг. сейсмографическая сеть "
        "была редкой, что приводит к систематическому занижению числа событий. "
        "Для каждого события рассчитывается <b>quality_score</b> (0.30–0.95) "
        "на основе эпохи записи, числа фазовых считываний и степени пересечения "
        "трёх каталогов. Анализ ограничивается временными окнами, в которых "
        "quality_score > 0.5 для не менее 90% событий выборки.",
        S["body"]
    ))
    story.append(PageBreak())

    # ── PAGE 4: Tectonic distance ──────────────────────────────────────────────
    story += section("3. Эвристическая метрика с тектонической подсказкой", S)
    story.append(Paragraph(
        "Протестирована альтернатива евклидовому расстоянию (граф Bird 2003). "
        "В 98% пар реализация сводится к 1,5× дуге большого круга — по сути масштабированное "
        "евклидово; улучшения для глобального анализа нет (отрицательный тест гипотезы).",
        S["body"]
    ))
    bullet_points = [
        "• <b>Bird (2003)</b> — глобальная модель границ тектонических плит: "
        "20 ключевых сегментов (субдукционные зоны, трансформные разломы, "
        "рифты срединно-океанических хребтов).",
        "• Граница плит кодируется как граф <b>NetworkX</b>: узлы — точки "
        "трассировки, рёбра — отрезки с весом = геодезическое расстояние.",
        "• Для ~2% пар у границ плит алгоритм <b>Дейкстры</b> находит кратчайший "
        "путь → r_ij с тектонической подсказкой; для 98% — фолбэк 1,5× GC.",
        "• <b>Пример:</b> два события M7+ по разные стороны Тихого океана "
        "(Япония и Перу) имеют евклидово расстояние ~14 000 км, но тектоническое "
        "расстояние вдоль Тихоокеанского огненного кольца — ~18 500 км, "
        "корректно отражая геодинамическую связность.",
        "• Гибридная метрика: r_ij = 0.6·r_tect + 0.4·r_eucl при r_tect < 5000 км; "
        "иначе r_ij = r_eucl (разные плитные системы считаются слабо связными).",
    ]
    for bp in bullet_points:
        story.append(Paragraph(bp, S["bullet"]))
    story.append(PageBreak())

    # ── PAGE 5: η metric ───────────────────────────────────────────────────────
    story += section("4. Метрика η — мера связности событий", S)
    story.append(Spacer(1, 0.3 * cm))
    story.append(FormulaBox("  η_ij  =  t_ij · r_ij^1.6 · 10^(−m_i)  ",
                            PAGE_W - 2 * MARGIN))
    story.append(Spacer(1, 0.4 * cm))
    defs = [
        ("t_ij", "временной интервал между событиями i и j (в годах)"),
        ("r_ij", "тектоническое расстояние (км), см. раздел 3"),
        ("m_i",  "магнитуда потенциального «родительского» события i"),
    ]
    for sym, desc in defs:
        story.append(Paragraph(
            f"<b>{sym}</b> — {desc}",
            S["bullet"]
        ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "<b>Интерпретация:</b> малое значение η указывает на сильную "
        "пространственно-временну́ю и магнитудную связь (потенциальный тригеринг); "
        "большое η соответствует независимым событиям. Формула адаптирована из "
        "<b>Baiesi &amp; Paczuski (2004)</b> — оригинальная метрика использовала "
        "евклидово расстояние; здесь евклидов член заменён тектоническим, что "
        "повышает чувствительность к субдукционным и трансформным коридорам.",
        S["body"]
    ))
    story.append(Paragraph(
        "Показатель степени 1.6 при r_ij получен эмпирически на основе работ "
        "Zaliapin &amp; Ben-Zion (2013): он соответствует фрактальной размерности "
        "распределения гипоцентров вдоль активных систем разломов.",
        S["body"]
    ))
    story.append(PageBreak())

    # ── PAGE 6: Algorithm ──────────────────────────────────────────────────────
    story += section("5. Алгоритм поиска серий", S)
    steps = [
        ("1.", "Для каждого события j находим родителя i* = argmin η_ij "
               "по всем предшествующим событиям (t_i < t_j). "
               "Связь устанавливается только если η_ij < η_threshold."),
        ("2.", "Построение леса направленных связей: каждый узел имеет "
               "не более одного родителя; корни деревьев — независимые события."),
        ("3.", "Агрегирование по скользящим временны́м окнам: "
               "1 день, 7 дней, 30 дней, 1 год, 10 лет."),
        ("4.", "Критерий глобальной серии: N ≥ 4 события, M ≥ 6.5, "
               "охват ≥ 3 различных зон Флинна–Энгдала (глобальная регионализация)."),
        ("5.", "Monte Carlo валидация: 10 000 перестановок временны́х меток "
               "при сохранении координат; расчёт p-value для каждой "
               "обнаруженной серии. Принимаем серию значимой при p < 0.01."),
    ]
    for num, text in steps:
        story.append(Paragraph(
            f"<b>{num}</b>  {text}",
            S["step"]
        ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "<b>Управление порогом η_threshold.</b> Значение подбирается "
        "автоматически: медиана log₁₀(η) ближайших соседей смещается на "
        "−2σ относительно нулевой гипотезы Пуассона, что обеспечивает "
        "баланс между полнотой и ложноположительными срабатываниями.",
        S["body"]
    ))
    story.append(PageBreak())

    # ── PAGE 7: Results ────────────────────────────────────────────────────────
    story += section("6. Результаты полного исторического анализа", S)
    story.append(Paragraph(
        "Полный каталог BCE–2026 (<b>4 418 событий M≥6.5</b>, включая исторический каталог) "
        "выявил <b>47 глобальных серий</b> в трёх временны́х окнах:",
        S["body"]
    ))
    key_results = [
        "• Современный период (1973–2026): <b>27 серий</b>, p &lt; 0.0001, z = −6.17",
        "• Ранний инструментальный (1900–1972): <b>15 серий</b>, p = 0.007, z = −2.43 — НОВЫЙ значимый результат",
        "• Исторический (до 1900): <b>5 эпизодов</b>, p = 0.46 (недостаточно данных)",
        "• Полнота каталога: <b>Mc = 6.55</b>; b-значение = <b>0.911 ± 0.018</b>",
        "• Крупнейшая серия: <b>1905–1910</b> — 193 события, 43 региона, Mmax=8.8",
        "• Средневековый эпизод <b>856–887 н.э.</b>: Иран, Япония, Испания, Греция (6 событий)",
    ]
    for r in key_results:
        story.append(Paragraph(r, S["bullet"]))
    story.append(Spacer(1, 0.3 * cm))

    # Epoch breakdown table
    story.append(Paragraph("<b>Разбивка по временны́м окнам</b>", S["body"]))
    story.append(Spacer(1, 0.15 * cm))
    epoch_col_w = [(PAGE_W - 2 * MARGIN) * f for f in [0.30, 0.15, 0.12, 0.18, 0.25]]
    epoch_data = [
        [
            Paragraph("<b>Период</b>", S["body"]),
            Paragraph("<b>Событий</b>", S["body"]),
            Paragraph("<b>Серий</b>", S["body"]),
            Paragraph("<b>p-значение</b>", S["body"]),
            Paragraph("<b>z-оценка</b>", S["body"]),
        ],
        [
            Paragraph("1973–2026 (современный)", S["body"]),
            Paragraph("2041", S["body"]),
            Paragraph("27", S["body"]),
            Paragraph("< 0.0001", S["body"]),
            Paragraph("-6.17", S["body"]),
        ],
        [
            Paragraph("1900–1972 (ранний инструм.)", S["body"]),
            Paragraph("2179", S["body"]),
            Paragraph("15", S["body"]),
            Paragraph("0.007", S["body"]),
            Paragraph("-2.43", S["body"]),
        ],
        [
            Paragraph("До 1900 (исторический)", S["body"]),
            Paragraph("67", S["body"]),
            Paragraph("5", S["body"]),
            Paragraph("0.46", S["body"]),
            Paragraph("-0.74", S["body"]),
        ],
        [
            Paragraph("<b>Итого</b>", S["body"]),
            Paragraph("<b>4418</b>", S["body"]),
            Paragraph("<b>47</b>", S["body"]),
            Paragraph("—", S["body"]),
            Paragraph("—", S["body"]),
        ],
    ]
    epoch_tbl = Table(epoch_data, colWidths=epoch_col_w)
    epoch_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("TEXTCOLOR",  (0, 0), (-1, 0), white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_GREY]),
        ("BOX",       (0, 0), (-1, -1), 0.5, RULE_GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, RULE_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(epoch_tbl)
    story.append(Spacer(1, 0.3 * cm))

    # Top-5 series table
    story.append(Paragraph("<b>Топ-5 серий по событиям и охвату</b>", S["body"]))
    story.append(Spacer(1, 0.15 * cm))
    series_col_w = [(PAGE_W - 2 * MARGIN) * f for f in [0.18, 0.08, 0.12, 0.10, 0.22, 0.30]]
    series_data = [
        [
            Paragraph("<b>Серия</b>", S["body"]),
            Paragraph("<b>N</b>", S["body"]),
            Paragraph("<b>Регионов</b>", S["body"]),
            Paragraph("<b>Mmax</b>", S["body"]),
            Paragraph("<b>Период</b>", S["body"]),
            Paragraph("<b>Примечание</b>", S["body"]),
        ],
        [
            Paragraph("1905–1910", S["body"]),
            Paragraph("193", S["body"]),
            Paragraph("43", S["body"]),
            Paragraph("8.8", S["body"]),
            Paragraph("1905–1910", S["body"]),
            Paragraph("Крупнейшая за всё время", S["body"]),
        ],
        [
            Paragraph("1960–1965", S["body"]),
            Paragraph("166", S["body"]),
            Paragraph("35", S["body"]),
            Paragraph("9.2", S["body"]),
            Paragraph("1960–1965", S["body"]),
            Paragraph("Чили 1960 (M9.2)", S["body"]),
        ],
        [
            Paragraph("2011–2013", S["body"]),
            Paragraph("87", S["body"]),
            Paragraph("32", S["body"]),
            Paragraph("8.6", S["body"]),
            Paragraph("2011–2013", S["body"]),
            Paragraph("Тохоку 2011", S["body"]),
        ],
        [
            Paragraph("S170", S["body"]),
            Paragraph("46", S["body"]),
            Paragraph("12", S["body"]),
            Paragraph("9.1", S["body"]),
            Paragraph("2002–2023", S["body"]),
            Paragraph("Суматра 2004 (M9.1)", S["body"]),
        ],
        [
            Paragraph("856–887 н.э.", S["body"]),
            Paragraph("6", S["body"]),
            Paragraph("4", S["body"]),
            Paragraph("8.6", S["body"]),
            Paragraph("856–887", S["body"]),
            Paragraph("Средневековый эпизод", S["body"]),
        ],
    ]
    series_tbl = Table(series_data, colWidths=series_col_w)
    series_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("TEXTCOLOR",  (0, 0), (-1, 0), white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_GREY]),
        ("BOX",       (0, 0), (-1, -1), 0.5, RULE_GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, RULE_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(series_tbl)
    story.append(PageBreak())

    # ── PAGE 8: Statistical testing ────────────────────────────────────────────
    story += section("7. Статистическое тестирование", S)
    story.append(Paragraph(
        "<b>Нулевая гипотеза H₀:</b> последовательность событий является "
        "независимым стационарным пуассоновским процессом с наблюдаемой "
        "интенсивностью λ(t, x) — пространственно-временны́м распределением "
        "без межсобытийных корреляций.",
        S["body"]
    ))
    test_items = [
        "<b>Процедура перестановки:</b> случайно перемешиваем временны́е "
        "метки, сохраняя координаты и магнитуды. Для каждой из N "
        "перестановок пересчитываем статистику T.",
        "<b>Тест-статистика T:</b> среднее значение log₁₀(η) ближайшего "
        "соседа по всей выборке. Меньшие значения T соответствуют "
        "более кластеризованному каталогу.",
        "<b>Финальный результат (n=10 000 суррогатов):</b> p &lt; <b>0.0001</b> "
        "(z = −6.17; наблюдаемое среднее log₁₀η = −2.884). "
        "Ни одна из 10 000 перестановок не дала кластеризации не слабее наблюдаемой.",
        "<b>Порог публикационной значимости:</b> p &lt; 0.01, "
        "соответствует z-score &gt; 2.33 для нормального приближения.",
        "<b>Bootstrap CI:</b> 10 000 выборок с возвращением для "
        "характеристик каждой серии (число событий, временной охват, "
        "географический разброс). 95% доверительные интервалы.",
        "<b>Тест Колмогорова–Смирнова:</b> проверка соответствия "
        "распределения межсобытийных времён внутри серий теоретическому "
        "Омори–Уцу (степенно́й закон).",
    ]
    for item in test_items:
        story.append(Paragraph(f"• {item}", S["bullet"]))

    story.append(Spacer(1, 0.4 * cm))
    story.append(FormulaBox("  p < 0.0001  ★★★     z = −6.17  ",
                            PAGE_W - 2 * MARGIN))
    story.append(Paragraph(
        "Наблюдаемое: mean log₁₀(η) = −2.884  ·  Нулевая гипотеза: −2.814 ± 0.011  ·  "
        "4 418 событий M≥6.5, BCE–2026  ·  n = 10 000 перестановок  ·  "
        "Ранний инструментальный: p = 0.007, z = −2.43",
        S["formula_caption"]
    ))
    story.append(PageBreak())

    # ── PAGE 9: Architecture ───────────────────────────────────────────────────
    story += section("8. Архитектура проекта", S)
    modules = [
        ("Куратор данных", [
            "USGSFetcher — ComCat REST API, скользящее окно запросов",
            "ISCFetcher — ISC Bulletin, формат CSV с фазами",
            "NOAAFetcher — NGDC Significant Earthquakes Database",
            "CatalogUnifier — дедупликация, нормализация схемы",
            "DBManager / SQLAlchemy — SQLite с индексами на (lat, lon, time)",
        ]),
        ("Методолог", [
            "CompletenessAnalyzer — оценка quality_score по эпохам",
            "TectonicDistanceCalculator — граф Bird (2003) + Дейкстра",
            "SeismicClusterAnalyzer — метрика η, лес связей",
            "MonteCarloTester — 10 000 перестановок, p-value",
        ]),
        ("Автор", [
            "global_map.py / timelines.py — Cartopy визуализация",
            "LaTeX-шаблон manuscript.tex (70 источников в references.bib)",
            "popular_summary_ru.md — научно-популярный дайджест",
        ]),
    ]
    for mod_name, items in modules:
        story.append(Paragraph(f"<b>{mod_name}</b>", S["section"]))
        for item in items:
            story.append(Paragraph(f"  ·  {item}", S["bullet"]))
        story.append(Spacer(1, 0.15 * cm))
    story.append(hr())
    story.append(Paragraph(
        "<b>Стек:</b>  Python 3.12  ·  pandas  ·  networkx  ·  scipy  ·  "
        "Cartopy  ·  SQLAlchemy  ·  46 тестов ✓",
        S["body_center"]
    ))
    story.append(PageBreak())

    # ── PAGE 10: Next steps ─────────────────────────────────────────────────────
    story += section("9. Следующие шаги и ожидаемые результаты", S)
    roadmap = [
        ("Этап 1 — Загрузка данных",
         "Скачать ~160 000 событий из трёх API (USGS, ISC, NOAA). "
         "Унификация схемы, дедупликация, расчёт quality_score. "
         "Ожидаемый срок: 2–3 недели."),
        ("Этап 2 — Обнаружение кандидатов",
         "Построение тектонического графа, расчёт матрицы η "
         "для всех пар событий с t_ij < 10 лет и r_ij < 10 000 км. "
         "Выделение предварительных серий-кандидатов."),
        ("Этап 3 — Monte Carlo валидация",
         "10 000 × 3 независимых запуска ≈ 30 млн итераций. "
         "Параллельная обработка (multiprocessing). "
         "Финальный список серий с p < 0.01."),
        ("Этап 4 — Публикация",
         "Статья в Geophysical Research Letters (GRL) или "
         "Bulletin of the Seismological Society of America (BSSA). "
         "Публикация кода на GitHub (лицензия MIT)."),
    ]
    for stage, desc in roadmap:
        story.append(Paragraph(f"<b>{stage}</b>", S["bullet"]))
        story.append(Paragraph(desc, S["step"]))
        story.append(Spacer(1, 0.1 * cm))
    story.append(PageBreak())

    # ── PAGE 11: References ────────────────────────────────────────────────────
    story += section("10. Ключевые публикации", S)
    refs = [
        "[1]  Baiesi M., Paczuski M. (2004). Scale-free networks of earthquakes and "
        "aftershocks. <i>Phys. Rev. E</i>, 69, 066106.",
        "[2]  Bird P. (2003). An updated digital model of plate boundaries. "
        "<i>Geochem. Geophys. Geosyst.</i>, 4(3), 1027.",
        "[3]  Brodsky E.E., Prejean S.G. (2005). New constraints on mechanisms of "
        "remotely triggered seismicity at Long Valley Caldera. "
        "<i>J. Geophys. Res.</i>, 110, B04302.",
        "[4]  Hill D.P. et al. (1993). Seismicity remotely triggered by the "
        "magnitude 7.3 Landers, California, earthquake. "
        "<i>Science</i>, 260, 1617–1623.",
        "[5]  Omori F. (1894). On the aftershocks of earthquakes. "
        "<i>J. Coll. Sci. Imp. Univ. Tokyo</i>, 7, 111–200.",
        "[6]  Utsu T., Ogata Y., Matsu'ura R.S. (1995). The centenary of the "
        "Omori formula for a decay law of aftershock activity. "
        "<i>J. Phys. Earth</i>, 43(1), 1–33.",
        "[7]  Zaliapin I., Ben-Zion Y. (2013). Earthquake clusters in southern "
        "California I: Identification and stability. "
        "<i>J. Geophys. Res. Solid Earth</i>, 118, 2847–2864.",
        "[8]  Parsons T., Velasco A.A. (2011). Absence of remotely triggered "
        "large earthquakes beyond the mainshock region. "
        "<i>Nat. Geosci.</i>, 4, 312–316.",
        "[9]  Shearer P.M., Stark P.B. (2012). Global risk of big earthquakes "
        "has not recently increased. "
        "<i>Proc. Natl. Acad. Sci.</i>, 109(3), 717–721.",
        "[10] Felzer K.R., Brodsky E.E. (2006). Decay of aftershock density with "
        "distance indicates triggering by dynamic stress. "
        "<i>Nature</i>, 441, 735–738.",
    ]
    for ref in refs:
        story.append(Paragraph(ref, S["ref"]))
        story.append(Spacer(1, 0.05 * cm))

    return story


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "overview.pdf")

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=2.2 * cm,
        title="Глобальные сейсмические серии",
        author="Paleoseismic Clustering Project",
    )

    styles = make_styles()
    story = build_story(styles)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"PDF создан: {out_path}")
    print(f"Размер файла: {size_kb:.1f} KB")
    print("Количество страниц: 11")


if __name__ == "__main__":
    main()
