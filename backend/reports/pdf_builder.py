import io
import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
)

BRAND_GREEN = colors.HexColor('#1A5C38')
BRAND_GOLD = colors.HexColor('#D4A012')
LIGHT_GREEN = colors.HexColor('#E8F5EE')
LIGHT_GREY = colors.HexColor('#F5F5F5')
TEXT_COLOR = colors.HexColor('#1A1A1A')
TEXT_SECONDARY = colors.HexColor('#5A5A5A')

DIMENSION_NAMES = {
    'R': 'Realistic',
    'I': 'Investigative',
    'A': 'Artistic',
    'S': 'Social',
    'E': 'Enterprising',
    'C': 'Conventional',
}


def build_student_report(data):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
        compress=False,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'ReportTitle', parent=styles['Heading1'],
        fontSize=18, textColor=BRAND_GREEN, spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        'SectionTitle', parent=styles['Heading2'],
        fontSize=13, textColor=BRAND_GREEN, spaceBefore=6 * mm, spaceAfter=3 * mm,
    ))
    styles.add(ParagraphStyle(
        'BodyText2', parent=styles['BodyText'],
        fontSize=10, textColor=TEXT_COLOR,
    ))
    styles.add(ParagraphStyle(
        'SmallGrey', parent=styles['BodyText'],
        fontSize=8, textColor=TEXT_SECONDARY,
    ))

    elements = []

    # --- Header ---
    logo_path = data.get('logo_path')
    if logo_path and os.path.isfile(logo_path):
        elements.append(Image(logo_path, width=30 * mm, height=30 * mm))
        elements.append(Spacer(1, 3 * mm))

    elements.append(Paragraph('Student Progress Report', styles['ReportTitle']))
    elements.append(Paragraph(
        f'Generated on {date.today().strftime("%d %B %Y")}',
        styles['SmallGrey'],
    ))
    elements.append(Spacer(1, 4 * mm))

    # --- Student profile ---
    elements.append(Paragraph('Student Profile', styles['SectionTitle']))
    school_display = data.get('school_name') or 'Self-Guided'
    county = data.get('county') or 'Not set'
    profile_data = [
        ['Name', data['student_name']],
        ['Grade', str(data['grade'])],
        ['School', school_display],
        ['County', county],
        ['Email', data['email']],
    ]
    profile_table = Table(profile_data, colWidths=[35 * mm, 130 * mm])
    profile_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), TEXT_SECONDARY),
        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_COLOR),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(profile_table)
    elements.append(Spacer(1, 4 * mm))

    # --- Grades table ---
    elements.append(Paragraph('Academic Grades', styles['SectionTitle']))
    subjects = data.get('subjects', [])
    if not subjects:
        elements.append(Paragraph('No subjects enrolled yet.', styles['BodyText2']))
    else:
        for subj in subjects:
            elements.append(Paragraph(
                f"<b>{subj['name']}</b> ({subj['code']})",
                styles['BodyText2'],
            ))
            if not subj['grades']:
                elements.append(Paragraph(
                    '&nbsp;&nbsp;&nbsp;&nbsp;No grades recorded.',
                    styles['SmallGrey'],
                ))
            else:
                grade_rows = [['Term', 'Year', 'Level']]
                for g in subj['grades']:
                    grade_rows.append([
                        f"Term {g['term']}",
                        str(g['year']),
                        g['label'],
                    ])
                grade_table = Table(grade_rows, colWidths=[30 * mm, 25 * mm, 110 * mm])
                grade_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GREEN),
                    ('TEXTCOLOR', (0, 0), (-1, 0), BRAND_GREEN),
                    ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_COLOR),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                ]))
                elements.append(grade_table)
            elements.append(Spacer(1, 3 * mm))

    # --- RIASEC results ---
    elements.append(Paragraph('Career Personality (RIASEC)', styles['SectionTitle']))
    riasec = data.get('riasec')
    if not riasec:
        elements.append(Paragraph('No assessment completed yet.', styles['BodyText2']))
    else:
        scores = riasec['scores']
        sorted_dims = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
        top_3 = set(sorted_dims[:3])

        riasec_rows = [['Dimension', 'Score']]
        for dim in ['R', 'I', 'A', 'S', 'E', 'C']:
            label = DIMENSION_NAMES.get(dim, dim)
            riasec_rows.append([label, str(scores.get(dim, 0))])

        riasec_table = Table(riasec_rows, colWidths=[60 * mm, 30 * mm])
        style_cmds = [
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GREEN),
            ('TEXTCOLOR', (0, 0), (-1, 0), BRAND_GREEN),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ]
        dim_order = ['R', 'I', 'A', 'S', 'E', 'C']
        for i, dim in enumerate(dim_order):
            row_idx = i + 1
            if dim in top_3:
                style_cmds.append(('BACKGROUND', (0, row_idx), (-1, row_idx), LIGHT_GREEN))
                style_cmds.append(('FONTNAME', (0, row_idx), (0, row_idx), 'Helvetica-Bold'))

        riasec_table.setStyle(TableStyle(style_cmds))
        elements.append(riasec_table)

        if riasec.get('holland_code'):
            elements.append(Spacer(1, 2 * mm))
            elements.append(Paragraph(
                f"Holland Code: <b>{riasec['holland_code']}</b>",
                styles['BodyText2'],
            ))

    elements.append(Spacer(1, 4 * mm))

    # --- Pathway recommendations ---
    recommendations = data.get('recommendations', [])
    if recommendations:
        elements.append(Paragraph('Recommended Career Pathways', styles['SectionTitle']))
        rec_rows = [['Rank', 'Pathway', 'Fit']]
        for rec in recommendations[:3]:
            rec_rows.append([
                str(rec['rank']),
                rec['pathway_name'],
                f"{rec['fit_pct']}%",
            ])

        rec_table = Table(rec_rows, colWidths=[20 * mm, 110 * mm, 25 * mm])
        rec_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GREEN),
            ('TEXTCOLOR', (0, 0), (-1, 0), BRAND_GREEN),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#FEF8E7')),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ]))
        elements.append(rec_table)

    elements.append(Spacer(1, 8 * mm))

    # --- Footer disclaimer ---
    elements.append(Paragraph(
        'Generated by Smarta Shauri — This report is advisory only and does not '
        'constitute an official academic record.',
        styles['SmallGrey'],
    ))

    doc.build(elements)
    return buf.getvalue()
