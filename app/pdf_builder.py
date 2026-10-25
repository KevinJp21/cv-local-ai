
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    Flowable,
)

# Paleta sobria: negro y grises.
BLACK = colors.HexColor("#171717")
INK = colors.HexColor("#383838")
HEADING = colors.HexColor("#292929")
NAME_GRAY = colors.HexColor("#595959")
RULE = colors.HexColor("#858585")
LIGHT_GRAY = colors.HexColor("#E8E8E8")

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


def safe(value: str) -> str:
    """Escapa XML y permite **negrita** dentro del texto."""
    text = escape(str(value)).replace("\n", "<br/>")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


class SpacedText(Flowable):
    """Texto con espaciado entre letras."""

    def __init__(
        self,
        text,
        font,
        size,
        color,
        char_space=0,
        leading=None,
    ):
        super().__init__()
        self.text = text
        self.font = font
        self.size = size
        self.color = color
        self.char_space = char_space
        self.leading = leading or size * 1.1

    def wrap(self, availWidth, availHeight):
        self.width = (
            stringWidth(self.text, self.font, self.size)
            + self.char_space * max(0, len(self.text) - 1)
        )
        self.height = self.leading
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        text = canvas.beginText(0, self.leading * 0.22)
        text.setFont(self.font, self.size)
        text.setFillColor(self.color)
        text.setCharSpace(self.char_space)
        text.textOut(self.text)
        canvas.drawText(text)


def build_cv_pdf(profile: dict, cv: dict, output_path: Path) -> None:
    margin_x = 15 * mm

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=margin_x,
        leftMargin=margin_x,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"CV - {profile['name']}",
        author=profile["name"],
    )

    content_w = A4[0] - 2 * margin_x

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="CVHeadTitle",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=15,
        textColor=BLACK,
        alignment=TA_RIGHT,
        spaceAfter=5,
    ))

    styles.add(ParagraphStyle(
        name="CVHeadContact",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=8.5,
        leading=11,
        textColor=INK,
        alignment=TA_RIGHT,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name="CVSection",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=13,
        textColor=HEADING,
        spaceBefore=0,
        spaceAfter=5,
        keepWithNext=True,
    ))

    styles.add(ParagraphStyle(
        name="CVBody",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=9.3,
        leading=13.2,
        textColor=INK,
        alignment=TA_LEFT,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name="CVSkill",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=8.5,
        leading=11.5,
        textColor=INK,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name="CVJobTitle",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10.2,
        leading=13,
        textColor=BLACK,
        spaceBefore=0,
        spaceAfter=1,
        keepWithNext=True,
    ))

    styles.add(ParagraphStyle(
        name="CVCompany",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=9,
        leading=12,
        textColor=INK,
        spaceAfter=1,
        keepWithNext=True,
    ))

    styles.add(ParagraphStyle(
        name="CVDates",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=8.5,
        leading=11,
        textColor=HEADING,
        spaceAfter=4,
        keepWithNext=True,
    ))

    styles.add(ParagraphStyle(
        name="CVBullet",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=9,
        leading=12.2,
        leftIndent=13,
        firstLineIndent=0,
        bulletIndent=1,
        textColor=INK,
        spaceAfter=4,
        splitLongWords=0,
    ))

    styles.add(ParagraphStyle(
        name="CVMeta",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=8.4,
        leading=11.5,
        textColor=INK,
    ))

    story = []
    contact = cv["contact"]

    # --------------------------------------------------
    # ENCABEZADO
    # --------------------------------------------------

    name_parts = profile["name"].upper().split(None, 1)
    first = name_parts[0]
    rest = name_parts[1] if len(name_parts) > 1 else ""

    name_block = [
        SpacedText(
            first,
            FONT,
            27,
            NAME_GRAY,
            char_space=3.0,
            leading=31,
        ),
        Spacer(1, 1),
        SpacedText(
            rest,
            FONT,
            24,
            BLACK,
            char_space=0.7,
            leading=28,
        ),
    ]

    def link(text, href):
        return (
            f'<link href="{escape(href)}" color="#292929">'
            f'<u>{safe(text)}</u></link>'
        )

    def as_url(value):
        value = str(value)
        return value if value.startswith(("http://", "https://")) else (
            "https://" + value
        )

    right_block = [
        Paragraph(
            safe(cv["target_title"].upper()),
            styles["CVHeadTitle"],
        )
    ]

    if cv.get("header_note"):
        right_block.append(
            Paragraph(
                safe(cv["header_note"]),
                styles["CVHeadContact"],
            )
        )

    for key, href in (
        ("portfolio", as_url(contact["portfolio"])),
        ("linkedin", as_url(contact["linkedin"])),
        ("email", "mailto:" + contact["email"]),
    ):
        if contact.get(key):
            right_block.append(
                Paragraph(
                    link(contact[key], href),
                    styles["CVHeadContact"],
                )
            )

    if contact.get("phone"):
        right_block.append(
            Paragraph(
                safe(contact["phone"]),
                styles["CVHeadContact"],
            )
        )

    header = Table(
        [[name_block, right_block]],
        colWidths=[
            content_w * 0.47,
            content_w * 0.53,
        ],
    )

    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(header)

    def rule(before=5, after=7, thickness=1):
        story.append(
            HRFlowable(
                width="100%",
                thickness=thickness,
                color=RULE,
                spaceBefore=before,
                spaceAfter=after,
                lineCap="butt",
            )
        )

    def heading(title):
        story.append(
            Paragraph(title.upper(), styles["CVSection"])
        )

    rule(before=7, after=8, thickness=1.5)

    # --------------------------------------------------
    # PERFIL PROFESIONAL
    # --------------------------------------------------

    heading("Perfil profesional")

    story.append(
        Paragraph(
            safe(cv["professional_summary"]),
            styles["CVBody"],
        )
    )

    rule(before=5, after=8)

    # --------------------------------------------------
    # EXPERIENCIA: AHORA TIENE PRIORIDAD
    # --------------------------------------------------

    experiences = cv.get("experiences", [])
    if experiences:
        heading("Experiencia")

        for exp in experiences:
            story.append(
                Paragraph(
                    safe(exp["title"]),
                    styles["CVJobTitle"],
                )
            )

            story.append(
                Paragraph(
                    safe(exp["company"]),
                    styles["CVCompany"],
                )
            )

            story.append(
                Paragraph(
                    safe(exp["dates"]),
                    styles["CVDates"],
                )
            )

            for bullet in exp.get("bullets", []):
                story.append(
                    Paragraph(
                        safe(bullet),
                        styles["CVBullet"],
                        bulletText="•",
                    )
                )

            # Separación discreta entre experiencias.
            story.append(Spacer(1, 5))

        rule(before=3, after=7, thickness=1.5)

    # --------------------------------------------------
    # HABILIDADES Y TECNOLOGÍAS
    # --------------------------------------------------

    heading("Habilidades y/o Tecnologías")

    for group, skills in cv.get("skill_groups", {}).items():
        cleaned = [
            str(skill).strip()
            for skill in skills
            if str(skill).strip()
        ]

        if not cleaned:
            continue

        story.append(
            Paragraph(
                f"<b>{safe(group)}:</b> "
                f"{safe(', '.join(cleaned))}",
                styles["CVSkill"],
            )
        )

    rule(before=6, after=7)

    # --------------------------------------------------
    # EDUCACIÓN, IDIOMAS Y UBICACIÓN
    # --------------------------------------------------

    edu_lines = str(cv["education_text"]).split("\n")
    edu_html = []

    for index, line in enumerate(edu_lines):
        line = safe(line.strip())

        if not line:
            continue

        if index == 0:
            edu_html.append(f"<b>{line}</b>")
        else:
            edu_html.append(line)

    edu_cell = [
        Paragraph("EDUCACIÓN", styles["CVSection"]),
        Paragraph(
            "<br/>".join(edu_html),
            styles["CVMeta"],
        ),
    ]

    lang_cell = [
        Paragraph("IDIOMAS", styles["CVSection"]),
        Paragraph(
            "<br/>".join(
                safe(language)
                for language in cv.get("languages", [])
            ),
            styles["CVMeta"],
        ),
    ]

    loc_cell = [
        Paragraph("UBICACIÓN", styles["CVSection"]),
        Paragraph(
            safe(contact.get("location", "")),
            styles["CVMeta"],
        ),
        Spacer(1, 3),
        Paragraph(
            f"<b>Disponibilidad:</b> "
            f"{safe(contact.get('availability', ''))}",
            styles["CVMeta"],
        ),
    ]

    cols = Table(
        [[edu_cell, lang_cell, loc_cell]],
        colWidths=[
            content_w * 0.38,
            content_w * 0.17,
            content_w * 0.45,
        ],
    )

    cols.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(cols)

    doc.build(story)
