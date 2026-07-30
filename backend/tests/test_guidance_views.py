import pytest
from rest_framework.test import APIClient

from guidance.models import FrameworkVersion, SubjectCombination
from tests.factories import (
    FrameworkVersionFactory,
    PathwayTrackFactory,
    SubjectCombinationFactory,
)


pytestmark = pytest.mark.django_db

FRAMEWORK_URL = '/api/v1/guidance/framework/current/'
PATHWAYS_URL = '/api/v1/guidance/pathways/'
COMBINATIONS_URL = '/api/v1/guidance/combinations/'


class TestPublicGuidancePermissions:
    @pytest.mark.parametrize(
        'url',
        [FRAMEWORK_URL, PATHWAYS_URL, COMBINATIONS_URL],
    )
    def test_reference_endpoints_are_public(self, url):
        response = APIClient().get(url)

        assert response.status_code == 200
        assert response.data['error'] is None

    def test_invalid_auth_cookie_does_not_block_public_reference_data(self):
        client = APIClient()
        client.cookies['access_token'] = 'not-a-valid-token'

        response = client.get(COMBINATIONS_URL)

        assert response.status_code == 200


class TestCurrentFrameworkView:
    def test_returns_source_and_effective_date(self):
        response = APIClient().get(FRAMEWORK_URL)

        assert response.status_code == 200
        assert response.data['data']['code'] == 'CBC-SS-PILOT-2026'
        assert response.data['data']['source_url'].startswith('https://')
        assert response.data['data']['effective_date'] == '2026-01-01'

    def test_returns_404_when_there_is_no_active_framework(self):
        FrameworkVersion.objects.update(is_active=False)

        response = APIClient().get(FRAMEWORK_URL)

        assert response.status_code == 404


class TestPathwayListView:
    def test_returns_three_pathways_with_active_tracks(self):
        response = APIClient().get(PATHWAYS_URL)

        data = response.data['data']
        assert len(data) == 3
        assert {pathway['name'] for pathway in data} == {
            'STEM',
            'Social Sciences',
            'Arts & Sports Science',
        }
        assert sum(len(pathway['tracks']) for pathway in data) == 7
        assert all(track['is_active'] for pathway in data for track in pathway['tracks'])

    def test_excludes_tracks_from_inactive_frameworks(self):
        inactive_framework = FrameworkVersionFactory(is_active=False)
        PathwayTrackFactory(framework_version=inactive_framework, code='OLD-TRACK')

        response = APIClient().get(PATHWAYS_URL)

        returned_codes = {
            track['code']
            for pathway in response.data['data']
            for track in pathway['tracks']
        }
        assert 'OLD-TRACK' not in returned_codes

    def test_query_count_is_bounded(self, django_assert_num_queries):
        with django_assert_num_queries(3):
            response = APIClient().get(PATHWAYS_URL)

        assert response.status_code == 200


class TestCombinationListView:
    def test_returns_only_active_current_framework_combinations(self):
        current = FrameworkVersion.objects.current()
        inactive = SubjectCombination.objects.filter(
            framework_version=current
        ).first()
        inactive.is_active = False
        inactive.save(update_fields=['is_active'])
        old_framework = FrameworkVersionFactory(is_active=False)
        old_track = PathwayTrackFactory(framework_version=old_framework)
        SubjectCombinationFactory(
            framework_version=old_framework,
            track=old_track,
            code='OLD-COMBO',
        )

        response = APIClient().get(COMBINATIONS_URL)

        returned_codes = {item['code'] for item in response.data['data']}
        assert inactive.code not in returned_codes
        assert 'OLD-COMBO' not in returned_codes
        assert len(returned_codes) == 9

    def test_payload_contains_track_subjects_framework_and_offered_schools(self):
        response = APIClient().get(COMBINATIONS_URL)

        combination = response.data['data'][0]
        assert set(combination) == {
            'id',
            'code',
            'title',
            'description',
            'related_routes',
            'framework',
            'track',
            'subjects',
            'offered_schools',
        }
        assert len(combination['subjects']) == 3
        assert combination['track']['pathway']['name']
        assert combination['framework']['source_url'].startswith('https://')
        assert combination['related_routes']

    @pytest.mark.parametrize(
        ('params', 'expected_codes'),
        [
            ({'pathway': 'STEM'}, {'ST1042', 'ST2007', 'ST2067', 'ST3074'}),
            ({'track': 'SPORTS-RECREATION'}, {'AS2009'}),
            ({'county': 'nyeri'}, {'ST1042', 'ST2067', 'SS2033', 'AS1049'}),
            (
                {'school': 'PILOT-MUR-001'},
                {'ST2067', 'ST3074', 'SS1006', 'AS1021'},
            ),
            ({'search': 'media'}, {'ST3074'}),
        ],
    )
    def test_filters(self, params, expected_codes):
        response = APIClient().get(COMBINATIONS_URL, params)

        assert response.status_code == 200
        assert {item['code'] for item in response.data['data']} == expected_codes

    def test_query_count_is_bounded(self, django_assert_num_queries):
        with django_assert_num_queries(3):
            response = APIClient().get(COMBINATIONS_URL)

        assert response.status_code == 200
        assert len(response.data['data']) == 10


class TestCombinationDetailView:
    def test_returns_active_combination(self):
        combination = SubjectCombination.objects.get(code='ST1042')

        response = APIClient().get(f'{COMBINATIONS_URL}{combination.pk}/')

        assert response.status_code == 200
        assert response.data['data']['code'] == 'ST1042'

    def test_inactive_combination_returns_404(self):
        combination = SubjectCombination.objects.get(code='ST1042')
        combination.is_active = False
        combination.save(update_fields=['is_active'])

        response = APIClient().get(f'{COMBINATIONS_URL}{combination.pk}/')

        assert response.status_code == 404
