import io
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from tests.factories import VerifiedUserFactory, UserFactory, StudentProfileFactory
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.fixture
def client():
    return APIClient()


def make_auth_client(user):
    c = APIClient()
    refresh = RefreshToken.for_user(user)
    c.cookies['access_token'] = str(refresh.access_token)
    return c


@pytest.fixture
def verified_profile(db):
    user = VerifiedUserFactory(role='student')
    return StudentProfileFactory(user=user, grade=9)


@pytest.mark.django_db
class TestStudentProfileView:
    def test_get_profile_returns_200(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        response = c.get('/api/v1/students/profile/')
        assert response.status_code == 200
        assert response.data['data']['email'] == verified_profile.user.email
        assert response.data['data']['grade'] == 9

    def test_patch_updates_bio(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        response = c.patch('/api/v1/students/profile/', {'bio': 'I love science.'}, format='json')
        assert response.status_code == 200
        assert response.data['data']['bio'] == 'I love science.'

    def test_patch_bio_over_500_chars_rejected(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        response = c.patch('/api/v1/students/profile/', {'bio': 'x' * 501}, format='json')
        assert response.status_code == 400

    def test_patch_cannot_change_grade(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        c.patch('/api/v1/students/profile/', {'grade': 10}, format='json')
        verified_profile.refresh_from_db()
        assert verified_profile.grade == 9

    def test_unverified_student_patch_returns_403(self, db):
        user = UserFactory(role='student', is_email_verified=False)
        StudentProfileFactory(user=user, grade=9)
        c = make_auth_client(user)
        response = c.patch('/api/v1/students/profile/', {'bio': 'hi'}, format='json')
        assert response.status_code == 403

    def test_unauthenticated_returns_401(self, client):
        response = client.get('/api/v1/students/profile/')
        assert response.status_code == 401

    def test_counselor_role_returns_403(self, db):
        user = VerifiedUserFactory(role='counselor')
        c = make_auth_client(user)
        response = c.get('/api/v1/students/profile/')
        assert response.status_code == 403

    def test_patch_cannot_change_photo_url(self, verified_profile):
        verified_profile.photo_url = None
        verified_profile.save()
        c = make_auth_client(verified_profile.user)
        c.patch('/api/v1/students/profile/', {'photo_url': 'https://evil.com/photo.jpg'}, format='json')
        verified_profile.refresh_from_db()
        assert verified_profile.photo_url is None


def _make_image_bytes(fmt='JPEG', width=50, height=50):
    img = Image.new('RGB', (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


@pytest.mark.django_db
class TestPhotoUploadView:
    def test_upload_valid_jpeg_returns_200(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        image_bytes = _make_image_bytes('JPEG')
        photo = SimpleUploadedFile('photo.jpg', image_bytes, content_type='image/jpeg')
        response = c.post('/api/v1/students/profile/photo/', {'photo': photo}, format='multipart')
        assert response.status_code == 200
        assert 'photo_url' in response.data['data']
        verified_profile.refresh_from_db()
        assert verified_profile.photo_url is not None

    def test_upload_valid_png_returns_200(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        image_bytes = _make_image_bytes('PNG')
        photo = SimpleUploadedFile('photo.png', image_bytes, content_type='image/png')
        response = c.post('/api/v1/students/profile/photo/', {'photo': photo}, format='multipart')
        assert response.status_code == 200

    def test_upload_non_image_rejected(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        fake = SimpleUploadedFile('file.txt', b'not an image', content_type='text/plain')
        response = c.post('/api/v1/students/profile/photo/', {'photo': fake}, format='multipart')
        assert response.status_code == 400
        assert (
            'JPEG' in response.data['message']
            or 'PNG' in response.data['message']
            or 'Invalid image file' in response.data['message']
        )

    def test_upload_oversized_file_rejected(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        big = SimpleUploadedFile('big.jpg', b'x' * (5 * 1024 * 1024 + 1), content_type='image/jpeg')
        response = c.post('/api/v1/students/profile/photo/', {'photo': big}, format='multipart')
        assert response.status_code == 400
        assert '5MB' in response.data['message']

    def test_no_file_returns_400(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        response = c.post('/api/v1/students/profile/photo/', {}, format='multipart')
        assert response.status_code == 400

    def test_delete_photo_clears_photo_url(self, verified_profile):
        verified_profile.photo_url = 'https://example.com/photo.jpg'
        verified_profile.save()
        c = make_auth_client(verified_profile.user)
        response = c.delete('/api/v1/students/profile/photo/')
        assert response.status_code == 200
        verified_profile.refresh_from_db()
        assert verified_profile.photo_url is None


from students.models import Subject, StudentSubject


@pytest.mark.django_db
class TestSubjectListView:
    def test_returns_subjects_for_grade(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        response = c.get('/api/v1/students/subjects/?grade=9')
        assert response.status_code == 200
        assert len(response.data['data']) == 14
        codes = [s['code'] for s in response.data['data']]
        assert 'MTH9' in codes

    def test_invalid_grade_returns_400(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        response = c.get('/api/v1/students/subjects/?grade=abc')
        assert response.status_code == 400

    def test_unverified_returns_403(self, db):
        user = UserFactory(role='student', is_email_verified=False)
        StudentProfileFactory(user=user, grade=9)
        c = make_auth_client(user)
        response = c.get('/api/v1/students/subjects/?grade=9')
        assert response.status_code == 403


@pytest.mark.django_db
class TestMySubjectListView:
    def test_enroll_in_subject_returns_201(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        subject = Subject.objects.get(code='MTH9')
        response = c.post('/api/v1/students/my-subjects/', {'subject_id': subject.id}, format='json')
        assert response.status_code == 201
        assert StudentSubject.objects.filter(
            student_profile=verified_profile, subject=subject
        ).exists()

    def test_enroll_wrong_grade_subject_returns_400(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        subject = Subject.objects.get(code='MTH10')
        response = c.post('/api/v1/students/my-subjects/', {'subject_id': subject.id}, format='json')
        assert response.status_code == 400

    def test_duplicate_enrollment_returns_400(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        subject = Subject.objects.get(code='ENG9')
        c.post('/api/v1/students/my-subjects/', {'subject_id': subject.id}, format='json')
        response = c.post('/api/v1/students/my-subjects/', {'subject_id': subject.id}, format='json')
        assert response.status_code == 400

    def test_list_enrolled_subjects(self, verified_profile):
        from tests.factories import StudentSubjectFactory
        StudentSubjectFactory(student_profile=verified_profile, subject=Subject.objects.get(code='ENG9'))
        c = make_auth_client(verified_profile.user)
        response = c.get('/api/v1/students/my-subjects/')
        assert response.status_code == 200
        assert len(response.data['data']) == 1

    def test_remove_subject_without_confirm_returns_400(self, verified_profile):
        from tests.factories import StudentSubjectFactory
        ss = StudentSubjectFactory(student_profile=verified_profile, subject=Subject.objects.get(code='KIS9'))
        c = make_auth_client(verified_profile.user)
        response = c.post(f'/api/v1/students/my-subjects/{ss.pk}/remove/', {}, format='json')
        assert response.status_code == 400
        assert StudentSubject.objects.filter(pk=ss.pk).exists()

    def test_remove_subject_with_confirm_deletes_enrollment(self, verified_profile):
        from tests.factories import StudentSubjectFactory
        ss = StudentSubjectFactory(student_profile=verified_profile, subject=Subject.objects.get(code='AGR9'))
        c = make_auth_client(verified_profile.user)
        response = c.post(f'/api/v1/students/my-subjects/{ss.pk}/remove/', {'confirm': True}, format='json')
        assert response.status_code == 200
        assert not StudentSubject.objects.filter(pk=ss.pk).exists()


from tests.factories import StudentSubjectFactory, CBCGradeFactory


@pytest.fixture
def enrolled_subject(verified_profile):
    subject = Subject.objects.get(code='MTH9')
    return StudentSubjectFactory(student_profile=verified_profile, subject=subject)


@pytest.mark.django_db
class TestCBCGradeViews:
    def test_add_grade_returns_201(self, verified_profile, enrolled_subject):
        c = make_auth_client(verified_profile.user)
        response = c.post(
            f'/api/v1/students/my-subjects/{enrolled_subject.pk}/grades/',
            {'term': 1, 'year': 2026, 'level': 'ME1'},
            format='json',
        )
        assert response.status_code == 201
        assert response.data['data']['level'] == 'ME1'

    def test_list_grades_returns_200(self, verified_profile, enrolled_subject):
        CBCGradeFactory(student_subject=enrolled_subject, term=1, year=2026, level='EE1')
        c = make_auth_client(verified_profile.user)
        response = c.get(f'/api/v1/students/my-subjects/{enrolled_subject.pk}/grades/')
        assert response.status_code == 200
        assert len(response.data['data']) == 1

    def test_duplicate_term_year_returns_400(self, verified_profile, enrolled_subject):
        CBCGradeFactory(student_subject=enrolled_subject, term=2, year=2026, level='ME2')
        c = make_auth_client(verified_profile.user)
        response = c.post(
            f'/api/v1/students/my-subjects/{enrolled_subject.pk}/grades/',
            {'term': 2, 'year': 2026, 'level': 'AE1'},
            format='json',
        )
        assert response.status_code == 400

    def test_invalid_year_returns_400(self, verified_profile, enrolled_subject):
        c = make_auth_client(verified_profile.user)
        response = c.post(
            f'/api/v1/students/my-subjects/{enrolled_subject.pk}/grades/',
            {'term': 1, 'year': 1990, 'level': 'ME1'},
            format='json',
        )
        assert response.status_code == 400

    def test_update_grade_returns_200(self, verified_profile, enrolled_subject):
        grade = CBCGradeFactory(student_subject=enrolled_subject, term=3, year=2026, level='AE1')
        c = make_auth_client(verified_profile.user)
        response = c.put(
            f'/api/v1/students/my-subjects/{enrolled_subject.pk}/grades/{grade.pk}/',
            {'term': 3, 'year': 2026, 'level': 'ME1'},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['data']['level'] == 'ME1'

    def test_delete_grade_returns_200(self, verified_profile, enrolled_subject):
        from students.models import CBCGrade
        grade = CBCGradeFactory(student_subject=enrolled_subject, term=1, year=2025, level='BE1')
        c = make_auth_client(verified_profile.user)
        response = c.delete(
            f'/api/v1/students/my-subjects/{enrolled_subject.pk}/grades/{grade.pk}/'
        )
        assert response.status_code == 200
        assert not CBCGrade.objects.filter(pk=grade.pk).exists()

    def test_cannot_access_other_students_grades(self, db, enrolled_subject):
        other_user = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=other_user, grade=9)
        c = make_auth_client(other_user)
        response = c.get(f'/api/v1/students/my-subjects/{enrolled_subject.pk}/grades/')
        assert response.status_code == 404
