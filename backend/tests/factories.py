import factory
from django.contrib.auth import get_user_model
from accounts.models import School, StudentProfile

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = 'student'
    county = factory.LazyAttribute(lambda o: None if o.role == 'system_admin' else 'kiambu')
    is_email_verified = False
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')


class VerifiedUserFactory(UserFactory):
    is_email_verified = True


class SchoolFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = School

    name = factory.Sequence(lambda n: f'Test School {n}')
    county = 'kiambu'
    school_code = factory.Sequence(lambda n: f'SCH{n:04d}')


class StudentProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentProfile

    user = factory.SubFactory(UserFactory, role='student')
    mode = 'self_guided'
    school = None
    grade = 9
