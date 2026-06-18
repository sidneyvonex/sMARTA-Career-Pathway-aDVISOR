import pytest
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APIClient
from tests.factories import SchoolAdminFactory, SchoolFactory, StudentProfileFactory, CounselorFactory, CounselorAssignmentFactory
from riasec.models import RIASECAssessment
from counselors.models import CounselorAssignment

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


class TestSchoolCounselorsView:
    def setup_method(self):
        self.client = APIClient()
        self.school = SchoolFactory(name='Starehe Boys', county='nairobi', school_code='NAI003')
        self.admin = SchoolAdminFactory(school=self.school)
        self.client.force_authenticate(self.admin)

    def test_list_counselors(self):
        c1 = CounselorFactory(school=self.school, first_name='Alice', last_name='Wanjiku')
        c2 = CounselorFactory(school=self.school, first_name='Bob', last_name='Ochieng')
        CounselorFactory(school=SchoolFactory())  # different school — should not appear
        response = self.client.get('/api/v1/school-admin/counselors/')
        assert response.status_code == 200
        data = response.data['data']
        assert len(data) == 2
        names = {d['first_name'] for d in data}
        assert names == {'Alice', 'Bob'}

    def test_counselor_entry_has_student_count(self):
        c = CounselorFactory(school=self.school)
        sp = StudentProfileFactory(school=self.school, mode='school_linked')
        CounselorAssignmentFactory(counselor=c, student_profile=sp, school=self.school)
        response = self.client.get('/api/v1/school-admin/counselors/')
        assert response.data['data'][0]['student_count'] == 1

    def test_add_counselor_to_school(self):
        counselor = CounselorFactory(school=None, email='new@school.co.ke')
        response = self.client.post('/api/v1/school-admin/counselors/add/', {'email': 'new@school.co.ke'})
        assert response.status_code == 200
        counselor.refresh_from_db()
        assert counselor.school == self.school

    def test_add_counselor_already_at_another_school(self):
        other_school = SchoolFactory()
        CounselorFactory(school=other_school, email='taken@school.co.ke')
        response = self.client.post('/api/v1/school-admin/counselors/add/', {'email': 'taken@school.co.ke'})
        assert response.status_code == 400
        assert 'already assigned' in response.data['message']

    def test_add_non_counselor_fails(self):
        SchoolAdminFactory(email='admin@school.co.ke', school=None)
        response = self.client.post('/api/v1/school-admin/counselors/add/', {'email': 'admin@school.co.ke'})
        assert response.status_code == 404

    def test_add_nonexistent_email_fails(self):
        response = self.client.post('/api/v1/school-admin/counselors/add/', {'email': 'nobody@school.co.ke'})
        assert response.status_code == 404

    def test_remove_counselor_from_school(self):
        c = CounselorFactory(school=self.school)
        sp = StudentProfileFactory(school=self.school, mode='school_linked')
        assignment = CounselorAssignmentFactory(counselor=c, student_profile=sp, school=self.school)
        response = self.client.post(f'/api/v1/school-admin/counselors/{c.id}/remove/')
        assert response.status_code == 200
        c.refresh_from_db()
        assert c.school is None
        assignment.refresh_from_db()
        assert assignment.is_active is False

    def test_remove_counselor_not_at_school(self):
        other = CounselorFactory(school=SchoolFactory())
        response = self.client.post(f'/api/v1/school-admin/counselors/{other.id}/remove/')
        assert response.status_code == 404


class TestSchoolStudentsView:
    def setup_method(self):
        self.client = APIClient()
        self.school = SchoolFactory(name='Starehe Boys', county='nairobi', school_code='NAI004')
        self.admin = SchoolAdminFactory(school=self.school)
        self.client.force_authenticate(self.admin)

    def test_list_students(self):
        sp1 = StudentProfileFactory(school=self.school, mode='school_linked')
        sp2 = StudentProfileFactory(school=self.school, mode='school_linked')
        StudentProfileFactory(school=SchoolFactory(), mode='school_linked')  # different school
        StudentProfileFactory(mode='self_guided')  # no school
        response = self.client.get('/api/v1/school-admin/students/')
        assert response.status_code == 200
        assert len(response.data['data']) == 2

    def test_student_entry_includes_counselor(self):
        sp = StudentProfileFactory(school=self.school, mode='school_linked')
        c = CounselorFactory(school=self.school, first_name='Dr', last_name='Ouma')
        CounselorAssignmentFactory(counselor=c, student_profile=sp, school=self.school)
        response = self.client.get('/api/v1/school-admin/students/')
        student = response.data['data'][0]
        assert student['counselor_name'] == 'Dr Ouma'

    def test_student_entry_without_counselor(self):
        StudentProfileFactory(school=self.school, mode='school_linked')
        response = self.client.get('/api/v1/school-admin/students/')
        student = response.data['data'][0]
        assert student['counselor_name'] is None

    def test_student_entry_includes_assessment_status(self):
        sp = StudentProfileFactory(school=self.school, mode='school_linked')
        RIASECAssessment.objects.create(student_profile=sp)
        response = self.client.get('/api/v1/school-admin/students/')
        student = response.data['data'][0]
        assert student['quiz_status'] == 'done'


class TestSchoolStatsView:
    def setup_method(self):
        self.client = APIClient()
        self.school = SchoolFactory(name='Starehe Boys', county='nairobi', school_code='NAI005')
        self.admin = SchoolAdminFactory(school=self.school)
        self.client.force_authenticate(self.admin)

    def test_stats_empty_school(self):
        response = self.client.get('/api/v1/school-admin/stats/')
        assert response.status_code == 200
        data = response.data['data']
        assert data['total_students'] == 0
        assert data['total_counselors'] == 0
        assert data['assessed'] == 0
        assert data['unassigned'] == 0

    def test_stats_with_data(self):
        CounselorFactory(school=self.school)
        sp1 = StudentProfileFactory(school=self.school, mode='school_linked')
        sp2 = StudentProfileFactory(school=self.school, mode='school_linked')
        sp3 = StudentProfileFactory(school=self.school, mode='school_linked')
        RIASECAssessment.objects.create(student_profile=sp1)
        c = CounselorFactory(school=self.school)
        CounselorAssignmentFactory(counselor=c, student_profile=sp1, school=self.school)
        response = self.client.get('/api/v1/school-admin/stats/')
        data = response.data['data']
        assert data['total_students'] == 3
        assert data['total_counselors'] == 2
        assert data['assessed'] == 1
        assert data['unassigned'] == 2


class TestSchoolAssignmentView:
    def setup_method(self):
        self.client = APIClient()
        self.school = SchoolFactory(name='Starehe Boys', county='nairobi', school_code='NAI006')
        self.admin = SchoolAdminFactory(school=self.school)
        self.client.force_authenticate(self.admin)

    def test_assign_student_to_counselor(self):
        sp = StudentProfileFactory(school=self.school, mode='school_linked')
        c = CounselorFactory(school=self.school)
        response = self.client.post('/api/v1/school-admin/assignments/', {
            'student_id': sp.user.id,
            'counselor_id': c.id,
        })
        assert response.status_code == 201
        assert CounselorAssignment.objects.filter(
            student_profile=sp, counselor=c, is_active=True,
        ).exists()

    def test_reassign_deactivates_old(self):
        sp = StudentProfileFactory(school=self.school, mode='school_linked')
        c1 = CounselorFactory(school=self.school)
        c2 = CounselorFactory(school=self.school)
        old = CounselorAssignmentFactory(counselor=c1, student_profile=sp, school=self.school)
        response = self.client.post('/api/v1/school-admin/assignments/', {
            'student_id': sp.user.id,
            'counselor_id': c2.id,
        })
        assert response.status_code == 201
        old.refresh_from_db()
        assert old.is_active is False
        assert CounselorAssignment.objects.filter(
            student_profile=sp, counselor=c2, is_active=True,
        ).exists()

    def test_assign_student_not_at_school(self):
        sp = StudentProfileFactory(school=SchoolFactory(), mode='school_linked')
        c = CounselorFactory(school=self.school)
        response = self.client.post('/api/v1/school-admin/assignments/', {
            'student_id': sp.user.id,
            'counselor_id': c.id,
        })
        assert response.status_code == 404

    def test_assign_counselor_not_at_school(self):
        sp = StudentProfileFactory(school=self.school, mode='school_linked')
        c = CounselorFactory(school=SchoolFactory())
        response = self.client.post('/api/v1/school-admin/assignments/', {
            'student_id': sp.user.id,
            'counselor_id': c.id,
        })
        assert response.status_code == 404

    def test_remove_assignment(self):
        sp = StudentProfileFactory(school=self.school, mode='school_linked')
        c = CounselorFactory(school=self.school)
        a = CounselorAssignmentFactory(counselor=c, student_profile=sp, school=self.school)
        response = self.client.post(f'/api/v1/school-admin/assignments/{a.id}/remove/')
        assert response.status_code == 200
        a.refresh_from_db()
        assert a.is_active is False

    def test_remove_assignment_wrong_school(self):
        other_school = SchoolFactory()
        sp = StudentProfileFactory(school=other_school, mode='school_linked')
        c = CounselorFactory(school=other_school)
        a = CounselorAssignmentFactory(counselor=c, student_profile=sp, school=other_school)
        response = self.client.post(f'/api/v1/school-admin/assignments/{a.id}/remove/')
        assert response.status_code == 404
