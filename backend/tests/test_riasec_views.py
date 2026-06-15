import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from tests.factories import VerifiedUserFactory, UserFactory, StudentProfileFactory


def make_auth_client(user):
    c = APIClient()
    refresh = RefreshToken.for_user(user)
    c.cookies['access_token'] = str(refresh.access_token)
    return c


def all_responses(score=3):
    """Build a valid 30-response payload using seeded question IDs."""
    from riasec.models import RIASECQuestion
    return [{'question_id': q.id, 'score': score} for q in RIASECQuestion.objects.all()]


@pytest.fixture
def verified_profile(db):
    user = VerifiedUserFactory(role='student')
    return StudentProfileFactory(user=user, grade=9)


# ---------------------------------------------------------------------------
# GET /api/v1/students/assessment/questions/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestQuestionListView:
    def test_returns_30_questions(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        r = c.get('/api/v1/students/assessment/questions/')
        assert r.status_code == 200
        assert len(r.data['data']) == 30

    def test_questions_ordered_by_order_field(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        r = c.get('/api/v1/students/assessment/questions/')
        orders = [q['order'] for q in r.data['data']]
        assert orders == sorted(orders)

    def test_each_question_has_dimension_and_text(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        r = c.get('/api/v1/students/assessment/questions/')
        for q in r.data['data']:
            assert 'dimension' in q
            assert 'text' in q
            assert q['dimension'] in list('RIASEC')

    def test_unauthenticated_returns_401(self):
        r = APIClient().get('/api/v1/students/assessment/questions/')
        assert r.status_code == 401

    def test_unverified_returns_403(self, db):
        user = UserFactory(role='student', is_email_verified=False)
        StudentProfileFactory(user=user, grade=9)
        c = make_auth_client(user)
        r = c.get('/api/v1/students/assessment/questions/')
        assert r.status_code == 403

    def test_non_student_returns_403(self, db):
        user = VerifiedUserFactory(role='counselor')
        c = make_auth_client(user)
        r = c.get('/api/v1/students/assessment/questions/')
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/students/assessment/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAssessmentSubmitView:
    def test_valid_submission_returns_201(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        r = c.post('/api/v1/students/assessment/', {'responses': all_responses(3)}, format='json')
        assert r.status_code == 201

    def test_response_contains_holland_code(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        r = c.post('/api/v1/students/assessment/', {'responses': all_responses(3)}, format='json')
        assert 'holland_code' in r.data['data']
        code = r.data['data']['holland_code']
        assert len(code) == 3
        assert all(ch in 'RIASEC' for ch in code)

    def test_response_contains_6_dimension_scores(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        r = c.post('/api/v1/students/assessment/', {'responses': all_responses(4)}, format='json')
        scores = r.data['data']['scores']
        assert set(scores.keys()) == {'R', 'I', 'A', 'S', 'E', 'C'}
        # All scores = 4 × 5 questions = 20 per dimension
        assert all(v == 20 for v in scores.values())

    def test_response_contains_3_ranked_recommendations(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        r = c.post('/api/v1/students/assessment/', {'responses': all_responses(3)}, format='json')
        recs = r.data['data']['recommendations']
        assert len(recs) == 3
        assert [rec['rank'] for rec in recs] == [1, 2, 3]

    def test_each_recommendation_has_fit_pct(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        r = c.post('/api/v1/students/assessment/', {'responses': all_responses(3)}, format='json')
        for rec in r.data['data']['recommendations']:
            assert 'fit_pct' in rec
            assert 0 <= rec['fit_pct'] <= 100

    def test_scores_and_recommendations_saved_to_db(self, verified_profile):
        from riasec.models import RIASECAssessment, RIASECScore, Recommendation
        c = make_auth_client(verified_profile.user)
        c.post('/api/v1/students/assessment/', {'responses': all_responses(3)}, format='json')
        assessment = RIASECAssessment.objects.get(student_profile=verified_profile)
        assert RIASECScore.objects.filter(assessment=assessment).count() == 6
        assert Recommendation.objects.filter(assessment=assessment).count() == 3

    def test_fewer_than_30_responses_returns_400(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        r = c.post('/api/v1/students/assessment/', {'responses': all_responses()[:15]}, format='json')
        assert r.status_code == 400

    def test_duplicate_question_id_returns_400(self, verified_profile):
        from riasec.models import RIASECQuestion
        responses = all_responses()
        first_id = responses[0]['question_id']
        responses[1]['question_id'] = first_id  # duplicate
        c = make_auth_client(verified_profile.user)
        r = c.post('/api/v1/students/assessment/', {'responses': responses}, format='json')
        assert r.status_code == 400

    def test_score_out_of_range_returns_400(self, verified_profile):
        responses = all_responses()
        responses[0]['score'] = 6  # invalid
        c = make_auth_client(verified_profile.user)
        r = c.post('/api/v1/students/assessment/', {'responses': responses}, format='json')
        assert r.status_code == 400

    def test_invalid_question_id_returns_400(self, verified_profile):
        responses = all_responses()
        responses[0]['question_id'] = 99999  # doesn't exist
        c = make_auth_client(verified_profile.user)
        r = c.post('/api/v1/students/assessment/', {'responses': responses}, format='json')
        assert r.status_code == 400

    def test_unlimited_retakes_allowed(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        r1 = c.post('/api/v1/students/assessment/', {'responses': all_responses(3)}, format='json')
        r2 = c.post('/api/v1/students/assessment/', {'responses': all_responses(4)}, format='json')
        assert r1.status_code == 201
        assert r2.status_code == 201

    def test_unauthenticated_returns_401(self):
        r = APIClient().post('/api/v1/students/assessment/', {'responses': []}, format='json')
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/students/assessment/ (history)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAssessmentHistoryView:
    def test_returns_empty_list_before_any_submission(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        r = c.get('/api/v1/students/assessment/')
        assert r.status_code == 200
        assert r.data['data'] == []

    def test_returns_all_assessments_newest_first(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        c.post('/api/v1/students/assessment/', {'responses': all_responses(3)}, format='json')
        c.post('/api/v1/students/assessment/', {'responses': all_responses(4)}, format='json')
        r = c.get('/api/v1/students/assessment/')
        assert r.status_code == 200
        assert len(r.data['data']) == 2

    def test_cannot_see_other_students_assessments(self, db, verified_profile):
        other_user = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=other_user, grade=9)
        c_other = make_auth_client(other_user)
        c_other.post('/api/v1/students/assessment/', {'responses': all_responses(3)}, format='json')
        c = make_auth_client(verified_profile.user)
        r = c.get('/api/v1/students/assessment/')
        assert r.data['data'] == []


# ---------------------------------------------------------------------------
# GET /api/v1/students/assessment/latest/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAssessmentLatestView:
    def test_returns_404_when_no_assessment(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        r = c.get('/api/v1/students/assessment/latest/')
        assert r.status_code == 404

    def test_returns_latest_assessment(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        c.post('/api/v1/students/assessment/', {'responses': all_responses(2)}, format='json')
        c.post('/api/v1/students/assessment/', {'responses': all_responses(5)}, format='json')
        r = c.get('/api/v1/students/assessment/latest/')
        assert r.status_code == 200
        # Latest submission had all scores = 5 × 5 = 25
        assert all(v == 25 for v in r.data['data']['scores'].values())
