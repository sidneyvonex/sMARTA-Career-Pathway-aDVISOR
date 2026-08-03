import io
import os
from datetime import date
from xml.sax.saxutils import escape

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


def _text(value):
    return escape(str(value or ''))


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
        f'Generated on {_text(data.get("generated_at") or date.today().strftime("%d %B %Y"))}',
        styles['SmallGrey'],
    ))
    elements.append(Spacer(1, 4 * mm))

    # --- Deterministic academic progress ---
    progress = data.get('academic_progress') or {}
    elements.append(Paragraph('Academic Progress', styles['SectionTitle']))
    overall = progress.get('overall') or {}
    elements.append(Paragraph(
        f"<b>Overall support status:</b> {_text(overall.get('label') or 'Insufficient evidence')}",
        styles['BodyText2'],
    ))
    progress_subjects = progress.get('subjects') or []
    if not progress_subjects:
        elements.append(Paragraph(
            'No active subject progress can be derived yet.',
            styles['BodyText2'],
        ))
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
    elements.append(Paragraph(
        'Generated by Smarta Shauri. This report is advisory only and does not '
        'predict success or determine placement. It does not submit official Senior '
        'School choices or constitute an official academic record.',
        styles['SmallGrey'],
    ))

    doc.build(elements)
    return buf.getvalue()
