import factory
from django.contrib.auth import get_user_model
from accounts.models import School, StudentProfile
from students.models import Subject, StudentSubject, CBCGrade
from riasec.models import RIASECAssessment, RIASECScore, Pathway, Recommendation
from notifications.models import Notification
from parents.models import ParentStudentLink
from counselors.models import CounselorAssignment, CounselorNote
from system_admin.models import AuditLog

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
    grade = factory.Iterator([9, 10])


class SubjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subject
        django_get_or_create = ('code',)

    name = factory.Sequence(lambda n: f'Subject {n}')
    code = factory.Sequence(lambda n: f'TST{n:04d}9')
    grade = 9
    category = 'Core'


class StudentSubjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentSubject

    student_profile = factory.SubFactory(StudentProfileFactory, grade=9)
    subject = factory.SubFactory(SubjectFactory, grade=9)


class CBCGradeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CBCGrade

    student_subject = factory.SubFactory(StudentSubjectFactory)
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


class AuditLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuditLog

    actor = factory.SubFactory(SystemAdminFactory)
    action = 'school_created'
    target_type = 'school'
    target_id = 1
    details = factory.LazyFunction(dict)
