from datetime import date
from rest_framework import serializers
from accounts.models import StudentProfile
from .models import (
    AcademicGoal,
    CBCGrade,
    GRADE_LEVEL_CHOICES,
    PerformanceLevelDefinition,
    StudentSubject,
    Subject,
)


class StudentProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    county = serializers.CharField(source='user.county', read_only=True)

    class Meta:
        model = StudentProfile
        fields = (
            'id', 'email', 'first_name', 'last_name', 'county',
            'grade', 'mode', 'school_membership_status',
            'bio', 'date_of_birth', 'career_interests', 'photo_url',
        )
        read_only_fields = (
            'id', 'email', 'first_name', 'last_name', 'county',
            'grade', 'mode', 'school_membership_status', 'photo_url',
        )

    def validate_bio(self, value):
        if len(value) > 500:
            raise serializers.ValidationError('Bio must be 500 characters or less.')
        return value

    def validate_career_interests(self, value):
        if len(value) > 500:
            raise serializers.ValidationError('Career interests must be 500 characters or less.')
        return value


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = (
            'id',
            'name',
            'code',
            'continuity_code',
            'grade',
            'category',
            'is_active',
            'is_selectable_in_combination',
        )


class StudentSubjectSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.filter(is_active=True), source='subject', write_only=True
    )

    class Meta:
        model = StudentSubject
        fields = (
            'id',
            'subject',
            'subject_id',
            'continuity_code',
            'academic_grade',
            'academic_year',
            'is_active',
            'ended_at',
            'created_at',
        )
        read_only_fields = (
            'id',
            'subject',
            'continuity_code',
            'academic_grade',
            'academic_year',
            'is_active',
            'ended_at',
            'created_at',
        )


class CBCGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CBCGrade
        fields = (
            'id',
            'term',
            'year',
            'level',
            'framework',
            'academic_grade',
            'raw_score',
            'source',
            'verified_by',
            'verified_school',
            'verified_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'framework',
            'academic_grade',
            'source',
            'verified_by',
            'verified_school',
            'verified_at',
            'created_at',
            'updated_at',
        )

    def validate_year(self, value):
        current_year = date.today().year
        if value < current_year - 5 or value > current_year + 1:
            raise serializers.ValidationError(
                f'Year must be between {current_year - 5} and {current_year + 1}.'
            )
        return value


class ProgressEvidenceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    academic_grade = serializers.IntegerField()
    year = serializers.IntegerField()
    term = serializers.IntegerField()
    level = serializers.CharField()
    rank = serializers.IntegerField()
    framework = serializers.DictField()
    source = serializers.CharField()
    verified_by = serializers.IntegerField(allow_null=True)
    verified_school = serializers.IntegerField(allow_null=True)
    verified_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()


class ProgressDecisionInputsSerializer(serializers.Serializer):
    latest_framework = serializers.DictField(allow_null=True)
    me2_rank = serializers.IntegerField(allow_null=True)


class ProgressSubjectSerializer(serializers.Serializer):
    continuity_code = serializers.CharField()
    subject_name = serializers.CharField()
    status = serializers.CharField()
    label = serializers.CharField()
    rule_code = serializers.CharField()
    explanation = serializers.CharField()
    suggested_action = serializers.CharField()
    evidence_confidence = serializers.CharField()
    records_used = ProgressEvidenceSerializer(many=True)
    evidence = ProgressEvidenceSerializer(many=True)
    decision_inputs = ProgressDecisionInputsSerializer()


class ProgressOverallSerializer(serializers.Serializer):
    status = serializers.CharField()
    label = serializers.CharField()
    subject_continuity_codes = serializers.ListField(child=serializers.CharField())


class ProgressAssessmentSerializer(serializers.Serializer):
    subjects = ProgressSubjectSerializer(many=True)
    overall = ProgressOverallSerializer()
    advisory_disclaimer = serializers.CharField()


class AcademicGoalWriteSerializer(serializers.ModelSerializer):
    target_level_definition = serializers.PrimaryKeyRelatedField(
        queryset=PerformanceLevelDefinition.objects.select_related('framework'),
        required=False,
    )
    target_level = serializers.ChoiceField(
        choices=GRADE_LEVEL_CHOICES,
        write_only=True,
        required=False,
    )

    class Meta:
        model = AcademicGoal
        fields = (
            'continuity_code',
            'target_level_definition',
            'target_level',
            'target_term',
            'target_year',
            'target_academic_grade',
            'action_plan',
        )

    def _current_evidence(self, continuity_code):
        learner = self.context['learner']
        return (
            CBCGrade.objects.filter(
                student_subject__student_profile=learner,
                student_subject__continuity_code=continuity_code,
            )
            .select_related('framework', 'student_subject')
            .order_by('academic_grade', 'year', 'term', 'created_at', 'pk')
            .last()
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        target_code = attrs.pop('target_level', None)
        supplied_target = attrs.get('target_level_definition')
        if target_code is not None and supplied_target is not None:
            raise serializers.ValidationError(
                {'target_level': 'Choose a target level by code or definition, not both.'}
            )
        if self.instance is None:
            continuity_code = attrs['continuity_code']
            current_evidence = self._current_evidence(continuity_code)
            if current_evidence is None:
                raise serializers.ValidationError(
                    {'continuity_code': 'Academic evidence is required before setting a goal.'}
                )
            try:
                current_level = PerformanceLevelDefinition.objects.select_related(
                    'framework'
                ).get(
                    framework=current_evidence.framework,
                    code=current_evidence.level,
                )
            except PerformanceLevelDefinition.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {'continuity_code': 'The current assessment framework is incomplete.'}
                ) from exc
            attrs['current_evidence'] = current_evidence
            attrs['current_level_definition'] = current_level
        else:
            current_evidence = self.instance.current_evidence
            current_level = self.instance.current_level_definition
            attrs['continuity_code'] = self.instance.continuity_code

        if target_code is not None:
            try:
                target_level = PerformanceLevelDefinition.objects.select_related(
                    'framework'
                ).get(framework=current_level.framework, code=target_code)
            except PerformanceLevelDefinition.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {'target_level': 'That target level is unavailable in the current framework.'}
                ) from exc
        else:
            target_level = supplied_target or (
                self.instance.target_level_definition if self.instance else None
            )
        if target_level is None:
            raise serializers.ValidationError(
                {'target_level': 'Choose a target performance level.'}
            )
        if target_level.framework_id != current_level.framework_id:
            raise serializers.ValidationError(
                {'target_level_definition': 'Target level must use the current assessment framework.'}
            )
        if target_level.rank < current_level.rank:
            raise serializers.ValidationError(
                {'target_level_definition': 'Target level cannot be lower than the current level.'}
            )
        target_period = (
            attrs.get(
                'target_academic_grade',
                self.instance.target_academic_grade if self.instance else None,
            ),
            attrs.get('target_year', self.instance.target_year if self.instance else None),
            attrs.get('target_term', self.instance.target_term if self.instance else None),
        )
        current_period = (
            current_evidence.academic_grade,
            current_evidence.year,
            current_evidence.term,
        )
        if target_period <= current_period:
            raise serializers.ValidationError(
                {'target_term': 'Target period must be later than the current evidence period.'}
            )
        attrs['target_level_definition'] = target_level
        return attrs

    def create(self, validated_data):
        learner = self.context['learner']
        return AcademicGoal.objects.create(
            learner=learner,
            created_by=learner.user,
            **validated_data,
        )


class AcademicGoalSerializer(serializers.ModelSerializer):
    current_level = serializers.SerializerMethodField()
    target_level = serializers.SerializerMethodField()
    ready_for_achievement = serializers.SerializerMethodField()
    readiness_evidence = serializers.SerializerMethodField()

    class Meta:
        model = AcademicGoal
        fields = (
            'id',
            'continuity_code',
            'current_evidence',
            'current_level',
            'target_level',
            'target_term',
            'target_year',
            'target_academic_grade',
            'action_plan',
            'status',
            'ready_for_achievement',
            'readiness_evidence',
            'created_by',
            'achieved_at',
            'closed_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    @staticmethod
    def get_current_level(goal):
        return {
            'code': goal.current_level_code,
            'rank': goal.current_level_rank,
            'framework': {
                'code': goal.current_framework_code,
                'version': goal.current_framework_version,
            },
        }

    @staticmethod
    def get_target_level(goal):
        return {
            'id': goal.target_level_definition_id,
            'code': goal.target_level_code,
            'rank': goal.target_level_rank,
            'framework': {
                'code': goal.target_framework_code,
                'version': goal.target_framework_version,
            },
        }

    def _readiness(self, goal):
        cache = self.context.setdefault('academic_goal_readiness', {})
        if goal.pk not in cache:
            cache[goal.pk] = goal.readiness_evidence()
        return cache[goal.pk]

    def get_ready_for_achievement(self, goal):
        return self._readiness(goal) is not None

    def get_readiness_evidence(self, goal):
        evidence = self._readiness(goal)
        return evidence.pk if evidence is not None else None
