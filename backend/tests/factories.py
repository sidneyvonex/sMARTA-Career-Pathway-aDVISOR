from datetime import date

import factory
from django.contrib.auth import get_user_model
from accounts.models import School, StudentProfile
from students.models import (
    AssessmentFramework,
    CBCGrade,
    PerformanceLevelDefinition,
    StudentSubject,
    Subject,
)
from riasec.models import RIASECAssessment, RIASECScore, Pathway, Recommendation
from notifications.models import Notification
from parents.models import ParentStudentLink
from counselors.models import CounselorAssignment, CounselorNote
from system_admin.models import AuditLog
from guidance.models import (
    FrameworkVersion,
    PathwayTrack,
    SchoolOffering,
    SubjectCombination,
)

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = 'student'
    # Automatically None for system_admin; explicit county= override takes precedence
    county = factory.LazyAttribute(lambda o: None if o.role == 'system_admin' else 'kiambu')
    is_email_verified = False
    password = factory.django.Password('TestPass123!')


class VerifiedUserFactory(UserFactory):
    is_email_verified = True


class CounselorFactory(UserFactory):
    role = 'counselor'
    is_email_verified = True
    school = None


class ParentFactory(UserFactory):
    role = 'parent'
    is_email_verified = True


class SchoolFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = School

    name = factory.Sequence(lambda n: f'Test School {n}')
    county = 'kiambu'
    school_code = factory.Sequence(lambda n: f'SCH{n:04d}')
    verification_status = School.VERIFICATION_VERIFIED
    source_url = 'https://selection.education.go.ke/schools'
    source_checked_at = date(2026, 7, 31)


class SystemAdminFactory(UserFactory):
    role = 'system_admin'
    county = None
    is_email_verified = True


class SchoolAdminFactory(UserFactory):
    role = 'school_admin'
    is_email_verified = True
    school = factory.SubFactory(SchoolFactory)


class StudentProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentProfile

    user = factory.SubFactory(UserFactory, role='student')
    mode = 'self_guided'
    school = None
    school_membership_status = factory.LazyAttribute(
        lambda profile: 'active' if profile.mode == 'school_linked' else 'not_applicable'
    )
    grade = factory.Iterator([9, 10])


class SubjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subject
        django_get_or_create = ('code',)

    name = factory.Sequence(lambda n: f'Subject {n}')
    code = factory.Sequence(lambda n: f'TST{n:04d}9')
    grade = 9
    category = 'Core'
    is_selectable_in_combination = False


class StudentSubjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentSubject

    student_profile = factory.SubFactory(StudentProfileFactory, grade=9)
    subject = factory.SubFactory(SubjectFactory, grade=9)


class AssessmentFrameworkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AssessmentFramework

    code = factory.Sequence(lambda n: f'CBC-TEST-{n:04d}')
    version = 'v1'
    title = factory.Sequence(lambda n: f'Test Assessment Framework {n}')
    scope = factory.Sequence(lambda n: f'test_scope_{n}')
    source_url = 'https://kicd.ac.ke/curriculum-reform/'
    effective_date = date(2026, 1, 1)
    status = AssessmentFramework.STATUS_DRAFT


class PerformanceLevelDefinitionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PerformanceLevelDefinition

    framework = factory.SubFactory(AssessmentFrameworkFactory)
    code = factory.Sequence(lambda n: f'L{n}')
    label = factory.Sequence(lambda n: f'Level {n}')
    description = factory.Sequence(lambda n: f'Performance level {n}.')
    rank = factory.Sequence(lambda n: n + 1)


class CBCGradeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CBCGrade

    student_subject = factory.SubFactory(StudentSubjectFactory)
    academic_grade = factory.LazyAttribute(
        lambda grade: grade.student_subject.subject.grade
    )
    framework = factory.LazyAttribute(
        lambda grade: AssessmentFramework.objects.get(
            scope=(
                'junior_school'
                if grade.academic_grade == 9
                else 'senior_school'
            ),
            status=AssessmentFramework.STATUS_ACTIVE,
        )
    )
    verified_school = factory.LazyAttribute(
        lambda grade: getattr(getattr(grade, 'verified_by', None), 'school', None)
    )
    term = 1
    year = 2026
    level = 'ME1'


class RIASECAssessmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RIASECAssessment

    student_profile = factory.SubFactory(StudentProfileFactory, grade=9)


class RIASECScoreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RIASECScore

    assessment = factory.SubFactory(RIASECAssessmentFactory)
    dimension = 'R'
    raw_score = 15


class PathwayFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pathway

    name = factory.Sequence(lambda n: f'Pathway {n}')
    description = 'Test pathway description'
    weight_r = 1.0
    weight_i = 1.0
    weight_a = 0.0
    weight_s = 0.0
    weight_e = 0.0
    weight_c = 0.0


class FrameworkVersionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FrameworkVersion

    code = factory.Sequence(lambda n: f'CBC-SS-{2026 + n}')
    title = factory.Sequence(lambda n: f'CBC Senior School Framework {2026 + n}')
    description = 'Curated framework for pilot guidance.'
    source_url = 'https://kicd.ac.ke/curriculum-reform/'
    effective_date = factory.LazyFunction(lambda: date(2026, 1, 1))
    is_active = False


class PathwayTrackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PathwayTrack

    framework_version = factory.SubFactory(FrameworkVersionFactory)
    pathway = factory.SubFactory(PathwayFactory)
    code = factory.Sequence(lambda n: f'TRACK-{n:04d}')
    name = factory.Sequence(lambda n: f'Pilot Track {n}')
    description = 'Pilot pathway track.'
    is_active = True


class SubjectCombinationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SubjectCombination

    track = factory.SubFactory(PathwayTrackFactory)
    framework_version = factory.LazyAttribute(
        lambda combination: combination.track.framework_version
    )
    code = factory.Sequence(lambda n: f'COMBO-{n:04d}')
    title = factory.Sequence(lambda n: f'Pilot Combination {n}')
    description = 'Three-subject pilot combination.'
    verification_status = SubjectCombination.VERIFICATION_VERIFIED
    source_url = (
        'https://selection.education.go.ke/uploads/'
        '1750333580754-subject-combinations-1750333524964.pdf'
    )
    source_checked_at = date(2026, 7, 31)
    subject_one = factory.SubFactory(
        SubjectFactory,
        grade=10,
        category='Elective',
        is_selectable_in_combination=True,
    )
    subject_two = factory.SubFactory(
        SubjectFactory,
        grade=10,
        category='Elective',
        is_selectable_in_combination=True,
    )
    subject_three = factory.SubFactory(
        SubjectFactory,
        grade=10,
        category='Elective',
        is_selectable_in_combination=True,
    )
    is_active = True


class SchoolOfferingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SchoolOffering

    school = factory.SubFactory(SchoolFactory)
    combination = factory.SubFactory(SubjectCombinationFactory)
    is_active = True
    verification_status = SchoolOffering.VERIFICATION_VERIFIED
    source_url = 'https://selection.education.go.ke/schools'
    source_checked_at = date(2026, 7, 31)


class RecommendationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Recommendation

    assessment = factory.SubFactory(RIASECAssessmentFactory)
    pathway = factory.SubFactory(PathwayFactory)
    rank = 1
    fit_score = 0.87
    fit_pct = 87


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    user = factory.SubFactory(VerifiedUserFactory)
    type = 'assessment_submitted'
    message = 'Your RIASEC assessment results are ready.'
    read = False


class CounselorAssignmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CounselorAssignment

    counselor = factory.SubFactory(CounselorFactory)
    student_profile = factory.SubFactory(StudentProfileFactory)
    school = factory.SubFactory(SchoolFactory)
    is_active = True


class CounselorNoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CounselorNote

    counselor = factory.SubFactory(CounselorFactory)
    student = factory.SubFactory(VerifiedUserFactory, role='student')
    body = factory.Faker('paragraph')
    visible_to_parent = False


class ParentStudentLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ParentStudentLink

    parent = factory.SubFactory(ParentFactory)
    student = factory.SubFactory(VerifiedUserFactory, role='student')
    status = ParentStudentLink.STATUS_ACTIVE


class AuditLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuditLog

    actor = factory.SubFactory(SystemAdminFactory)
    action = 'school_created'
    target_type = 'school'
    target_id = 1
    details = factory.LazyFunction(dict)
