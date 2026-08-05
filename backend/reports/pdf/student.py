import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Circle, Drawing, Line, String
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

from .components import footer_disclaimer, report_header, text
from .theme import (
    BRAND_GOLD,
    BRAND_GREEN,
    LIGHT_GREEN,
    LIGHT_GREY,
    TEXT_COLOR,
    TEXT_SECONDARY,
    get_styles,
)

DIMENSION_NAMES = {
    'R': 'Realistic',
    'I': 'Investigative',
    'A': 'Artistic',
    'S': 'Social',
    'E': 'Enterprising',
    'C': 'Conventional',
}


_text = text

LEVEL_POINTS = {
    'BE2': 1, 'BE1': 2, 'AE2': 3, 'AE1': 4,
    'ME2': 5, 'ME1': 6, 'EE2': 7, 'EE1': 8,
}
LEVEL_LABELS = {
    'BE2': 'Below Expectation - Level 2', 'BE1': 'Below Expectation - Level 1',
    'AE2': 'Approaching Expectation - Level 2', 'AE1': 'Approaching Expectation - Level 1',
    'ME2': 'Meeting Expectation - Level 2', 'ME1': 'Meeting Expectation - Level 1',
    'EE2': 'Exceeding Expectation - Level 2', 'EE1': 'Exceeding Expectation - Level 1',
}
SERIES_COLORS = [
    colors.HexColor('#136F63'), colors.HexColor('#1769AA'),
    colors.HexColor('#D58B00'), colors.HexColor('#7B4AB5'),
    colors.HexColor('#C24949'), colors.HexColor('#217A9B'),
]


def _progress_chart(subjects):
    records = [record for subject in subjects[:6] for record in (subject.get('evidence') or subject.get('records_used') or []) if record.get('level') in LEVEL_POINTS]
    periods = sorted({(record.get('year'), record.get('term')) for record in records})
    if not periods:
        return None
    width, height = 165 * mm, 58 * mm
    left, right, bottom, top = 29 * mm, 35 * mm, 11 * mm, 7 * mm
    plot_width, plot_height = width - left - right, height - bottom - top
    drawing = Drawing(width, height)
    for points, label in ((1, 'Below'), (3, 'Approaching'), (5, 'Meeting'), (7, 'Exceeding')):
        y = bottom + ((points - 1) / 7) * plot_height
        drawing.add(Line(left, y, width - right, y, strokeColor=colors.HexColor('#D8DEE6'), strokeWidth=0.5))
        drawing.add(String(left - 3 * mm, y - 1.2 * mm, label, textAnchor='end', fontName='Helvetica', fontSize=6.5, fillColor=TEXT_SECONDARY))

    def x_for(period):
        index = periods.index(period)
        return left + (plot_width / 2 if len(periods) == 1 else index * plot_width / (len(periods) - 1))

    multiple_years = len({item[0] for item in periods}) > 1
    for period in periods:
        x = x_for(period)
        year, term = period
        label = f'{year} T{term}' if multiple_years else f'Term {term}'
        drawing.add(String(x, 2 * mm, label, textAnchor='middle', fontName='Helvetica', fontSize=6.5, fillColor=TEXT_SECONDARY))
    for index, subject in enumerate(subjects[:6]):
        color = SERIES_COLORS[index % len(SERIES_COLORS)]
        by_period = {(record.get('year'), record.get('term')): record for record in (subject.get('evidence') or subject.get('records_used') or []) if record.get('level') in LEVEL_POINTS}
        points = []
        for period in periods:
            record = by_period.get(period)
            if not record:
                continue
            x = x_for(period)
            y = bottom + ((LEVEL_POINTS[record['level']] - 1) / 7) * plot_height
            points.append((x, y))
            drawing.add(Circle(x, y, 1.5 * mm, fillColor=color, strokeColor=colors.white, strokeWidth=0.5))
        for start, end in zip(points, points[1:]):
            drawing.add(Line(*start, *end, strokeColor=color, strokeWidth=1.6))
        legend_y = height - top - index * 6 * mm
        drawing.add(Line(width - right + 3 * mm, legend_y, width - right + 10 * mm, legend_y, strokeColor=color, strokeWidth=2))
        drawing.add(String(width - right + 12 * mm, legend_y - 1.2 * mm, str(subject.get('subject_name') or '')[:18], fontName='Helvetica', fontSize=6.5, fillColor=TEXT_COLOR))
    return drawing


def _academic_progress_elements(data, styles, include_status_basis=True):
    progress = data.get('academic_progress') or {}
    subjects = progress.get('subjects') or []
    filters = data.get('report_filters') or {}
    filter_labels = []
    if filters.get('year'):
        filter_labels.append(f"Academic year {filters['year']}")
    if filters.get('term'):
        filter_labels.append(f"Term {filters['term']}")
    if filters.get('subject'):
        filter_labels.append(next((str(item.get('subject_name')) for item in subjects if item.get('continuity_code') == filters['subject']), filters['subject']))
    evidence_count = sum(len(item.get('evidence') or item.get('records_used') or []) for item in subjects)
    latest, improving = [], 0
    for subject in subjects:
        ordered = sorted(subject.get('evidence') or subject.get('records_used') or [], key=lambda item: (item.get('year') or 0, item.get('term') or 0))
        if ordered:
            latest.append(ordered[-1])
        if len(ordered) > 1 and LEVEL_POINTS.get(ordered[-1].get('level'), 0) > LEVEL_POINTS.get(ordered[0].get('level'), 0):
            improving += 1
    meeting = sum(LEVEL_POINTS.get(item.get('level'), 0) >= 5 for item in latest)
    elements = [Paragraph('Academic Progress', styles['SectionTitle'])]
    if filter_labels:
        elements.append(Paragraph('<b>Reporting scope:</b> ' + _text(' / '.join(filter_labels)), styles['SmallGrey']))
    summary = Table([
        ['Subjects shown', 'Improving', 'Meeting or above', 'Evidence records'],
        [str(len(subjects)), str(improving), f'{meeting} of {len(latest)}', str(evidence_count)],
    ], colWidths=[41.25 * mm] * 4)
    summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GREEN), ('TEXTCOLOR', (0, 0), (-1, 0), BRAND_GREEN),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 7.5),
        ('FONTSIZE', (0, 1), (-1, 1), 12), ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#D8DEE6')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D8DEE6')),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.extend([summary, Spacer(1, 3 * mm)])
    chart = _progress_chart(subjects)
    if chart:
        elements.extend([Paragraph('Progress Across Terms', styles['SectionTitle']), chart])
        if len(subjects) > 6:
            elements.append(Paragraph('The chart shows the first six subjects; the table includes every selected subject.', styles['SmallGrey']))
    if not subjects:
        elements.append(Paragraph('No academic evidence matches this reporting scope.', styles['BodyText2']))
    else:
        rows = [['Subject', 'Term 1', 'Term 2', 'Term 3', 'Current band', 'Trend']]
        for subject in subjects:
            ordered = sorted(subject.get('evidence') or subject.get('records_used') or [], key=lambda item: (item.get('year') or 0, item.get('term') or 0))
            latest_year = ordered[-1].get('year') if ordered else None
            by_term = {item.get('term'): item for item in ordered if item.get('year') == latest_year}
            current = ordered[-1].get('level') if ordered else None
            if len(ordered) < 2:
                trend = 'Not enough evidence'
            else:
                delta = LEVEL_POINTS.get(ordered[-1].get('level'), 0) - LEVEL_POINTS.get(ordered[0].get('level'), 0)
                trend = 'Improving' if delta > 0 else 'Declining' if delta < 0 else 'Steady'
            rows.append([
                Paragraph(_text(subject.get('subject_name')), styles['SmallGrey']),
                *[Paragraph(_text(LEVEL_LABELS.get((by_term.get(term) or {}).get('level'), 'No evidence')), styles['SmallGrey']) for term in (1, 2, 3)],
                Paragraph(_text(LEVEL_LABELS.get(current, 'No evidence')), styles['SmallGrey']),
                Paragraph(trend, styles['SmallGrey']),
            ])
        table = Table(rows, colWidths=[32 * mm, 25 * mm, 25 * mm, 25 * mm, 33 * mm, 25 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_GREEN), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#D8DEE6')), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.extend([Paragraph('Subject by Term', styles['SectionTitle']), table])
        if not include_status_basis:
            elements.append(Paragraph('Advisor Note', styles['SectionTitle']))
            for subject in subjects:
                elements.append(Paragraph(
                    f"<b>{_text(subject.get('subject_name'))}:</b> "
                    f"{_text(subject.get('suggested_action'))}",
                    styles['SmallGrey'],
                ))
            elements.append(Paragraph(
                '<b>Evidence basis:</b> recorded CBC results and their verification provenance. '
                f"<b>Advisory:</b> {_text(progress.get('advisory_disclaimer') or 'Performance bands support learning conversations and do not determine placement.')}",
                styles['SmallGrey'],
            ))
            elements.append(Spacer(1, 3 * mm))
            return elements
        elements.append(Paragraph('Status Basis and Next Steps', styles['SectionTitle']))
        for subject in subjects:
            elements.append(Paragraph(
                f"<b>{_text(subject.get('subject_name'))}:</b> "
                f"{_text(subject.get('label'))} ({_text(subject.get('rule_code'))}). "
                f"{_text(subject.get('explanation'))} "
                f"<b>Next step:</b> {_text(subject.get('suggested_action'))}",
                styles['SmallGrey'],
            ))
            elements.append(Paragraph('<b>Evidence used for this status</b>', styles['SmallGrey']))
            for record in subject.get('records_used') or []:
                framework = record.get('framework') or {}
                origin = 'School entered' if record.get('source') == 'school' else 'Learner entered'
                if record.get('verified_at'):
                    verification = f"School verified on {record.get('verified_at')}"
                elif record.get('verified_school'):
                    verification = 'Verification removed; school provenance retained'
                else:
                    verification = 'Not school verified'
                elements.append(Paragraph(
                    f"Grade {_text(record.get('academic_grade'))} &#183; "
                    f"Term {_text(record.get('term'))} {_text(record.get('year'))} &#183; "
                    f"{_text(record.get('level'))} &#183; "
                    f"{_text(framework.get('code'))} {_text(framework.get('version'))}. "
                    f"Origin: {_text(origin)}. Verification: {_text(verification)}.",
                    styles['SmallGrey'],
                ))
    if progress.get('advisory_disclaimer'):
        elements.append(Paragraph(_text(progress['advisory_disclaimer']), styles['SmallGrey']))
    elements.append(Spacer(1, 4 * mm))
    return elements


def build_student_report(data):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
    )

    styles = get_styles()

    elements = report_header(
        'Academic Progress Report',
        generated_at=data.get('generated_at'),
        logo_path=data.get('logo_path'),
        styles=styles,
    )

    if data.get('academic_only') or data.get('report_filters'):
        filters = data.get('report_filters') or {}
        identity_rows = [
            ['Learner', data.get('student_name') or 'Not available', 'Academic year', filters.get('year') or 'All years'],
            ['Class', f"Grade {data.get('grade') or 'Not available'}", 'Reporting term', f"Term {filters['term']}" if filters.get('term') else 'All terms'],
            ['School', data.get('school_name') or 'Self-Guided', 'Identifier', data.get('email') or 'Not available'],
        ]
        identity = Table(identity_rows, colWidths=[23 * mm, 57 * mm, 28 * mm, 57 * mm])
        identity.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), BRAND_GREEN),
            ('TEXTCOLOR', (2, 0), (2, -1), BRAND_GREEN),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GREY),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#D8DEE6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.extend([identity, Spacer(1, 4 * mm)])
        elements.extend(_academic_progress_elements(data, styles, include_status_basis=False))
        doc.build(elements)
        return buf.getvalue()

    elements.extend(_academic_progress_elements(data, styles))
    progress = {}
    progress_subjects = []
    for subject in progress_subjects:
        elements.append(Paragraph(
            f"<b>{_text(subject.get('subject_name'))}</b> — "
            f"{_text(subject.get('label'))} ({_text(subject.get('rule_code'))})",
            styles['BodyText2'],
        ))
        elements.append(Paragraph(
            _text(subject.get('explanation')),
            styles['SmallGrey'],
        ))
        elements.append(Paragraph(
            f"<b>Suggested action:</b> {_text(subject.get('suggested_action'))} "
            f"<b>Evidence:</b> {_text(str(subject.get('evidence_confidence') or '').replace('_', ' '))}",
            styles['SmallGrey'],
        ))
        elements.append(Paragraph(
            '<b>Evidence used for this status</b>',
            styles['SmallGrey'],
        ))
        records_used = subject.get('records_used') or []
        if not records_used:
            elements.append(Paragraph(
                'No academic evidence records were used.',
                styles['SmallGrey'],
            ))
        for record in records_used:
            record_framework = record.get('framework') or {}
            origin = (
                'School entered'
                if record.get('source') == 'school'
                else 'Learner entered'
            )
            if record.get('verified_at'):
                verification = (
                    f"School verified on {record.get('verified_at')}"
                )
            elif record.get('verified_school'):
                verification = 'Verification removed; school provenance retained'
            else:
                verification = 'Not school verified'
            elements.append(Paragraph(
                f"Grade {_text(record.get('academic_grade'))} · "
                f"Term {_text(record.get('term'))} {_text(record.get('year'))} · "
                f"{_text(record.get('level'))} · "
                f"{_text(record_framework.get('code'))} "
                f"{_text(record_framework.get('version'))}",
                styles['SmallGrey'],
            ))
            elements.append(Paragraph(
                f"Origin: {_text(origin)}. Verification: {_text(verification)}.",
                styles['SmallGrey'],
            ))
    if progress.get('advisory_disclaimer'):
        elements.append(Paragraph(
            _text(progress['advisory_disclaimer']),
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

    # --- Evidence provenance and readiness ---
    evidence = data.get('evidence_summary', {})
    elements.append(Paragraph('Evidence Sources', styles['SectionTitle']))
    evidence_rows = [
        [
            'Academic evidence',
            (
                f"{evidence.get('subjects_with_evidence', 0)} of "
                f"{evidence.get('total_subjects', 0)} enrolled subjects; "
                f"{evidence.get('total_grade_records', 0)} recorded grades"
            ),
        ],
        [
            'Interest evidence',
            (
                f"RIASEC assessment submitted {evidence.get('assessment_submitted_at')}"
                if evidence.get('assessment_submitted_at')
                else 'No RIASEC assessment submitted'
            ),
        ],
    ]
    evidence_table = Table(evidence_rows, colWidths=[40 * mm, 125 * mm])
    evidence_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), TEXT_SECONDARY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(evidence_table)

    completeness = data.get('evidence_completeness', {})
    elements.append(Paragraph('Evidence Completeness', styles['SectionTitle']))
    elements.append(Paragraph(
        f"<b>{_text(completeness.get('label') or 'Not started')}</b>. "
        f"{_text(completeness.get('explanation') or 'No academic evidence has been recorded yet.')}",
        styles['BodyText2'],
    ))
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
                grade_rows = [['Term', 'Year', 'Level', 'Framework / provenance']]
                for g in subj['grades']:
                    grade_framework = g.get('framework') or {}
                    provenance = (
                        f"{grade_framework.get('code', 'Unknown framework')} "
                        f"{grade_framework.get('version', '')}; "
                        f"{str(g.get('source') or 'learner').title()}-entered"
                    )
                    if g.get('verified_school') and g.get('verified_at'):
                        provenance += f"; Verified by {g['verified_school']}"
                        provenance += f" on {g['verified_at']}"
                    elif g.get('verified_school'):
                        provenance += (
                            f"; Previously verified by {g['verified_school']}; "
                            'verification removed'
                        )
                    grade_rows.append([
                        f"Term {g['term']}",
                        str(g['year']),
                        g['label'],
                        Paragraph(_text(provenance), styles['SmallGrey']),
                    ])
                grade_table = Table(
                    grade_rows,
                    colWidths=[24 * mm, 20 * mm, 52 * mm, 69 * mm],
                )
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

    # --- Learner-owned academic targets ---
    elements.append(Paragraph('Academic Targets', styles['SectionTitle']))
    academic_goals = data.get('academic_goals') or []
    if not academic_goals:
        elements.append(Paragraph('No academic targets recorded.', styles['BodyText2']))
    for goal in academic_goals:
        current = goal.get('current_level') or {}
        target = goal.get('target_level') or {}
        target_framework = target.get('framework') or {}
        elements.append(Paragraph(
            f"<b>{_text(goal.get('continuity_code'))}</b>: "
            f"{_text(current.get('code'))} to {_text(target.get('code'))} "
            f"by Term {_text(goal.get('target_term'))} {_text(goal.get('target_year'))} "
            f"({_text(target_framework.get('code'))} {_text(target_framework.get('version'))})",
            styles['BodyText2'],
        ))
        elements.append(Paragraph(
            f"<b>Action plan:</b> {_text(goal.get('action_plan'))} "
            f"<b>Status:</b> {_text(goal.get('status'))}",
            styles['SmallGrey'],
        ))

    # --- Learner-owned tertiary exploration goals ---
    elements.append(Paragraph('Education Goals', styles['SectionTitle']))
    education_goals = data.get('education_goals') or []
    if not education_goals:
        elements.append(Paragraph('No education goals recorded.', styles['BodyText2']))
    for goal in education_goals:
        institution = goal.get('institution') or {}
        programme = goal.get('programme') or {}
        provenance = programme or institution
        elements.append(Paragraph(
            f"<b>{_text(institution.get('name'))}</b>"
            f"{f' — {_text(programme.get("name"))}' if programme.get('name') else ''}",
            styles['BodyText2'],
        ))
        elements.append(Paragraph(
            f"{_text(provenance.get('education_framework'))} · "
            f"{_text(provenance.get('admission_cycle'))}; effective "
            f"{_text(provenance.get('effective_date'))}; "
            f"{_text(provenance.get('verification_status'))}. "
            f"Source: {_text(provenance.get('source_url'))}. "
            f"{('Historical reference only.' if provenance.get('verification_status') == 'historical' else '')}",
            styles['SmallGrey'],
        ))
    elements.append(Spacer(1, 4 * mm))

    # --- RIASEC results ---
    elements.append(Paragraph('Interest Profile (RIASEC)', styles['SectionTitle']))
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

    # --- Pathways suggested for exploration ---
    recommendations = data.get('recommendations', [])
    if recommendations:
        elements.append(Paragraph('Pathways Suggested for Exploration', styles['SectionTitle']))
        elements.append(Paragraph(
            'Interest alignment is an advisory starting point based on the learner\'s responses. '
            'It does not predict success or determine placement.',
            styles['BodyText2'],
        ))
        elements.append(Spacer(1, 2 * mm))
        rec_rows = [['Rank', 'Pathway', 'Interest alignment']]
        for rec in recommendations[:3]:
            rec_rows.append([
                str(rec['rank']),
                rec['pathway_name'],
                'Strongest' if rec['rank'] == 1 else 'Suggested',
            ])

        rec_table = Table(rec_rows, colWidths=[20 * mm, 95 * mm, 40 * mm])
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

        primary_explanation = recommendations[0].get('explanation') or {}
        if primary_explanation.get('summary'):
            elements.append(Spacer(1, 2 * mm))
            elements.append(Paragraph(
                f"<b>Why this is suggested:</b> {_text(primary_explanation['summary'])}",
                styles['BodyText2'],
            ))
        if primary_explanation.get('limitations'):
            elements.append(Paragraph(
                _text(primary_explanation['limitations']),
                styles['SmallGrey'],
            ))
        if primary_explanation.get('next_step'):
            elements.append(Paragraph(
                f"<b>Next step:</b> {_text(primary_explanation['next_step'])}",
                styles['BodyText2'],
            ))

    # --- Provisional choice and learner plan ---
    choice = data.get('provisional_choice')
    elements.append(Paragraph('Provisional Combination', styles['SectionTitle']))
    if not choice:
        elements.append(Paragraph(
            'No provisional subject combination has been selected.',
            styles['BodyText2'],
        ))
    else:
        choice_rows = [
            ['Combination', f"{choice.get('code', '')} - {choice.get('title', '')}"],
            ['Pathway / track', f"{choice.get('pathway', '')} / {choice.get('track', '')}"],
            ['Subjects', ', '.join(choice.get('subjects', []))],
        ]
        choice_table = Table(choice_rows, colWidths=[40 * mm, 125 * mm])
        choice_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_GREEN),
            ('TEXTCOLOR', (0, 0), (0, -1), BRAND_GREEN),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(choice_table)
        if choice.get('learner_reason'):
            elements.append(Paragraph(
                f"<b>Learner reason:</b> {_text(choice['learner_reason'])}",
                styles['BodyText2'],
            ))

    plan = data.get('plan')
    elements.append(Paragraph('Plan Milestones', styles['SectionTitle']))
    if not plan:
        elements.append(Paragraph('No learner plan has been created.', styles['BodyText2']))
    else:
        status_label = str(plan.get('review_status', 'draft')).replace('_', ' ').title()
        elements.append(Paragraph(
            f"<b>Review status:</b> {_text(status_label)}",
            styles['BodyText2'],
        ))
        if plan.get('learner_reason'):
            elements.append(Paragraph(
                f"<b>Plan rationale:</b> {_text(plan['learner_reason'])}",
                styles['BodyText2'],
            ))
        milestones = plan.get('milestones', [])
        if milestones:
            milestone_rows = [['Milestone', 'Due date', 'Status']]
            for milestone in milestones:
                milestone_rows.append([
                    milestone.get('title', ''),
                    milestone.get('due_date') or 'No due date',
                    'Complete' if milestone.get('is_complete') else 'Open',
                ])
            milestone_table = Table(
                milestone_rows,
                colWidths=[95 * mm, 35 * mm, 30 * mm],
            )
            milestone_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GREEN),
                ('TEXTCOLOR', (0, 0), (-1, 0), BRAND_GREEN),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(milestone_table)
        else:
            elements.append(Paragraph('No milestones added yet.', styles['BodyText2']))

    # --- Version and source provenance ---
    framework = data.get('framework') or {}
    elements.append(Paragraph('Report Provenance', styles['SectionTitle']))
    provenance_rows = [
        ['Framework', f"{framework.get('code') or 'Not available'} - {framework.get('title') or 'Not available'}"],
        ['Framework effective date', framework.get('effective_date') or 'Not available'],
        ['Framework source', framework.get('source_url') or 'Not available'],
        ['RIASEC instrument', data.get('instrument_version') or 'Not available'],
        ['Recommendation algorithm', data.get('algorithm_version') or 'Not available'],
    ]
    provenance_table = Table(provenance_rows, colWidths=[45 * mm, 120 * mm])
    provenance_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (0, -1), TEXT_SECONDARY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(provenance_table)
    elements.append(Spacer(1, 8 * mm))

    # --- Footer disclaimer ---
    elements.append(footer_disclaimer(
        'Generated by Smarta Shauri. This report is advisory only and does not '
        'predict success or determine placement. It does not submit official Senior '
        'School choices or constitute an official academic record.',
        styles,
    ))

    doc.build(elements)
    return buf.getvalue()
