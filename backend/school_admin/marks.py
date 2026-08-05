import csv
import io
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsEmailVerified, IsSchoolAdmin
from accounts.response import _error, _success
from students.evidence import transition_grade_verification
from students.models import AcademicPeriod, CBCGrade, StudentSubject
from students.periods import ENTRY_CLOSED_MESSAGE, serialize_academic_period
from system_admin.utils import log_action

from .reporting import active_school_profiles


MARKS_IMPORT_HEADERS = {'student_email', 'subject_code', 'level'}
MARKS_IMPORT_OPTIONAL_HEADERS = {'raw_score'}
MARKS_IMPORT_MAX_ROWS = 1000
MARKS_IMPORT_MAX_BYTES = 2 * 1024 * 1024
VALID_LEVELS = {choice[0] for choice in CBCGrade._meta.get_field('level').choices}


def _school_for(request):
    school = request.user.school
    if school is None:
        return None, _error(
            'No school assigned to your account.',
            status.HTTP_404_NOT_FOUND,
        )
    if not school.is_active:
        return None, _error('Your school is inactive.', status.HTTP_403_FORBIDDEN)
    return school, None


def _decode_csv(upload):
    if upload.size > MARKS_IMPORT_MAX_BYTES:
        raise ValueError('The marks CSV must be 2 MB or smaller.')
    if not upload.name.lower().endswith('.csv'):
        raise ValueError('Upload a CSV file.')
    try:
        return upload.read().decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('The marks CSV must use UTF-8 encoding.') from exc


def _raw_score(value):
    value = (value or '').strip()
    if not value:
        return None
    try:
        score = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('raw_score must be a number or blank') from exc
    try:
        return CBCGrade._meta.get_field('raw_score').clean(score, None)
    except ValidationError as exc:
        raise ValueError('; '.join(exc.messages)) from exc


def _parse_marks(upload, *, school, period):
    text = _decode_csv(upload)
    reader = csv.DictReader(io.StringIO(text))
    headers = set(reader.fieldnames or [])
    missing = MARKS_IMPORT_HEADERS - headers
    unexpected = headers - MARKS_IMPORT_HEADERS - MARKS_IMPORT_OPTIONAL_HEADERS
    if missing:
        raise ValueError(
            'Missing required columns: ' + ', '.join(sorted(missing)) + '.'
        )
    if unexpected:
        raise ValueError('Unexpected columns: ' + ', '.join(sorted(unexpected)) + '.')

    source_rows = list(reader)
    if not source_rows:
        raise ValueError('The marks CSV has no data rows.')
    if len(source_rows) > MARKS_IMPORT_MAX_ROWS:
        raise ValueError(f'Upload at most {MARKS_IMPORT_MAX_ROWS} marks at once.')

    profiles = {
        profile.user.email.lower(): profile
        for profile in active_school_profiles(school).select_related('user')
    }
    enrollments = {
        (enrollment.student_profile_id, enrollment.subject.code.lower()): enrollment
        for enrollment in StudentSubject.objects.filter(
            student_profile__in=profiles.values(),
            is_active=True,
            academic_year=period.year,
        ).select_related('subject')
    }
    existing = {
        grade.student_subject_id: grade
        for grade in CBCGrade.objects.filter(
            student_subject__in=enrollments.values(),
            year=period.year,
            term=period.term,
        )
    }

    rows = []
    seen = set()
    valid_rows = []
    for index, row in enumerate(source_rows, start=2):
        email = (row.get('student_email') or '').strip().lower()
        subject_code = (row.get('subject_code') or '').strip()
        level = (row.get('level') or '').strip().upper()
        public = {
            'row': index,
            'student_email': email,
            'subject_code': subject_code,
            'level': level,
        }
        errors = []
        profile = profiles.get(email)
        if not email:
            errors.append('student_email is required')
        elif profile is None:
            errors.append('student is not actively linked to this school')
        if not subject_code:
            errors.append('subject_code is required')
        enrollment = (
            enrollments.get((profile.id, subject_code.lower()))
            if profile is not None and subject_code
            else None
        )
        if profile is not None and subject_code and enrollment is None:
            errors.append('student is not enrolled in this subject for this year')
        if level not in VALID_LEVELS:
            errors.append('level must be EE1, EE2, ME1, ME2, AE1, AE2, BE1, or BE2')
        try:
            raw_score = _raw_score(row.get('raw_score'))
        except ValueError as exc:
            raw_score = None
            errors.append(str(exc))

        identity = (email, subject_code.lower())
        if identity in seen:
            errors.append('duplicate student and subject in this file')
        seen.add(identity)

        grade = existing.get(enrollment.id) if enrollment is not None else None
        if grade is not None and any((
            grade.verified_by_id,
            grade.verified_at,
            grade.verified_school_id,
        )):
            errors.append('this term result is already finalized')

        if errors:
            public.update(action='error', errors=errors)
        else:
            action = 'replace_learner_entry' if grade is not None else 'create'
            public.update(
                action=action,
                errors=[],
                raw_score=str(raw_score) if raw_score is not None else None,
            )
            valid_rows.append({
                'enrollment': enrollment,
                'grade': grade,
                'level': level,
                'raw_score': raw_score,
                'public': public,
            })
        rows.append(public)

    error_count = sum(row['action'] == 'error' for row in rows)
    return {
        'period': serialize_academic_period(period),
        'row_count': len(rows),
        'valid_count': len(rows) - error_count,
        'error_count': error_count,
        'rows': rows,
    }, valid_rows


class SchoolAcademicPeriodListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def get(self, request):
        _, error = _school_for(request)
        if error:
            return error
        return _success(
            data=[
                serialize_academic_period(period)
                for period in AcademicPeriod.objects.all()
            ]
        )


class SchoolMarksImportView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request):
        school, error = _school_for(request)
        if error:
            return error
        upload = request.FILES.get('file')
        if upload is None:
            return _error('Choose a marks CSV file.')
        try:
            period_id = int(request.data.get('period_id', ''))
        except (TypeError, ValueError):
            return _error('Choose an academic period.')
        preview_value = str(request.data.get('preview', 'true')).lower()
        if preview_value not in {'true', 'false'}:
            return _error('preview must be true or false.')
        preview = preview_value == 'true'

        try:
            period = AcademicPeriod.objects.get(pk=period_id)
        except AcademicPeriod.DoesNotExist:
            return _error('Academic period not found.', status.HTTP_404_NOT_FOUND)
        if not period.accepts_entries():
            return _error(ENTRY_CLOSED_MESSAGE, status.HTTP_409_CONFLICT)

        try:
            result, valid_rows = _parse_marks(
                upload,
                school=school,
                period=period,
            )
        except ValueError as exc:
            return _error(str(exc))

        if preview:
            return _success(data=result, message='Marks file checked.')
        if result['error_count']:
            return _error(result)

        created_count = 0
        replaced_count = 0
        try:
            with transaction.atomic():
                locked_period = AcademicPeriod.objects.select_for_update().get(
                    pk=period.pk
                )
                if not locked_period.accepts_entries():
                    return _error(ENTRY_CLOSED_MESSAGE, status.HTTP_409_CONFLICT)
                for row in valid_rows:
                    enrollment = row['enrollment']
                    grade = row['grade']
                    if grade is None:
                        grade = CBCGrade(
                            student_subject=enrollment,
                            academic_grade=enrollment.academic_grade,
                            year=period.year,
                            term=period.term,
                            level=row['level'],
                            raw_score=row['raw_score'],
                            source='school',
                        )
                        grade.save()
                        created_count += 1
                    else:
                        grade = CBCGrade.objects.select_for_update().get(pk=grade.pk)
                        if any((grade.verified_by_id, grade.verified_at, grade.verified_school_id)):
                            raise ValidationError('A result was finalized while the file was being checked.')
                        grade.level = row['level']
                        grade.raw_score = row['raw_score']
                        grade.source = 'school'
                        grade.save(update_fields=['level', 'raw_score', 'source', 'updated_at'])
                        replaced_count += 1
                    transition_grade_verification(
                        grade,
                        actor=request.user,
                        school=school,
                        should_verify=True,
                    )
        except (IntegrityError, ValidationError) as exc:
            return _error(str(exc), status.HTTP_409_CONFLICT)

        result.update(
            created_count=created_count,
            replaced_count=replaced_count,
        )
        log_action(
            actor=request.user,
            action='school_marks_imported',
            target_type='period',
            target_id=period.id,
            details={
                'school_id': school.id,
                'year': period.year,
                'term': period.term,
                'created_count': created_count,
                'replaced_count': replaced_count,
            },
            request=request,
        )
        return _success(
            data=result,
            message='School marks imported and verified.',
            status_code=status.HTTP_201_CREATED,
        )
