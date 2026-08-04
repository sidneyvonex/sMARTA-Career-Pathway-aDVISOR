"""Shared Smarta Shauri PDF colours and paragraph styles."""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm

BRAND_GREEN = colors.HexColor('#1A5C38')
BRAND_GOLD = colors.HexColor('#D4A012')
LIGHT_GREEN = colors.HexColor('#E8F5EE')
LIGHT_GREY = colors.HexColor('#F5F5F5')
TEXT_COLOR = colors.HexColor('#1A1A1A')
TEXT_SECONDARY = colors.HexColor('#5A5A5A')


def get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'ReportTitle', parent=styles['Heading1'],
        fontSize=18, textColor=BRAND_GREEN, spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        'SectionTitle', parent=styles['Heading2'],
        fontSize=13, textColor=BRAND_GREEN,
        spaceBefore=6 * mm, spaceAfter=3 * mm,
    ))
    styles.add(ParagraphStyle(
        'BodyText2', parent=styles['BodyText'],
        fontSize=10, textColor=TEXT_COLOR,
    ))
    styles.add(ParagraphStyle(
        'SmallGrey', parent=styles['BodyText'],
        fontSize=8, textColor=TEXT_SECONDARY,
    ))
    return styles
