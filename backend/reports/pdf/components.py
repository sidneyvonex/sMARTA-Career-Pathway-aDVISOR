"""Reusable ReportLab flowables shared by all PDF report types."""

import os
from datetime import date
from xml.sax.saxutils import escape

from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle

from .theme import BRAND_GREEN, LIGHT_GREEN, LIGHT_GREY, TEXT_COLOR, TEXT_SECONDARY


def text(value):
    return escape(str(value or ''))


def report_header(title, subtitle='', generated_at=None, logo_path=None, styles=None):
    elements = []
    if logo_path and os.path.isfile(logo_path):
        elements.extend([Image(logo_path, width=30 * mm, height=30 * mm), Spacer(1, 3 * mm)])
    elements.append(Paragraph(text(title), styles['ReportTitle']))
    if subtitle:
        elements.append(Paragraph(text(subtitle), styles['BodyText2']))
    generated = generated_at or date.today().strftime('%d %B %Y')
    elements.extend([
        Paragraph(f'Generated on {text(generated)}', styles['SmallGrey']),
        Spacer(1, 4 * mm),
    ])
    return elements


def section_title(value, styles):
    return Paragraph(text(value), styles['SectionTitle'])


def key_value_table(rows, col_widths):
    table = Table(rows, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), TEXT_SECONDARY),
        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_COLOR),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return table


def data_table(headers, rows, col_widths, highlight_row_indices=None):
    data = [headers, *rows]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    commands = [
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), LIGHT_GREY),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.25, TEXT_SECONDARY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    for index in range(1, len(data)):
        if index % 2 == 0:
            commands.append(('BACKGROUND', (0, index), (-1, index), LIGHT_GREY))
    for index in highlight_row_indices or []:
        commands.append(('BACKGROUND', (0, index + 1), (-1, index + 1), LIGHT_GREEN))
    table.setStyle(TableStyle(commands))
    return table


def stat_grid(stats, styles, columns=3):
    cells = []
    for stat in stats:
        value = Paragraph(f'<b>{text(stat.get("value"))}</b>', styles['ReportTitle'])
        label = Paragraph(text(stat.get('label')), styles['BodyText2'])
        sublabel = Paragraph(text(stat.get('sublabel')), styles['SmallGrey'])
        cells.append([value, label, sublabel])
    rows = [cells[index:index + columns] for index in range(0, len(cells), columns)]
    if rows and len(rows[-1]) < columns:
        rows[-1].extend([''] * (columns - len(rows[-1])))
    table = Table(rows, colWidths=[170 * mm / columns] * columns)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GREEN),
        ('BOX', (0, 0), (-1, -1), 0.5, BRAND_GREEN),
        ('INNERGRID', (0, 0), (-1, -1), 2, LIGHT_GREY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return table


def empty_state(message, styles):
    return Paragraph(text(message), styles['BodyText2'])


def footer_disclaimer(message, styles):
    return Paragraph(text(message), styles['SmallGrey'])
