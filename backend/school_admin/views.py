import csv
import io
from io import BytesIO
from PIL import Image
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Count, Exists, F, OuterRef, Prefetch, Q
from django.db.models.functions import Lower
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsSchoolAdmin, IsEmailVerified
from accounts.utils import _temporary_password
from accounts.models import (
    School,
    User,
    StudentProfile,
    StudentSchoolMembership,
)
from accounts.response import _success, _error
from counselors.models import CounselorAssignment
from riasec.models import RIASECAssessment
from system_admin.utils import log_action
from guidance.models import FrameworkVersion, SchoolOffering, SubjectCombination
from guidance.selectors import active_combination_queryset
from guidance.serializers import (
    SchoolOfferingReplaceSerializer,
    SchoolSummarySerializer,
    SubjectCombinationSerializer,
)
from students.evidence import transition_grade_verification
from students.models import CBCGrade, StudentSubject
from students.serializers import CBCGradeSerializer
from system_admin.models import AuditLog
from notifications.models import Notification
from .reporting import get_school_stats


SCHOOL_EDITABLE_FIELDS = {'name', 'phone', 'email'}
STUDENT_IMPORT_HEADERS = {'first_name', 'last_name', 'email', 'grade'}
STUDENT_IMPORT_MAX_ROWS = 500
STUDENT_IMPORT_MAX_BYTES = 1024 * 1024


class SchoolOfferingsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def _get_school(self, request):
        school = request.user.school
        if school is None:
            return None, _error(
                'No school assigned to your account.',
                status.HTTP_404_NOT_FOUND,
            )
        if not school.is_active:
            return None, _error(
                'Your school is inactive.',
                status.HTTP_403_FORBIDDEN,
            )
        return school, None

    def _response_data(self, school):
        framework = FrameworkVersion.objects.current()
        if framework is None:
            combinations = SubjectCombination.objects.none()
        else:
            combinations = (
                  active_combination_queryset(
                      framework,
                      include_unverified_offerings=True,
                  )
                .filter(
                    school_offerings__school=school,
                    school_offerings__is_active=True,
                )
                .distinct()
            )
        combination_list = list(combinations)
        return {
            'school': SchoolSummarySerializer(school).data,
            'combination_ids': [
                combination.id for combination in combination_list
            ],
            'offerings': SubjectCombinationSerializer(
                combination_list,
                many=True,
            ).data,
        }

    def get(self, request):
        school, error = self._get_school(request)
        if error:
            return error
        return _success(data=self._response_data(school))

    def put(self, request):
        school, error = self._get_school(request)
        if error:
            return error

        serializer = SchoolOfferingReplaceSerializer(data=request.data)
        if not serializer.is_valid():
            return _error(serializer.errors)
        combination_ids = serializer.validated_data['combination_ids']

        framework = FrameworkVersion.objects.current()
        if framework is None:
            return _error(
                'No active guidance framework found.',
                status.HTTP_409_CONFLICT,
            )

        eligible_ids = set(
            SubjectCombination.objects.filter(
                pk__in=combination_ids,
                framework_version=framework,
                is_active=True,
                track__is_active=True,
            ).values_list('pk', flat=True)
        )
        if eligible_ids != set(combination_ids):
            return _error(
                'Only active combinations from the current guidance framework '
                'can be selected.'
            )

        with transaction.atomic():
            School.objects.select_for_update().get(pk=school.pk)
            previous_ids = sorted(
                SchoolOffering.objects.filter(school=school).values_list(
                    'combination_id',
                    flat=True,
                )
            )
            SchoolOffering.objects.filter(school=school).delete()
            SchoolOffering.objects.bulk_create(
                [
                    SchoolOffering(
                        school=school,
                        combination_id=combination_id,
                        is_active=True,
                    )
                    for combination_id in combination_ids
                ]
            )
            updated_ids = sorted(combination_ids)
            if previous_ids != updated_ids:
                log_action(
                    actor=request.user,
                    action='school_offerings_changed',
                    target_type='offering',
                    target_id=school.id,
                    details={
                        'school_id': school.id,
                        'previous_combination_ids': previous_ids,
                        'combination_ids': updated_ids,
                    },
                    request=request,
                )

        return _success(
            data=self._response_data(school),
            message='School offerings updated.',
        )


class SchoolGradeVerificationView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def put(self, request, student_id, grade_id):
        school = request.user.school
        if school is None:
            return _error(
                'No school assigned to your account.',
                status.HTTP_404_NOT_FOUND,
            )
        if not school.is_active:
            return _error('Your school is inactive.', status.HTTP_403_FORBIDDEN)
        if (
            'verified' not in request.data
            or type(request.data['verified']) is not bool
        ):
            return _error('verified must be a boolean.')
        should_verify = request.data['verified']

        with transaction.atomic():
            try:
                profile = (
                    StudentProfile.objects.select_for_update()
                    .get(user_id=student_id)
                )
            except StudentProfile.DoesNotExist:
                return _error(
                    'Grade not found for an active learner at your school.',
                    status.HTTP_404_NOT_FOUND,
                )

            membership_history = list(
                StudentSchoolMembership.objects.select_for_update().filter(
                    student_profile=profile,
                )
            )
            if membership_history:
                has_active_membership = any(
                    membership.school_id == school.id
                    and membership.status
                    == StudentSchoolMembership.STATUS_ACTIVE
                    for membership in membership_history
                )
            else:
                has_active_membership = (
                    profile.school_id == school.id
                    and profile.mode == 'school_linked'
                    and profile.school_membership_status == 'active'
                )
            if not has_active_membership:
                return _error(
                    'Grade not found for an active learner at your school.',
                    status.HTTP_404_NOT_FOUND,
                )

            try:
                grade = (
                    CBCGrade.objects.select_for_update()
                    .select_related(
                        'student_subject__student_profile',
                        'student_subject__subject',
                    )
                    .get(
                        pk=grade_id,
                        student_subject__student_profile=profile,
                        student_subject__is_active=True,
                    )
                )
            except CBCGrade.DoesNotExist:
                return _error(
                    'Grade not found for an active learner at your school.',
                    status.HTTP_404_NOT_FOUND,
                )

            if (
                grade.verified_school_id is not None
                and grade.verified_school_id != school.id
            ) or (
                grade.verified_at is not None
                and grade.verified_school_id is None
            ):
                return _error(
                    "You don't have permission to change this verification.",
                    status.HTTP_403_FORBIDDEN,
                )

            is_verified = grade.verified_at is not None
            verifier_changed = (
                should_verify
                and is_verified
                and grade.verified_by_id != request.user.id
            )
            changed = should_verify != is_verified or verifier_changed
            if changed:
                if should_verify:
                    action = 'grade_verified'
                else:
                    action = 'grade_verification_removed'
                transition_grade_verification(
                    grade,
                    actor=request.user,
                    school=school,
                    should_verify=should_verify,
                )

                forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
                ip_address = (
                    forwarded.split(',')[0].strip()
                    if forwarded
                    else request.META.get('REMOTE_ADDR')
                )
                AuditLog.objects.create(
                    actor=request.user,
                    action=action,
                    target_type='grade',
                    target_id=grade.id,
                    details={
                        'student_id': student_id,
                        'school_id': school.id,
                        'source': grade.source,
                    },
                    ip_address=ip_address,
                )
                Notification.objects.create(
                    user=profile.user,
                    type='grade_verification_changed',
                    message=(
                        f'{grade.student_subject.subject.name} evidence was '
                        f'{"verified" if should_verify else "unverified"} by '
                        f'{school.name}.'
                    ),
                )

        return _success(
            data=CBCGradeSerializer(grade).data,
            message=(
                'Grade verified.'
                if should_verify
                else 'Grade verification removed.'
            ),
        )


class SchoolProfileView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def _get_school(self, user):
        if not user.school:
            return None
        return user.school

    def _serialize(self, school):
        student_count = school.studentprofile_set.filter(
            mode='school_linked',
            school_membership_status='active',
        ).count()
        counselor_count = User.objects.filter(school=school, role='counselor').count()
        return {
            'id': school.id,
            'name': school.name,
            'county': school.county,
            'school_code': school.school_code,
            'logo_url': school.logo_url,
            'phone': school.phone,
            'email': school.email,
            'student_count': student_count,
            'counselor_count': counselor_count,
        }

    def get(self, request):
        school = self._get_school(request.user)
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)
        return _success(data=self._serialize(school))

    def patch(self, request):
        school = self._get_school(request.user)
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)
        updated = []
        for field in SCHOOL_EDITABLE_FIELDS:
            if field in request.data:
                value = request.data[field]
                if not isinstance(value, str):
                    return _error(f'{field} must be a string.')
                setattr(school, field, value.strip())
                updated.append(field)
        if updated:
            try:
                school.full_clean(exclude=['county', 'school_code'])
            except ValidationError as e:
                messages = []
                for field_errors in e.message_dict.values():
                    messages.extend(field_errors)
                return _error(messages[0] if messages else 'Invalid data.')
            school.save(update_fields=updated)
        return _success(data=self._serialize(school), message='School profile updated.')


MAX_LOGO_SIZE = 5 * 1024 * 1024
MAX_LOGO_DIM = 1000
ALLOWED_FORMATS = {'JPEG', 'PNG'}
FORMAT_TO_EXT = {'JPEG': 'jpg', 'PNG': 'png'}


class SchoolLogoUploadView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        logo = request.FILES.get('logo')
        if not logo:
            return _error('No logo file provided.')
        if logo.size > MAX_LOGO_SIZE:
            return _error('Logo must be 5MB or less.')

        file_bytes = logo.read()
        try:
            img = Image.open(BytesIO(file_bytes))
            img.verify()
            img = Image.open(BytesIO(file_bytes))
            fmt = img.format
        except Exception:
            return _error('Invalid image file.')

        if fmt not in ALLOWED_FORMATS:
            return _error('Only JPEG and PNG images are allowed.')

        try:
            if img.width > MAX_LOGO_DIM or img.height > MAX_LOGO_DIM:
                img.thumbnail((MAX_LOGO_DIM, MAX_LOGO_DIM), Image.LANCZOS)
            output = BytesIO()
            if fmt == 'JPEG' and img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output, format=fmt)
            output.seek(0)
        except Exception:
            return _error('Invalid image file.')

        self._delete_old_logo(school)

        ext = FORMAT_TO_EXT[fmt]
        filename = f'school-logos/school_{school.id}.{ext}'
        saved_path = default_storage.save(filename, ContentFile(output.read()))
        logo_url = default_storage.url(saved_path)

        school.logo_url = logo_url
        school.save(update_fields=['logo_url'])
        return _success(data={'logo_url': logo_url}, message='School logo updated.')

    def _delete_old_logo(self, school):
        if not school.logo_url:
            return
        for ext in FORMAT_TO_EXT.values():
            path = f'school-logos/school_{school.id}.{ext}'
            if default_storage.exists(path):
                default_storage.delete(path)


class SchoolLogoRemoveView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)
        for ext in FORMAT_TO_EXT.values():
            path = f'school-logos/school_{school.id}.{ext}'
            if default_storage.exists(path):
                default_storage.delete(path)
        school.logo_url = None
        school.save(update_fields=['logo_url'])
        return _success(message='Logo removed.')


class SchoolCounselorsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def get(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        counselors = (
            User.objects.filter(school=school, role='counselor')
            .annotate(
                student_count=Count(
                    'student_assignments',
                    filter=Q(student_assignments__is_active=True),
                )
            )
            .order_by('first_name', 'last_name')
        )

        data = [
            {
                'id': c.id,
                'first_name': c.first_name,
                'last_name': c.last_name,
                'email': c.email,
                'student_count': c.student_count,
                'joined_at': c.created_at.isoformat(),
            }
            for c in counselors
        ]
        return _success(data=data)


class SchoolCounselorAddView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        email = request.data.get('email', '').lower().strip()
        if not email:
            return _error('Email is required.')

        try:
            counselor = User.objects.get(email=email, role='counselor')
        except User.DoesNotExist:
            return _error('No counselor found with that email.', status.HTTP_404_NOT_FOUND)

        if counselor.school is not None:
            return _error('This counselor is already assigned to a school.')
        counselor.school = school
        counselor.save(update_fields=['school'])
        log_action(
            actor=request.user, action='counselor_added', target_type='user',
            target_id=counselor.id,
            details={'school_id': school.id, 'school_name': school.name},
            request=request,
        )
        return _success(
            data={'id': counselor.id, 'email': counselor.email},
            message=f'{counselor.first_name} {counselor.last_name} added to {school.name}.',
        )


class SchoolCounselorRemoveView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request, counselor_id):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        try:
            counselor = User.objects.get(pk=counselor_id, role='counselor', school=school)
        except User.DoesNotExist:
            return _error('Counselor not found at your school.', status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            CounselorAssignment.objects.filter(
                counselor=counselor, school=school, is_active=True,
            ).update(is_active=False)

            counselor.school = None
            counselor.save(update_fields=['school'])
        log_action(
            actor=request.user, action='counselor_removed', target_type='user',
            target_id=counselor.id,
            details={'school_id': school.id, 'school_name': school.name},
            request=request,
        )
        return _success(message=f'{counselor.first_name} {counselor.last_name} removed from {school.name}.')


class SchoolStudentsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def get(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        has_assessment = RIASECAssessment.objects.filter(student_profile=OuterRef('pk'))
        membership_history = StudentSchoolMembership.objects.filter(
            student_profile=OuterRef('pk')
        )
        active_school_membership = membership_history.filter(
            school=school,
            status=StudentSchoolMembership.STATUS_ACTIVE,
        )

        profiles = (
            StudentProfile.objects
            .select_related('user', 'school')
            .annotate(
                has_assessment=Exists(has_assessment),
                has_membership_history=Exists(membership_history),
                has_active_school_membership=Exists(active_school_membership),
            )
            .filter(
                Q(has_active_school_membership=True)
                | Q(
                    has_membership_history=False,
                    school=school,
                    mode='school_linked',
                    school_membership_status='active',
                )
            )
            .prefetch_related(
                Prefetch(
                    'counselor_assignments',
                    queryset=CounselorAssignment.objects.filter(is_active=True).select_related('counselor'),
                ),
                Prefetch(
                    'school_memberships',
                    queryset=StudentSchoolMembership.objects.select_related('school'),
                    to_attr='admin_memberships',
                ),
                Prefetch(
                    'enrolled_subjects',
                    queryset=StudentSubject.objects.select_related('subject').prefetch_related(
                        Prefetch(
                            'grades',
                            queryset=CBCGrade.objects.select_related(
                                'framework', 'verified_school'
                            ).order_by(
                                'academic_grade', 'year', 'term', 'created_at', 'pk'
                            ),
                        )
                    ),
                    to_attr='admin_enrollments',
                ),
            )
            .order_by('user__first_name', 'user__last_name')
        )

        data = []
        for p in profiles:
            active_assignment = None
            for a in p.counselor_assignments.all():
                if a.is_active:
                    active_assignment = a
                    break

            memberships = list(getattr(p, 'admin_memberships', []))
            current_membership = next(
                (
                    membership for membership in memberships
                    if membership.school_id == school.id
                    and membership.status in {
                        StudentSchoolMembership.STATUS_ACTIVE,
                        StudentSchoolMembership.STATUS_PENDING,
                    }
                ),
                None,
            )
            if memberships:
                authoritative_membership_status = (
                    current_membership.status
                    if current_membership is not None
                    else StudentSchoolMembership.STATUS_ENDED
                )
                authoritative_school = (
                    current_membership.school
                    if current_membership is not None
                    else None
                )
            else:
                authoritative_membership_status = p.school_membership_status
                authoritative_school = p.school
            has_active_membership = (
                authoritative_membership_status
                == StudentSchoolMembership.STATUS_ACTIVE
            )
            academic_evidence = []
            if has_active_membership:
                for enrollment in getattr(p, 'admin_enrollments', []):
                    for grade in enrollment.grades.all():
                        verified = grade.verified_at is not None
                        academic_evidence.append({
                            'id': grade.id,
                            'continuity_code': enrollment.continuity_code,
                            'subject_name': enrollment.subject.name,
                            'academic_grade': grade.academic_grade,
                            'term': grade.term,
                            'year': grade.year,
                            'level': grade.level,
                            'framework': {
                                'code': grade.framework.code,
                                'version': grade.framework.version,
                            },
                            'source': grade.source,
                            'verified_school': (
                                {
                                    'id': grade.verified_school_id,
                                    'name': grade.verified_school.name,
                                }
                                if grade.verified_school_id is not None
                                else None
                            ),
                            'verified_at': (
                                grade.verified_at.isoformat()
                                if grade.verified_at is not None
                                else None
                            ),
                            'can_verify': (
                                enrollment.is_active
                                and not verified
                                and (
                                    grade.verified_school_id is None
                                    or grade.verified_school_id == school.id
                                )
                            ),
                            'can_remove_verification': (
                                enrollment.is_active
                                and verified
                                and grade.verified_school_id == school.id
                            ),
                        })

            data.append({
                'id': p.user.id,
                'first_name': p.user.first_name,
                'last_name': p.user.last_name,
                'email': p.user.email,
                'grade': p.grade,
                'photo_url': p.photo_url,
                'quiz_status': 'done' if p.has_assessment else 'pending',
                'school_membership_status': authoritative_membership_status,
                'school': (
                    {
                        'id': authoritative_school.id,
                        'name': authoritative_school.name,
                    }
                    if authoritative_school is not None
                    else None
                ),
                'counselor_id': active_assignment.counselor_id if active_assignment else None,
                'counselor_name': (
                    f'{active_assignment.counselor.first_name} {active_assignment.counselor.last_name}'
                    if active_assignment else None
                ),
                'membership': (
                    {
                        'id': current_membership.id,
                        'status': current_membership.status,
                        'record_source': current_membership.record_source,
                        'requested_at': current_membership.requested_at.isoformat()
                        if current_membership.requested_at else None,
                        'started_at': current_membership.started_at.isoformat()
                        if current_membership.started_at else None,
                        'ended_at': current_membership.ended_at.isoformat()
                        if current_membership.ended_at else None,
                    }
                    if current_membership is not None
                    else None
                ),
                'transfer': {
                    'previous_membership_count': sum(
                        membership.status == StudentSchoolMembership.STATUS_ENDED
                        for membership in memberships
                    ) if has_active_membership else 0,
                },
                'academic_evidence': academic_evidence,
            })
        return _success(data=data)


class SchoolStudentImportView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request):
        school = request.user.school
        if not school:
            return _error(
                'No school assigned to your account.',
                status.HTTP_404_NOT_FOUND,
            )
        if not school.is_active:
            return _error('Your school is inactive.', status.HTTP_403_FORBIDDEN)

        upload = request.FILES.get('file')
        if upload is None:
            return _error('Choose a CSV file to import.')
        if upload.size > STUDENT_IMPORT_MAX_BYTES:
            return _error('The CSV file must be 1 MB or smaller.')
        if not upload.name.lower().endswith('.csv'):
            return _error('The uploaded file must use the .csv extension.')

        try:
            content = upload.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            return _error('The CSV file must be UTF-8 encoded.')

        try:
            reader = csv.DictReader(io.StringIO(content))
            headers = {
                (header or '').strip().lower()
                for header in (reader.fieldnames or [])
            }
            if not STUDENT_IMPORT_HEADERS.issubset(headers):
                missing = sorted(STUDENT_IMPORT_HEADERS - headers)
                return _error(
                    'Missing required CSV column(s): ' + ', '.join(missing) + '.'
                )
            rows = list(reader)
        except csv.Error:
            return _error('The CSV file could not be read.')

        if not rows:
            return _error('The CSV file has no learner rows.')
        if len(rows) > STUDENT_IMPORT_MAX_ROWS:
            return _error(
                f'A CSV file can contain at most {STUDENT_IMPORT_MAX_ROWS} learners.'
            )

        normalized_rows = []
        errors = []
        seen_emails = set()
        for row_number, raw_row in enumerate(rows, start=2):
            row = {
                str(key).strip().lower(): (value or '').strip()
                for key, value in raw_row.items()
                if key is not None
            }
            first_name = row.get('first_name', '')
            last_name = row.get('last_name', '')
            email = row.get('email', '').lower()
            grade_value = row.get('grade', '')
            row_errors = []
            if not first_name:
                row_errors.append('first_name is required')
            if not last_name:
                row_errors.append('last_name is required')
            try:
                validate_email(email)
            except ValidationError:
                row_errors.append('email is invalid')
            try:
                grade = int(grade_value)
                if grade not in dict(StudentProfile.GRADE_CHOICES):
                    raise ValueError
            except (TypeError, ValueError):
                grade = None
                row_errors.append('grade must be 9, 10, 11, or 12')
            if email in seen_emails:
                row_errors.append('email is repeated in this file')
            seen_emails.add(email)

            if row_errors:
                errors.append({
                    'row': row_number,
                    'email': email,
                    'message': '; '.join(row_errors),
                })
            else:
                normalized_rows.append({
                    'row': row_number,
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'grade': grade,
                })

        existing_users = {
            user.normalized_email: user.id
            for user in User.objects.annotate(normalized_email=Lower('email'))
            .filter(
                normalized_email__in=[row['email'] for row in normalized_rows]
            )
        }

        created = []
        linked = []
        already_linked = []
        for row in normalized_rows:
            existing_user_id = existing_users.get(row['email'])
            if existing_user_id is not None:
                outcome, detail = self._link_existing_student(
                    request=request,
                    school=school,
                    row=row,
                    user_id=existing_user_id,
                )
                if outcome == 'linked':
                    linked.append(detail)
                elif outcome == 'already_linked':
                    already_linked.append(detail)
                else:
                    errors.append({
                        'row': row['row'],
                        'email': row['email'],
                        'message': detail,
                    })
                continue

            password = _temporary_password()
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        email=row['email'],
                        password=password,
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        role='student',
                        county=school.county,
                        is_email_verified=True,
                    )
                    profile = StudentProfile.objects.create(
                        user=user,
                        mode='school_linked',
                        school=school,
                        school_membership_status='active',
                        grade=row['grade'],
                    )
                    StudentSchoolMembership.objects.create(
                        student_profile=profile,
                        school=school,
                        status=StudentSchoolMembership.STATUS_ACTIVE,
                        record_source=StudentSchoolMembership.SOURCE_ADMIN_IMPORT,
                        decided_by=request.user,
                        decided_at=timezone.now(),
                        started_at=timezone.now(),
                    )
            except IntegrityError:
                errors.append({
                    'row': row['row'],
                    'email': row['email'],
                    'message': 'an account with this email already exists',
                })
                continue

            created.append({
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'grade': profile.grade,
                'temporary_password': password,
            })

        if created or linked:
            log_action(
                actor=request.user,
                action='students_bulk_imported',
                target_type='school',
                target_id=school.id,
                details={
                    'school_id': school.id,
                    'created_count': len(created),
                    'linked_count': len(linked),
                    'already_linked_count': len(already_linked),
                    'error_count': len(errors),
                },
                request=request,
            )

        response = _success(
            data={
                'created_count': len(created),
                'linked_count': len(linked),
                'already_linked_count': len(already_linked),
                'error_count': len(errors),
                'created': created,
                'linked': linked,
                'already_linked': already_linked,
                'errors': sorted(errors, key=lambda error: error['row']),
            },
            message=(
                f'{len(created) + len(linked)} learner'
                f'{"s" if len(created) + len(linked) != 1 else ""} added '
                f'to {school.name}.'
            ),
            status_code=(
                status.HTTP_201_CREATED
                if created or linked
                else status.HTTP_200_OK
            ),
        )
        response['Cache-Control'] = 'no-store'
        return response

    def _link_existing_student(self, *, request, school, row, user_id):
        """Link a safe existing learner account without changing its password."""
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user_id)
            if user.role != 'student':
                return (
                    'error',
                    f'this email belongs to a {user.get_role_display()} account',
                )
            if not user.is_active:
                return (
                    'error',
                    'this learner account is deactivated; contact a system administrator',
                )
            if not user.is_email_verified:
                user.is_email_verified = True
                user.save(update_fields=['is_email_verified'])

            try:
                profile = (
                    StudentProfile.objects.select_for_update()
                    .get(user=user)
                )
            except StudentProfile.DoesNotExist:
                profile = StudentProfile.objects.create(
                    user=user,
                    mode='school_linked',
                    school=school,
                    school_membership_status='active',
                    grade=row['grade'],
                )
                StudentSchoolMembership.objects.create(
                    student_profile=profile,
                    school=school,
                    status=StudentSchoolMembership.STATUS_ACTIVE,
                    record_source=StudentSchoolMembership.SOURCE_ADMIN_IMPORT,
                    decided_by=request.user,
                    decided_at=timezone.now(),
                    started_at=timezone.now(),
                )
                return 'linked', self._existing_student_result(user, profile)

            memberships = StudentSchoolMembership.objects.select_for_update().filter(
                student_profile=profile,
            )
            active_membership = memberships.filter(
                status=StudentSchoolMembership.STATUS_ACTIVE,
            ).select_related('school').first()
            if active_membership is not None:
                if active_membership.school_id != school.id:
                    return (
                        'error',
                        f'learner is actively linked to {active_membership.school.name}; '
                        'use the school-transfer approval workflow',
                    )
                return (
                    'already_linked',
                    self._existing_student_result(user, profile),
                )

            pending_elsewhere = memberships.filter(
                status=StudentSchoolMembership.STATUS_PENDING,
            ).exclude(school=school).select_related('school').first()
            if pending_elsewhere is not None:
                return (
                    'error',
                    f'learner has a pending link request with '
                    f'{pending_elsewhere.school.name}',
                )

            same_school_pending = memberships.filter(
                school=school,
                status=StudentSchoolMembership.STATUS_PENDING,
            ).first()
            if same_school_pending is not None:
                same_school_pending.activate(decided_by=request.user)
            else:
                StudentSchoolMembership.objects.create(
                    student_profile=profile,
                    school=school,
                    status=StudentSchoolMembership.STATUS_ACTIVE,
                    record_source=StudentSchoolMembership.SOURCE_ADMIN_IMPORT,
                    decided_by=request.user,
                    decided_at=timezone.now(),
                    started_at=timezone.now(),
                )

            profile.mode = 'school_linked'
            profile.school = school
            profile.school_membership_status = 'active'
            profile.grade = row['grade']
            profile.save(update_fields=[
                'mode',
                'school',
                'school_membership_status',
                'grade',
            ])
            return 'linked', self._existing_student_result(user, profile)

    @staticmethod
    def _existing_student_result(user, profile):
        return {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'grade': profile.grade,
        }


class SchoolMembershipRequestsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def get(self, request):
        school = request.user.school
        if not school:
            return _error(
                'No school assigned to your account.',
                status.HTTP_404_NOT_FOUND,
            )

        memberships = (
            StudentSchoolMembership.objects.filter(
                school=school,
                status=StudentSchoolMembership.STATUS_PENDING,
            )
            .select_related('student_profile__user')
            .order_by(
                'requested_at',
                'student_profile__user__first_name',
                'student_profile__user__last_name',
            )
        )
        data = [
            {
                'student_id': membership.student_profile.user_id,
                'first_name': membership.student_profile.user.first_name,
                'last_name': membership.student_profile.user.last_name,
                'email': membership.student_profile.user.email,
                'grade': membership.student_profile.grade,
                'requested_at': (
                    membership.requested_at.isoformat()
                    if membership.requested_at is not None
                    else None
                ),
            }
            for membership in memberships
        ]
        represented_profile_ids = {
            membership.student_profile_id for membership in memberships
        }
        legacy_profiles = (
            StudentProfile.objects.filter(
                school=school,
                mode='school_linked',
                school_membership_status='pending',
            )
            .exclude(pk__in=represented_profile_ids)
            .filter(school_memberships__isnull=True)
            .select_related('user')
            .order_by('created_at', 'user__first_name', 'user__last_name')
        )
        data.extend([
            {
                'student_id': profile.user_id,
                'first_name': profile.user.first_name,
                'last_name': profile.user.last_name,
                'email': profile.user.email,
                'grade': profile.grade,
                'requested_at': profile.created_at.isoformat(),
            }
            for profile in legacy_profiles
        ])
        return _success(data=data)


class SchoolMembershipDecisionView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def put(self, request, student_id):
        school = request.user.school
        if not school:
            return _error(
                'No school assigned to your account.',
                status.HTTP_404_NOT_FOUND,
            )

        decision = request.data.get('decision')
        if decision not in {'approve', 'reject'}:
            return _error('decision must be either approve or reject.')

        with transaction.atomic():
            try:
                profile = (
                    StudentProfile.objects.select_for_update()
                    .select_related('user')
                    .get(user_id=student_id)
                )
            except StudentProfile.DoesNotExist:
                return _error(
                    'Pending membership request not found.',
                    status.HTTP_404_NOT_FOUND,
                )

            try:
                membership = (
                    StudentSchoolMembership.objects.select_for_update()
                    .select_related('school')
                    .get(
                        student_profile=profile,
                        school=school,
                        status=StudentSchoolMembership.STATUS_PENDING,
                    )
                )
            except StudentSchoolMembership.DoesNotExist:
                is_legacy_pending = (
                    profile.school_id == school.id
                    and profile.mode == 'school_linked'
                    and profile.school_membership_status == 'pending'
                    and not profile.school_memberships.exists()
                )
                if not is_legacy_pending:
                    decided_exists = StudentSchoolMembership.objects.filter(
                        student_profile=profile,
                        school=school,
                    ).exists()
                    return _error(
                        (
                            'This membership request has already been decided.'
                            if decided_exists
                            else 'Pending membership request not found.'
                        ),
                        (
                            status.HTTP_409_CONFLICT
                            if decided_exists
                            else status.HTTP_404_NOT_FOUND
                        ),
                    )
                membership = StudentSchoolMembership.objects.create(
                    student_profile=profile,
                    school=school,
                    status=StudentSchoolMembership.STATUS_PENDING,
                    record_source=(
                        StudentSchoolMembership.SOURCE_LEGACY_BACKFILL
                    ),
                    requested_at=None,
                )

            active_membership = (
                StudentSchoolMembership.objects.select_for_update()
                .filter(
                    student_profile=profile,
                    status=StudentSchoolMembership.STATUS_ACTIVE,
                )
                .first()
            )
            previous_school_id = (
                active_membership.school_id if active_membership else None
            )
            if decision == 'approve':
                if active_membership is not None:
                    active_membership.end()
                membership.activate(decided_by=request.user)
                profile.mode = 'school_linked'
                profile.school = school
                profile.school_membership_status = 'active'
                profile.save(
                    update_fields=[
                        'mode',
                        'school',
                        'school_membership_status',
                    ]
                )
                if previous_school_id is not None:
                    CounselorAssignment.objects.filter(
                        student_profile=profile,
                        school_id=previous_school_id,
                        is_active=True,
                    ).update(is_active=False)
                membership_status = 'active'
            else:
                membership.reject(decided_by=request.user)
                if active_membership is None:
                    profile.mode = 'school_linked'
                    profile.school = school
                    profile.school_membership_status = 'rejected'
                    profile.save(
                        update_fields=[
                            'mode',
                            'school',
                            'school_membership_status',
                        ]
                    )
                membership_status = 'rejected'

            action = (
                'school_membership_approved'
                if decision == 'approve'
                else 'school_membership_rejected'
            )
            forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
            ip_address = (
                forwarded.split(',')[0].strip()
                if forwarded
                else request.META.get('REMOTE_ADDR')
            )
            AuditLog.objects.create(
                actor=request.user,
                action=action,
                target_type='user',
                target_id=profile.user_id,
                details={
                    'school_id': school.id,
                    'school_name': school.name,
                    'decision': decision,
                    'membership_id': membership.id,
                    'previous_school_id': previous_school_id,
                },
                ip_address=ip_address,
            )
            Notification.objects.create(
                user=profile.user,
                type=(
                    'school_transfer_decided'
                    if previous_school_id is not None
                    else 'school_membership_decided'
                ),
                message=(
                    f'Your school link to {school.name} is now '
                    f'{membership_status}.'
                ),
            )

        return _success(
            data={
                'student_id': profile.user_id,
                'school_membership_status': membership_status,
            },
            message=(
                'Learner school link approved.'
                if decision == 'approve'
                else 'Learner school link rejected.'
            ),
        )


class SchoolStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def get(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        return _success(data=get_school_stats(school))


class SchoolAssignmentView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        student_id = request.data.get('student_id')
        counselor_id = request.data.get('counselor_id')

        try:
            profile = StudentProfile.objects.get(
                user_id=student_id,
                school=school,
                mode='school_linked',
                school_membership_status='active',
            )
        except StudentProfile.DoesNotExist:
            return _error('Student not found at your school.', status.HTTP_404_NOT_FOUND)

        try:
            counselor = User.objects.get(pk=counselor_id, role='counselor', school=school)
        except User.DoesNotExist:
            return _error('Counselor not found at your school.', status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            CounselorAssignment.objects.filter(
                student_profile=profile, is_active=True,
            ).update(is_active=False)

            assignment = CounselorAssignment.objects.create(
                counselor=counselor,
                student_profile=profile,
                school=school,
            )

        log_action(
            actor=request.user, action='counselor_assigned', target_type='assignment',
            target_id=assignment.id,
            details={'student_id': student_id, 'counselor_id': counselor_id},
            request=request,
        )
        return _success(
            data={'id': assignment.id, 'student_id': student_id, 'counselor_id': counselor_id},
            message=f'{profile.user.first_name} assigned to {counselor.first_name} {counselor.last_name}.',
            status_code=status.HTTP_201_CREATED,
        )


class SchoolBulkAssignmentView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request):
        school = request.user.school
        if not school:
            return _error(
                'No school assigned to your account.',
                status.HTTP_404_NOT_FOUND,
            )

        student_ids = request.data.get('student_ids')
        counselor_id = request.data.get('counselor_id')
        valid_ids = (
            isinstance(student_ids, list)
            and 1 <= len(student_ids) <= 50
            and all(type(student_id) is int and student_id > 0 for student_id in student_ids)
            and len(student_ids) == len(set(student_ids))
        )
        if not valid_ids:
            return _error(
                'student_ids must contain 1 to 50 unique learner IDs.'
            )

        try:
            counselor = User.objects.get(
                pk=counselor_id,
                role='counselor',
                school=school,
            )
        except (User.DoesNotExist, TypeError, ValueError):
            return _error(
                'Counselor not found at your school.',
                status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            profiles = list(
                StudentProfile.objects.select_for_update()
                .filter(
                    user_id__in=student_ids,
                    school=school,
                    mode='school_linked',
                    school_membership_status='active',
                )
                .order_by('user_id')
            )
            if len(profiles) != len(student_ids):
                return _error(
                    'Every selected learner must be approved and belong to your school.'
                )

            profile_ids = [profile.id for profile in profiles]
            if CounselorAssignment.objects.filter(
                student_profile_id__in=profile_ids,
                is_active=True,
            ).exists():
                return _error(
                    'Bulk assignment is limited to currently unassigned learners.'
                )

            assignments = CounselorAssignment.objects.bulk_create([
                CounselorAssignment(
                    counselor=counselor,
                    student_profile=profile,
                    school=school,
                )
                for profile in profiles
            ])

            for assignment, profile in zip(assignments, profiles):
                AuditLog.objects.create(
                    actor=request.user,
                    action='counselor_assigned',
                    target_type='assignment',
                    target_id=assignment.id,
                    details={
                        'student_id': profile.user_id,
                        'counselor_id': counselor.id,
                        'bulk': True,
                    },
                )

        return _success(
            data={
                'assigned_count': len(assignments),
                'counselor_id': counselor.id,
                'student_ids': student_ids,
            },
            message=(
                f'{len(assignments)} learners assigned to '
                f'{counselor.first_name} {counselor.last_name}.'
            ),
            status_code=status.HTTP_201_CREATED,
        )


class SchoolAssignmentRemoveView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request, assignment_id):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        try:
            assignment = CounselorAssignment.objects.get(
                pk=assignment_id, school=school, is_active=True,
            )
        except CounselorAssignment.DoesNotExist:
            return _error('Assignment not found.', status.HTTP_404_NOT_FOUND)

        assignment.is_active = False
        assignment.save(update_fields=['is_active'])
        return _success(message='Assignment removed.')
