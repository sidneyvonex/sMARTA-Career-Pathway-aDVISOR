from rest_framework import serializers

from accounts.models import School
from riasec.models import Pathway
from students.models import Subject

from .models import (
    FrameworkVersion,
    LearnerCombinationChoice,
    LearnerPlan,
    PlanMilestone,
    PathwayTrack,
    SubjectCombination,
)


class FrameworkVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrameworkVersion
        fields = (
            'id',
            'code',
            'title',
            'description',
            'source_url',
            'effective_date',
            'is_active',
        )


class FrameworkSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = FrameworkVersion
        fields = ('code', 'title', 'source_url', 'effective_date')


class PathwaySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pathway
        fields = ('id', 'name', 'description')


class PathwayTrackSerializer(serializers.ModelSerializer):
    pathway = PathwaySummarySerializer(read_only=True)

    class Meta:
        model = PathwayTrack
        fields = ('id', 'code', 'name', 'description', 'is_active', 'pathway')


class PathwayCatalogueSerializer(serializers.ModelSerializer):
    tracks = serializers.SerializerMethodField()

    class Meta:
        model = Pathway
        fields = ('id', 'name', 'description', 'tracks')

    def get_tracks(self, obj):
        tracks = getattr(obj, 'active_framework_tracks', ())
        return PathwayTrackSerializer(tracks, many=True).data


class SubjectSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'code', 'name', 'grade', 'category')


class SchoolSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ('id', 'school_code', 'name', 'county')


class SchoolOfferingReplaceSerializer(serializers.Serializer):
    combination_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )

    def validate_combination_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Combination IDs must be unique.'
            )
        return value


class SubjectCombinationSerializer(serializers.ModelSerializer):
    framework = FrameworkSummarySerializer(
        source='framework_version',
        read_only=True,
    )
    track = PathwayTrackSerializer(read_only=True)
    subjects = serializers.SerializerMethodField()
    offered_schools = serializers.SerializerMethodField()

    class Meta:
        model = SubjectCombination
        fields = (
            'id',
            'code',
            'title',
            'description',
            'related_routes',
            'framework',
            'track',
            'subjects',
            'offered_schools',
        )

    def get_subjects(self, obj):
        return SubjectSummarySerializer(obj.subjects, many=True).data

    def get_offered_schools(self, obj):
        offerings = getattr(obj, 'active_school_offerings', ())
        schools = [offering.school for offering in offerings]
        return SchoolSummarySerializer(schools, many=True).data


class LearnerCombinationChoiceCreateSerializer(serializers.Serializer):
    combination_id = serializers.IntegerField(min_value=1)
    learner_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        default='',
    )


class LearnerCombinationChoiceSerializer(serializers.ModelSerializer):
    combination = SubjectCombinationSerializer(read_only=True)

    class Meta:
        model = LearnerCombinationChoice
        fields = (
            'id',
            'combination',
            'status',
            'learner_reason',
            'created_at',
            'updated_at',
        )


class PlanMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanMilestone
        fields = (
            'id',
            'title',
            'due_date',
            'is_complete',
            'completed_at',
            'position',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'completed_at', 'created_at', 'updated_at')


class LearnerPlanSerializer(serializers.ModelSerializer):
    provisional_choice = LearnerCombinationChoiceSerializer(read_only=True)
    milestones = PlanMilestoneSerializer(many=True, read_only=True)

    class Meta:
        model = LearnerPlan
        fields = (
            'id',
            'provisional_choice',
            'learner_reason',
            'review_status',
            'reviewed_at',
            'milestones',
            'created_at',
            'updated_at',
        )


class LearnerPlanUpdateSerializer(serializers.Serializer):
    learner_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
    )
    review_status = serializers.ChoiceField(
        required=False,
        choices=(LearnerPlan.STATUS_DRAFT, LearnerPlan.STATUS_READY),
    )
