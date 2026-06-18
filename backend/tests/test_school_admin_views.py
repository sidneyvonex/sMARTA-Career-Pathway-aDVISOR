import pytest
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APIClient
from tests.factories import SchoolAdminFactory, SchoolFactory, StudentProfileFactory, CounselorFactory

pytestmark = pytest.mark.django_db


class TestSchoolProfileView:
    def setup_method(self):
        self.client = APIClient()
        self.school = SchoolFactory(name='Starehe Boys', county='nairobi', school_code='NAI001')
        self.admin = SchoolAdminFactory(school=self.school)
        self.client.force_authenticate(self.admin)

    def test_get_school_profile(self):
        response = self.client.get('/api/v1/school-admin/school/')
        assert response.status_code == 200
        data = response.data['data']
        assert data['name'] == 'Starehe Boys'
        assert data['county'] == 'nairobi'
        assert data['school_code'] == 'NAI001'
        assert data['logo_url'] is None
        assert data['student_count'] == 0
        assert data['counselor_count'] == 0

    def test_get_school_profile_with_counts(self):
        CounselorFactory(school=self.school)
        CounselorFactory(school=self.school)
        StudentProfileFactory(school=self.school, mode='school_linked')
        response = self.client.get('/api/v1/school-admin/school/')
        data = response.data['data']
        assert data['student_count'] == 1
        assert data['counselor_count'] == 2

    def test_patch_school_profile(self):
        response = self.client.patch('/api/v1/school-admin/school/', {
            'name': 'Starehe Boys Centre',
            'phone': '+254712345678',
            'email': 'info@starehe.ac.ke',
        })
        assert response.status_code == 200
        data = response.data['data']
        assert data['name'] == 'Starehe Boys Centre'
        assert data['phone'] == '+254712345678'
        assert data['email'] == 'info@starehe.ac.ke'

    def test_patch_rejects_school_code_change(self):
        response = self.client.patch('/api/v1/school-admin/school/', {
            'school_code': 'HACK001',
        })
        assert response.status_code == 200
        self.school.refresh_from_db()
        assert self.school.school_code == 'NAI001'

    def test_patch_rejects_county_change(self):
        response = self.client.patch('/api/v1/school-admin/school/', {
            'county': 'mombasa',
        })
        assert response.status_code == 200
        self.school.refresh_from_db()
        assert self.school.county == 'nairobi'

    def test_requires_school_admin_role(self):
        student_client = APIClient()
        student = CounselorFactory(school=self.school)
        student_client.force_authenticate(student)
        response = student_client.get('/api/v1/school-admin/school/')
        assert response.status_code == 403

    def test_admin_without_school_gets_404(self):
        orphan = SchoolAdminFactory(school=None)
        self.client.force_authenticate(orphan)
        response = self.client.get('/api/v1/school-admin/school/')
        assert response.status_code == 404


def _make_image(fmt='PNG', size=(100, 100)):
    img = Image.new('RGB', size, color='red')
    buf = BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    ext = 'png' if fmt == 'PNG' else 'jpg'
    return SimpleUploadedFile(f'logo.{ext}', buf.read(), content_type=f'image/{ext}')


class TestSchoolLogoUpload:
    def setup_method(self):
        self.client = APIClient()
        self.school = SchoolFactory(name='Starehe Boys', county='nairobi', school_code='NAI002')
        self.admin = SchoolAdminFactory(school=self.school)
        self.client.force_authenticate(self.admin)

    def test_upload_logo_png(self):
        logo = _make_image('PNG')
        response = self.client.post('/api/v1/school-admin/school/logo/', {'logo': logo}, format='multipart')
        assert response.status_code == 200
        assert response.data['data']['logo_url'] is not None
        self.school.refresh_from_db()
        assert self.school.logo_url is not None

    def test_upload_logo_jpeg(self):
        logo = _make_image('JPEG')
        response = self.client.post('/api/v1/school-admin/school/logo/', {'logo': logo}, format='multipart')
        assert response.status_code == 200

    def test_upload_rejects_no_file(self):
        response = self.client.post('/api/v1/school-admin/school/logo/', {}, format='multipart')
        assert response.status_code == 400
        assert 'No logo file' in response.data['message']

    def test_upload_rejects_oversized_file(self):
        large = SimpleUploadedFile('big.png', b'\x00' * (6 * 1024 * 1024), content_type='image/png')
        response = self.client.post('/api/v1/school-admin/school/logo/', {'logo': large}, format='multipart')
        assert response.status_code == 400
        assert '5MB' in response.data['message']

    def test_upload_rejects_non_image(self):
        txt = SimpleUploadedFile('doc.txt', b'hello', content_type='text/plain')
        response = self.client.post('/api/v1/school-admin/school/logo/', {'logo': txt}, format='multipart')
        assert response.status_code == 400

    def test_delete_logo(self):
        self.school.logo_url = 'https://example.com/old.png'
        self.school.save()
        response = self.client.delete('/api/v1/school-admin/school/logo/')
        assert response.status_code == 200
        self.school.refresh_from_db()
        assert self.school.logo_url is None

    def test_admin_without_school_gets_404(self):
        orphan = SchoolAdminFactory(school=None)
        self.client.force_authenticate(orphan)
        logo = _make_image()
        response = self.client.post('/api/v1/school-admin/school/logo/', {'logo': logo}, format='multipart')
        assert response.status_code == 404
