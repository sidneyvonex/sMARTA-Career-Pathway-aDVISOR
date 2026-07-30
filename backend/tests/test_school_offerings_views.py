import pytest
from rest_framework.test import APIClient

from guidance.models import FrameworkVersion, SchoolOffering, SubjectCombination
from system_admin.models import AuditLog
from tests.factories import (
    FrameworkVersionFactory,
    PathwayTrackFactory,
    SchoolAdminFactory,
    SchoolFactory,
    SchoolOfferingFactory,
    SubjectCombinationFactory,
    UserFactory,
    VerifiedUserFactory,
)


pytestmark = pytest.mark.django_db

OFFERINGS_URL = '/api/v1/school-admin/offerings/'


class TestSchoolOfferingsPermissions:
    def test_unauthenticated_request_is_rejected(self):
        assert APIClient().get(OFFERINGS_URL).status_code == 401

    def test_non_school_admin_is_rejected(self):
        client = APIClient()
        client.force_authenticate(VerifiedUserFactory(role='counselor'))

        assert client.get(OFFERINGS_URL).status_code == 403

    def test_unverified_school_admin_is_rejected(self):
        school = SchoolFactory()
        admin = UserFactory(
            role='school_admin',
            school=school,
            is_email_verified=False,
        )
        client = APIClient()
        client.force_authenticate(admin)

        assert client.get(OFFERINGS_URL).status_code == 403

    def test_admin_without_school_gets_404(self):
        client = APIClient()
        client.force_authenticate(SchoolAdminFactory(school=None))

        assert client.get(OFFERINGS_URL).status_code == 404

    def test_inactive_school_cannot_manage_offerings(self):
        school = SchoolFactory(is_active=False)
        client = APIClient()
        client.force_authenticate(SchoolAdminFactory(school=school))

        assert client.get(OFFERINGS_URL).status_code == 403
        assert (
            client.put(
                OFFERINGS_URL,
                {'combination_ids': []},
                format='json',
            ).status_code
            == 403
        )


class TestSchoolOfferingsRead:
    def setup_method(self):
        self.school = SchoolFactory(county='kiambu')
        self.admin = SchoolAdminFactory(school=self.school)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_returns_only_active_current_offerings_for_own_school(self):
        selected = SubjectCombination.objects.get(code='ST1042')
        inactive = SubjectCombination.objects.get(code='ST2007')
        inactive.is_active = False
        inactive.save(update_fields=['is_active'])
        SchoolOfferingFactory(school=self.school, combination=selected)
        SchoolOfferingFactory(school=self.school, combination=inactive)
        SchoolOfferingFactory(
            school=SchoolFactory(),
            combination=SubjectCombination.objects.get(code='AS2009'),
        )

        response = self.client.get(OFFERINGS_URL)

        assert response.status_code == 200
        assert response.data['data']['combination_ids'] == [selected.id]
        assert [item['code'] for item in response.data['data']['offerings']] == [
            'ST1042'
        ]

    def test_response_identifies_school_and_includes_source_metadata(self):
        combination = SubjectCombination.objects.get(code='AS2009')
        SchoolOfferingFactory(school=self.school, combination=combination)

        response = self.client.get(OFFERINGS_URL)

        data = response.data['data']
        assert data['school'] == {
            'id': self.school.id,
            'school_code': self.school.school_code,
            'name': self.school.name,
            'county': self.school.county,
        }
        assert data['offerings'][0]['framework']['source_url'].startswith('https://')


class TestSchoolOfferingsReplace:
    def setup_method(self):
        self.school = SchoolFactory(county='nyeri')
        self.admin = SchoolAdminFactory(school=self.school)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.original = [
            SubjectCombination.objects.get(code='ST1042'),
            SubjectCombination.objects.get(code='AS2009'),
        ]
        for combination in self.original:
            SchoolOfferingFactory(school=self.school, combination=combination)

    def test_put_replaces_complete_selection(self):
        replacements = [
            SubjectCombination.objects.get(code='SS2019'),
            SubjectCombination.objects.get(code='AS1049'),
        ]

        response = self.client.put(
            OFFERINGS_URL,
            {'combination_ids': [item.id for item in replacements]},
            format='json',
        )

        assert response.status_code == 200
        assert set(response.data['data']['combination_ids']) == {
            item.id for item in replacements
        }
        assert set(
            SchoolOffering.objects.filter(school=self.school).values_list(
                'combination_id',
                flat=True,
            )
        ) == {item.id for item in replacements}
        event = AuditLog.objects.get(action='school_offerings_changed')
        assert event.actor == self.admin
        assert event.target_type == 'offering'
        assert event.target_id == self.school.id
        assert set(event.details['previous_combination_ids']) == {
            item.id for item in self.original
        }
        assert set(event.details['combination_ids']) == {
            item.id for item in replacements
        }

    def test_empty_list_clears_all_offerings(self):
        response = self.client.put(
            OFFERINGS_URL,
            {'combination_ids': []},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['data']['combination_ids'] == []
        assert not SchoolOffering.objects.filter(school=self.school).exists()

    @pytest.mark.parametrize(
        'payload',
        [
            {},
            {'combination_ids': 'ST1042'},
            {'combination_ids': [1, 1]},
            {'combination_ids': [None]},
        ],
    )
    def test_invalid_replace_shape_is_rejected_without_mutation(self, payload):
        original_ids = {
            combination.id for combination in self.original
        }

        response = self.client.put(OFFERINGS_URL, payload, format='json')

        assert response.status_code == 400
        assert set(
            SchoolOffering.objects.filter(school=self.school).values_list(
                'combination_id',
                flat=True,
            )
        ) == original_ids

    def test_nonexistent_combination_is_rejected_without_mutation(self):
        response = self.client.put(
            OFFERINGS_URL,
            {'combination_ids': [999999]},
            format='json',
        )

        assert response.status_code == 400
        assert SchoolOffering.objects.filter(school=self.school).count() == 2

    def test_inactive_combination_is_rejected_without_mutation(self):
        combination = SubjectCombination.objects.get(code='SS2033')
        combination.is_active = False
        combination.save(update_fields=['is_active'])

        response = self.client.put(
            OFFERINGS_URL,
            {'combination_ids': [combination.id]},
            format='json',
        )

        assert response.status_code == 400
        assert SchoolOffering.objects.filter(school=self.school).count() == 2

    def test_combination_from_inactive_framework_is_rejected(self):
        inactive_framework = FrameworkVersionFactory(is_active=False)
        inactive_track = PathwayTrackFactory(framework_version=inactive_framework)
        old_combination = SubjectCombinationFactory(
            framework_version=inactive_framework,
            track=inactive_track,
        )

        response = self.client.put(
            OFFERINGS_URL,
            {'combination_ids': [old_combination.id]},
            format='json',
        )

        assert response.status_code == 400
        assert SchoolOffering.objects.filter(school=self.school).count() == 2
