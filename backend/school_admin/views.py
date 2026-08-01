from io import BytesIO
from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Count, Exists, F, OuterRef, Prefetch, Q
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsSchoolAdmin, IsEmailVerified
from accounts.models import School, User, StudentProfile
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
from students.models import CBCGrade
from students.serializers import CBCGradeSerializer
from system_admin.models import AuditLog
from notifications.models import Notification


SCHOOL_EDITABLE_FIELDS = {'name', 'phone', 'email'}


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
                grade = (
                    CBCGrade.objects.select_for_update()
                    .select_related('student_subject__student_profile')
                    .get(
                        pk=grade_id,
                        student_subject__student_profile__user_id=student_id,
                        student_subject__student_profile__school=school,
                        student_subject__student_profile__mode='school_linked',
                        student_subject__student_profile__school_membership_status='active',
                    )
                )
            except CBCGrade.DoesNotExist:
                return _error(
                    'Grade not found for an active learner at your school.',
                    status.HTTP_404_NOT_FOUND,
                )

            is_verified = grade.verified_at is not None
            verifier_changed = (
                should_verify
                and is_verified
                and grade.verified_by_id != request.user.id
            )
            changed = should_verify != is_verified or verifier_changed
            if changed:
                update_fields = ['verified_by', 'verified_at', 'updated_at']
                if should_verify:
                    grade.verified_by = request.user
                    grade.verified_at = timezone.now()
                    if grade.verified_school_id is None:
                        grade.verified_school = school
                        update_fields.append('verified_school')
                    action = 'grade_verified'
                else:
                    grade.verified_by = None
                    grade.verified_at = None
                    action = 'grade_verification_removed'
                grade.save(update_fields=update_fields)

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

        profiles = (
            StudentProfile.objects.filter(school=school, mode='school_linked')
            .select_related('user')
            .annotate(has_assessment=Exists(has_assessment))
            .prefetch_related(
                Prefetch(
                    'counselor_assignments',
                    queryset=CounselorAssignment.objects.filter(is_active=True).select_related('counselor'),
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

            data.append({
                'id': p.user.id,
                'first_name': p.user.first_name,
                'last_name': p.user.last_name,
                'email': p.user.email,
                'grade': p.grade,
                'photo_url': p.photo_url,
                'quiz_status': 'done' if p.has_assessment else 'pending',
                'school_membership_status': p.school_membership_status,
                'counselor_id': active_assignment.counselor_id if active_assignment else None,
                'counselor_name': (
                    f'{active_assignment.counselor.first_name} {active_assignment.counselor.last_name}'
                    if active_assignment else None
                ),
            })
        return _success(data=data)


class SchoolMembershipRequestsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def get(self, request):
        school = request.user.school
        if not school:
            return _error(
                'No school assigned to your account.',
                status.HTTP_404_NOT_FOUND,
            )

        profiles = (
            StudentProfile.objects.filter(
                school=school,
                mode='school_linked',
                school_membership_status='pending',
            )
            .select_related('user')
            .order_by('created_at', 'user__first_name', 'user__last_name')
        )
        return _success(data=[
            {
                'student_id': profile.user_id,
                'first_name': profile.user.first_name,
                'last_name': profile.user.last_name,
                'email': profile.user.email,
                'grade': profile.grade,
                'requested_at': profile.created_at.isoformat(),
            }
            for profile in profiles
        ])


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
                    .get(
                        user_id=student_id,
                        school=school,
                        mode='school_linked',
                    )
                )
            except StudentProfile.DoesNotExist:
                return _error(
                    'Pending membership request not found.',
                    status.HTTP_404_NOT_FOUND,
                )

            if profile.school_membership_status != 'pending':
                return _error(
                    'This membership request has already been decided.',
                    status.HTTP_409_CONFLICT,
                )

            membership_status = 'active' if decision == 'approve' else 'rejected'
            profile.school_membership_status = membership_status
            profile.save(update_fields=['school_membership_status'])

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
                },
                ip_address=ip_address,
            )
            Notification.objects.create(
                user=profile.user,
                type='school_membership_decided',
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

        has_assessment = RIASECAssessment.objects.filter(student_profile=OuterRef('pk'))

        profiles = (
            StudentProfile.objects.filter(
                school=school,
                mode='school_linked',
                school_membership_status='active',
            )
            .annotate(
                has_assessment=Exists(has_assessment),
                enrolled_subject_count=Count(
                    'enrolled_subjects',
                    distinct=True,
                ),
                subjects_with_evidence=Count(
                    'enrolled_subjects',
                    filter=Q(enrolled_subjects__grades__isnull=False),
                    distinct=True,
                ),
            )
        )
        total_students = profiles.count()
        assessed = profiles.filter(has_assessment=True).count()
        evidence_complete = profiles.filter(
            enrolled_subject_count__gte=3,
            subjects_with_evidence=F('enrolled_subject_count'),
        ).count()
        choices_saved = profiles.filter(
            combination_choices__isnull=False,
        ).distinct().count()
        plans_created = profiles.filter(
            learner_plan__isnull=False,
        ).count()
        reviews_completed = profiles.filter(
            learner_plan__review_status='reviewed',
        ).count()
        pending_memberships = StudentProfile.objects.filter(
            school=school,
            mode='school_linked',
            school_membership_status='pending',
        ).count()
        assigned_ids = set(
            CounselorAssignment.objects.filter(school=school, is_active=True)
            .values_list('student_profile_id', flat=True)
        )
        unassigned = profiles.exclude(pk__in=assigned_ids).count()
        counselors = list(
            User.objects.filter(school=school, role='counselor')
            .annotate(
                active_student_count=Count(
                    'student_assignments',
                    filter=Q(
                        student_assignments__is_active=True,
                        student_assignments__school=school,
                        student_assignments__student_profile__school_membership_status='active',
                    ),
                    distinct=True,
                ),
            )
            .order_by('first_name', 'last_name', 'pk')
        )
        total_counselors = len(counselors)
        framework = FrameworkVersion.objects.current()
        offerings_count = (
            SchoolOffering.objects.filter(
                school=school,
                is_active=True,
                combination__framework_version=framework,
                combination__is_active=True,
                combination__track__is_active=True,
            ).count()
            if framework is not None
            else 0
        )

        return _success(data={
            'total_students': total_students,
            'total_counselors': total_counselors,
            'assessed': assessed,
            'unassigned': unassigned,
            'pending_memberships': pending_memberships,
            'evidence_complete': evidence_complete,
            'choices_saved': choices_saved,
            'plans_created': plans_created,
            'reviews_completed': reviews_completed,
            'offerings_count': offerings_count,
            'offerings_configured': offerings_count > 0,
            'counselor_workload': [
                {
                    'counselor_id': counselor.id,
                    'counselor_name': (
                        f'{counselor.first_name} {counselor.last_name}'
                    ),
                    'student_count': counselor.active_student_count,
                }
                for counselor in counselors
            ],
        })


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
