import pytest
from rest_framework.test import APIClient

from riasec.models import RIASECAssessment
from tests.factories import (
    CBCGradeFactory,
    StudentProfileFactory,
    StudentSubjectFactory,
    SubjectFactory,
    UserFactory,
    VerifiedUserFactory,
)


pytestmark = pytest.mark.django_db

EVIDENCE_URL = '/api/v1/students/evidence-summary/'
GRADES_URL = '/api/v1/students/grades/summary/'


class TestStudentSummaryPermissions:
    @pytest.mark.parametrize('url', [EVIDENCE_URL, GRADES_URL])
    def test_unauthenticated_request_is_rejected(self, url):
        assert APIClient().get(url).status_code == 401

    @pytest.mark.parametrize('url', [EVIDENCE_URL, GRADES_URL])
    def test_non_student_is_rejected(self, url):
        client = APIClient()
        client.force_authenticate(VerifiedUserFactory(role='counselor'))

        assert client.get(url).status_code == 403

    @pytest.mark.parametrize('url', [EVIDENCE_URL, GRADES_URL])
    def test_unverified_student_is_rejected(self, url):
        user = UserFactory(role='student', is_email_verified=False)
        StudentProfileFactory(user=user)
        client = APIClient()
        client.force_authenticate(user)

        assert client.get(url).status_code == 403


class TestEvidenceSummaryView:
    def setup_method(self):
        self.profile = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
            grade=9,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.profile.user)

    def test_returns_complete_summary_contract(self):
        response = self.client.get(EVIDENCE_URL)

        assert response.status_code == 200
        assert set(response.data['data']) == {
            'profile_completion',
            'academic_evidence',
            'assessment',
            'saved_combination_count',
            'plan_status',
            'next_action',
        }
        assert response.data['data']['saved_combination_count'] == 0
        assert response.data['data']['plan_status'] == 'not_started'

    def test_incomplete_profile_is_first_next_action(self):
        response = self.client.get(EVIDENCE_URL)

        assert response.data['data']['profile_completion'] == {
            'status': 'incomplete',
            'completed_fields': 0,
            'total_fields': 3,
            'percent': 0,
            'missing_fields': ['bio', 'date_of_birth', 'career_interests'],
        }
        assert response.data['data']['next_action']['code'] == 'complete_profile'

    def test_academic_evidence_is_next_after_profile_completion(self):
        self.profile.bio = 'Interested in science and design.'
        self.profile.date_of_birth = '2011-01-10'
        self.profile.career_interests = 'Engineering'
        self.profile.save(
            update_fields=['bio', 'date_of_birth', 'career_interests']
        )

        response = self.client.get(EVIDENCE_URL)

        assert response.data['data']['profile_completion']['status'] == 'complete'
        assert response.data['data']['academic_evidence']['status'] == 'not_started'
        assert response.data['data']['next_action']['code'] == 'add_academic_evidence'

    def test_assessment_status_includes_version_slot(self):
        assessment_record = RIASECAssessment.objects.create(student_profile=self.profile)

        response = self.client.get(EVIDENCE_URL)

        assessment = response.data['data']['assessment']
        assert assessment['status'] == 'complete'
        assert assessment['instrument_version'] == assessment_record.instrument_version
        assert assessment['submitted_at'] is not None

    def test_next_action_advances_to_explore_after_required_evidence(self):
        self.profile.bio = 'Interested in science and design.'
        self.profile.date_of_birth = '2011-01-10'
        self.profile.career_interests = 'Engineering'
        self.profile.save(
            update_fields=['bio', 'date_of_birth', 'career_interests']
        )
        for index in range(3):
            enrollment = StudentSubjectFactory(
                student_profile=self.profile,
                subject=SubjectFactory(
                    code=f'EVD{index}9',
                    grade=9,
                ),
            )
            CBCGradeFactory(student_subject=enrollment)
        RIASECAssessment.objects.create(student_profile=self.profile)

        response = self.client.get(EVIDENCE_URL)

        assert response.data['data']['academic_evidence']['status'] == 'ready'
        assert response.data['data']['next_action']['code'] == 'explore_combinations'

    def test_query_count_is_bounded(self, django_assert_num_queries):
        for index in range(5):
            enrollment = StudentSubjectFactory(
                student_profile=self.profile,
                subject=SubjectFactory(code=f'QRY{index}9', grade=9),
            )
            CBCGradeFactory(student_subject=enrollment)

        with django_assert_num_queries(3):
            response = self.client.get(EVIDENCE_URL)

        assert response.status_code == 200


class TestGradeSummaryView:
    def setup_method(self):
        self.profile = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
            grade=9,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.profile.user)

    def test_returns_empty_summary_without_enrolments(self):
        response = self.client.get(GRADES_URL)

        assert response.status_code == 200
        assert response.data['data'] == {
            'status': 'not_started',
            'total_subjects': 0,
            'subjects_with_evidence': 0,
            'total_grade_records': 0,
            'subjects': [],
        }

    def test_returns_all_subjects_and_grades_in_one_response(self):
        first = StudentSubjectFactory(
            student_profile=self.profile,
            subject=SubjectFactory(code='GSUM19', name='Mathematics'),
        )
        second = StudentSubjectFactory(
            student_profile=self.profile,
            subject=SubjectFactory(code='GSUM29', name='English'),
        )
        CBCGradeFactory(student_subject=first, term=1, year=2026, level='ME1')
        CBCGradeFactory(student_subject=first, term=2, year=2026, level='EE2')

        response = self.client.get(GRADES_URL)

        data = response.data['data']
        assert data['status'] == 'in_progress'
        assert data['total_subjects'] == 2
        assert data['subjects_with_evidence'] == 1
        assert data['total_grade_records'] == 2
        mathematics = next(
            item for item in data['subjects'] if item['subject']['code'] == 'GSUM19'
        )
        assert [grade['term'] for grade in mathematics['grades']] == [1, 2]
        assert mathematics['latest_grade']['level'] == 'EE2'
        assert next(
            item for item in data['subjects'] if item['subject']['code'] == 'GSUM29'
        )['latest_grade'] is None

    def test_ready_when_three_or_more_subjects_all_have_evidence(self):
        for index in range(3):
            enrollment = StudentSubjectFactory(
                student_profile=self.profile,
                subject=SubjectFactory(code=f'RDY{index}9'),
            )
            CBCGradeFactory(student_subject=enrollment)

        response = self.client.get(GRADES_URL)

        assert response.data['data']['status'] == 'ready'

    def test_query_count_does_not_grow_per_subject(
        self,
        django_assert_num_queries,
    ):
        for index in range(6):
            enrollment = StudentSubjectFactory(
                student_profile=self.profile,
                subject=SubjectFactory(code=f'BND{index}9'),
            )
            CBCGradeFactory(student_subject=enrollment, term=1)
            CBCGradeFactory(student_subject=enrollment, term=2)

        with django_assert_num_queries(3):
            response = self.client.get(GRADES_URL)

        assert response.status_code == 200
        assert len(response.data['data']['subjects']) == 6
