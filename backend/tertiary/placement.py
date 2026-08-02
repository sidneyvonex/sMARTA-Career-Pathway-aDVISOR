from typing import Any, Mapping, Protocol, TypedDict

from .models import Programme


class PlacementFrameworkMetadata(TypedDict):
    requested_version: str
    catalogue_framework: str
    admission_cycle: str


class PlacementSourceMetadata(TypedDict):
    url: str
    effective_date: str
    verification_status: str
    source_scope: str
    external_key: str


class PlacementEvaluation(TypedDict):
    adapter_version: str
    status: str
    framework: PlacementFrameworkMetadata
    source: PlacementSourceMetadata
    explanation: str


class PlacementEvaluator(Protocol):
    """Versioned boundary for a future authoritative placement integration."""

    adapter_version: str

    def evaluate(
        self,
        programme: Programme,
        learner_evidence: Mapping[str, Any],
        framework_version: str,
    ) -> PlacementEvaluation:
        ...


class OfficialCriteriaUnavailableEvaluator:
    """Release adapter: report the authoritative-data gap without inference."""

    adapter_version = 'v1'

    def evaluate(
        self,
        programme: Programme,
        learner_evidence: Mapping[str, Any],
        framework_version: str,
    ) -> PlacementEvaluation:
        del learner_evidence
        return {
            'adapter_version': self.adapter_version,
            'status': 'official_criteria_unavailable',
            'framework': {
                'requested_version': framework_version,
                'catalogue_framework': programme.education_framework,
                'admission_cycle': programme.admission_cycle,
            },
            'source': {
                'url': programme.source_url,
                'effective_date': programme.effective_date.isoformat(),
                'verification_status': programme.verification_status,
                'source_scope': programme.source_scope,
                'external_key': programme.external_key,
            },
            'explanation': (
                'Official placement criteria are unavailable for this framework and '
                'catalogue reference. Smarta Shauri does not substitute a formula or threshold.'
            ),
        }
