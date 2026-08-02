from rest_framework import serializers

from .models import (
    HistoricalAdmissionReference,
    Institution,
    LearnerEducationGoal,
    Programme,
    ProgrammeSubjectReference,
)


PROVENANCE_FIELDS = (
    'source_scope',
    'external_key',
    'source_url',
    'education_framework',
    'admission_cycle',
    'effective_date',
    'verification_status',
)


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = (
            'id', 'name', 'institution_type', 'county', 'website_url',
            *PROVENANCE_FIELDS,
        )


class ProgrammeSummarySerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)

    class Meta:
        model = Programme
        fields = (
            'id', 'institution', 'code', 'name', 'description',
            *PROVENANCE_FIELDS,
        )


class ProgrammeSubjectReferenceSerializer(serializers.ModelSerializer):
    advisory_label = serializers.SerializerMethodField()

    class Meta:
        model = ProgrammeSubjectReference
        fields = (
            'id', 'subject_code', 'subject_name', 'mapping_kind', 'notes',
            'advisory_label', *PROVENANCE_FIELDS,
        )

    def get_advisory_label(self, _instance):
        return 'Exploration reference only; this does not determine admission.'


class HistoricalAdmissionReferenceSerializer(serializers.ModelSerializer):
    reference_status = serializers.SerializerMethodField()
    reference_only = serializers.SerializerMethodField()

    class Meta:
        model = HistoricalAdmissionReference
        fields = (
            'id', 'requirement_summary', 'reference_status', 'reference_only',
            *PROVENANCE_FIELDS,
        )

    def get_reference_status(self, _instance):
        return 'historical_reference'

    def get_reference_only(self, _instance):
        return True


class ProgrammeDetailSerializer(ProgrammeSummarySerializer):
    subject_references = ProgrammeSubjectReferenceSerializer(many=True, read_only=True)
    historical_admission_references = HistoricalAdmissionReferenceSerializer(
        many=True, read_only=True
    )

    class Meta(ProgrammeSummarySerializer.Meta):
        fields = ProgrammeSummarySerializer.Meta.fields + (
            'subject_references', 'historical_admission_references',
        )


class LearnerEducationGoalSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    programme = ProgrammeSummarySerializer(read_only=True)

    class Meta:
        model = LearnerEducationGoal
        fields = (
            'id', 'institution', 'programme', 'kind', 'priority', 'created_by',
            'created_at', 'updated_at',
        )


class LearnerEducationGoalWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnerEducationGoal
        fields = ('institution', 'programme', 'kind', 'priority')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        institution = attrs.get('institution', getattr(self.instance, 'institution', None))
        programme = attrs.get('programme', getattr(self.instance, 'programme', None))
        kind = attrs.get('kind', getattr(self.instance, 'kind', None))
        priority = attrs.get('priority', getattr(self.instance, 'priority', None))
        if programme is not None and programme.institution_id != institution.pk:
            raise serializers.ValidationError(
                {'programme': 'The programme must belong to the selected institution.'}
            )
        if kind == LearnerEducationGoal.KIND_PRIMARY and priority != 1:
            raise serializers.ValidationError({'priority': 'A primary goal uses priority 1.'})
        if kind == LearnerEducationGoal.KIND_ALTERNATIVE and priority not in (1, 2):
            raise serializers.ValidationError(
                {'priority': 'An alternative goal uses priority 1 or 2.'}
            )
        return attrs
