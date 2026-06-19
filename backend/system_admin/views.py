import logging
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.models import School, User, StudentProfile, COUNTY_CHOICES
from accounts.permissions import IsSystemAdmin, IsEmailVerified
from accounts.response import _success, _error
from .models import AuditLog
from .utils import log_action

logger = logging.getLogger(__name__)

SYSTEM_ADMIN_PERMS = [IsAuthenticated, IsEmailVerified, IsSystemAdmin]
VALID_COUNTIES = {c[0] for c in COUNTY_CHOICES}
SCHOOL_EDITABLE_FIELDS = {'name', 'phone', 'email'}


class DashboardView(APIView):
    permission_classes = SYSTEM_ADMIN_PERMS

    def get(self, request):
        users_by_role = {}
        for row in User.objects.values('role').annotate(count=Count('id')):
            users_by_role[row['role']] = row['count']

        schools_by_county = {}
        for row in School.objects.filter(is_active=True).values('county').annotate(count=Count('id')):
            schools_by_county[row['county']] = row['count']

        total_schools = School.objects.filter(is_active=True).count()
        recent_signups = User.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7),
        ).count()

        recent_audit = list(
            AuditLog.objects.select_related('actor')[:10].values(
                'id', 'action', 'target_type', 'target_id',
                'created_at', 'actor__email', 'actor__first_name', 'actor__last_name',
            )
        )
        for entry in recent_audit:
            entry['actor_email'] = entry.pop('actor__email')
            entry['actor_name'] = f"{entry.pop('actor__first_name', '') or ''} {entry.pop('actor__last_name', '') or ''}".strip()
            entry['created_at'] = entry['created_at'].isoformat()

        return _success(data={
            'users_by_role': users_by_role,
            'schools_by_county': schools_by_county,
            'total_schools': total_schools,
            'recent_signups': recent_signups,
            'recent_audit': recent_audit,
        })


class SchoolListView(APIView):
    permission_classes = SYSTEM_ADMIN_PERMS

    def get(self, request):
        qs = School.objects.annotate(
            student_count=Count(
                'studentprofile',
                filter=Q(studentprofile__mode='school_linked'),
            ),
            counselor_count=Count(
                'staff',
                filter=Q(staff__role='counselor'),
            ),
        )

        county = request.query_params.get('county')
        if county:
            qs = qs.filter(county=county)

        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(school_code__icontains=search))

        active_param = request.query_params.get('active')
        if active_param == 'true':
            qs = qs.filter(is_active=True)
        elif active_param == 'false':
            qs = qs.filter(is_active=False)

        qs = qs.order_by('name')

        page = max(int(request.query_params.get('page', 1)), 1)
        page_size = 20
        total = qs.count()
        start = (page - 1) * page_size
        schools = qs[start:start + page_size]

        data = [
            {
                'id': s.id,
                'name': s.name,
                'county': s.county,
                'school_code': s.school_code,
                'phone': s.phone,
                'email': s.email,
                'logo_url': s.logo_url,
                'is_active': s.is_active,
                'student_count': s.student_count,
                'counselor_count': s.counselor_count,
            }
            for s in schools
        ]

        return _success(data={'results': data, 'total': total, 'page': page, 'page_size': page_size})

    def post(self, request):
        name = request.data.get('name', '').strip()
        county = request.data.get('county', '').strip()
        school_code = request.data.get('school_code', '').strip()
        phone = request.data.get('phone', '').strip()
        email = request.data.get('email', '').strip()

        if not name:
            return _error('School name is required.')
        if not county:
            return _error('County is required.')
        if county not in VALID_COUNTIES:
            return _error(f'County must be one of: {", ".join(sorted(VALID_COUNTIES))}.')
        if not school_code:
            return _error('School code is required.')
        if School.objects.filter(school_code=school_code).exists():
            return _error('A school with this code already exists.')

        school = School.objects.create(
            name=name,
            county=county,
            school_code=school_code,
            phone=phone,
            email=email,
        )

        log_action(
            actor=request.user,
            action='school_created',
            target_type='school',
            target_id=school.id,
            details={'name': name, 'county': county, 'school_code': school_code},
            request=request,
        )

        return _success(
            data={
                'id': school.id,
                'name': school.name,
                'county': school.county,
                'school_code': school.school_code,
                'phone': school.phone,
                'email': school.email,
                'logo_url': school.logo_url,
                'is_active': school.is_active,
            },
            message=f'{name} created.',
            status_code=status.HTTP_201_CREATED,
        )


class SchoolDetailView(APIView):
    permission_classes = SYSTEM_ADMIN_PERMS

    def _get_school(self, school_id):
        try:
            return School.objects.get(pk=school_id)
        except School.DoesNotExist:
            return None

    def get(self, request, school_id):
        school = self._get_school(school_id)
        if not school:
            return _error('School not found.', status.HTTP_404_NOT_FOUND)

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

        student_count = StudentProfile.objects.filter(
            school=school, mode='school_linked',
        ).count()

        recent_students = list(
            StudentProfile.objects.filter(school=school, mode='school_linked')
            .select_related('user')
            .order_by('-created_at')[:10]
        )

        return _success(data={
            'id': school.id,
            'name': school.name,
            'county': school.county,
            'school_code': school.school_code,
            'phone': school.phone,
            'email': school.email,
            'logo_url': school.logo_url,
            'is_active': school.is_active,
            'student_count': student_count,
            'counselor_count': counselors.count(),
            'counselors': [
                {
                    'id': c.id,
                    'first_name': c.first_name,
                    'last_name': c.last_name,
                    'email': c.email,
                    'student_count': c.student_count,
                }
                for c in counselors
            ],
            'recent_students': [
                {
                    'id': s.user.id,
                    'first_name': s.user.first_name,
                    'last_name': s.user.last_name,
                    'grade': s.grade,
                    'created_at': s.created_at.isoformat(),
                }
                for s in recent_students
            ],
        })

    def patch(self, request, school_id):
        school = self._get_school(school_id)
        if not school:
            return _error('School not found.', status.HTTP_404_NOT_FOUND)

        updated = []
        for field in SCHOOL_EDITABLE_FIELDS:
            if field in request.data:
                value = request.data[field]
                if not isinstance(value, str):
                    return _error(f'{field} must be a string.')
                setattr(school, field, value.strip())
                updated.append(field)

        if not updated:
            return _error('No valid fields provided.')

        from django.core.exceptions import ValidationError
        try:
            school.full_clean(exclude=['county', 'school_code'])
        except ValidationError as e:
            messages = []
            for field_errors in e.message_dict.values():
                messages.extend(field_errors)
            return _error(messages[0] if messages else 'Invalid data.')

        school.save(update_fields=updated)

        log_action(
            actor=request.user,
            action='school_edited',
            target_type='school',
            target_id=school.id,
            details={'updated_fields': updated},
            request=request,
        )

        return _success(
            data={
                'id': school.id,
                'name': school.name,
                'county': school.county,
                'school_code': school.school_code,
                'phone': school.phone,
                'email': school.email,
                'logo_url': school.logo_url,
                'is_active': school.is_active,
            },
            message='School updated.',
        )


class SchoolDeactivateView(APIView):
    permission_classes = SYSTEM_ADMIN_PERMS

    def post(self, request, school_id):
        try:
            school = School.objects.get(pk=school_id)
        except School.DoesNotExist:
            return _error('School not found.', status.HTTP_404_NOT_FOUND)

        if not school.is_active:
            return _error('School is already deactivated.')

        school.is_active = False
        school.save(update_fields=['is_active'])

        log_action(
            actor=request.user,
            action='school_deactivated',
            target_type='school',
            target_id=school.id,
            details={'name': school.name},
            request=request,
        )

        return _success(message=f'{school.name} has been deactivated.')


class SchoolActivateView(APIView):
    permission_classes = SYSTEM_ADMIN_PERMS

    def post(self, request, school_id):
        try:
            school = School.objects.get(pk=school_id)
        except School.DoesNotExist:
            return _error('School not found.', status.HTTP_404_NOT_FOUND)

        if school.is_active:
            return _error('School is already active.')

        school.is_active = True
        school.save(update_fields=['is_active'])

        log_action(
            actor=request.user,
            action='school_activated',
            target_type='school',
            target_id=school.id,
            details={'name': school.name},
            request=request,
        )

        return _success(message=f'{school.name} has been activated.')
