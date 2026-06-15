from rest_framework import serializers
from .models import RIASECQuestion, RIASECAssessment, RIASECScore, Pathway, Recommendation
from .scoring import holland_code as derive_holland_code


class RIASECQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RIASECQuestion
        fields = ('id', 'dimension', 'text', 'order')


class PathwaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pathway
        fields = ('id', 'name', 'description')


class RecommendationSerializer(serializers.ModelSerializer):
    pathway = PathwaySerializer(read_only=True)

    class Meta:
        model = Recommendation
        fields = ('rank', 'fit_score', 'fit_pct', 'pathway')


class AssessmentResultSerializer(serializers.ModelSerializer):
    scores = serializers.SerializerMethodField()
    holland_code = serializers.SerializerMethodField()
    recommendations = RecommendationSerializer(many=True, read_only=True)

    class Meta:
        model = RIASECAssessment
        fields = ('id', 'submitted_at', 'holland_code', 'scores', 'recommendations')

    def get_scores(self, obj):
        return {s.dimension: s.raw_score for s in obj.scores.all()}

    def get_holland_code(self, obj):
        scores = {s.dimension: s.raw_score for s in obj.scores.all()}
        return derive_holland_code(scores)


class ResponseItemSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    score = serializers.IntegerField(min_value=1, max_value=5)


class AssessmentSubmitSerializer(serializers.Serializer):
    responses = ResponseItemSerializer(many=True)

    def validate_responses(self, value):
        from .models import RIASECQuestion
        if len(value) != 30:
            raise serializers.ValidationError(
                f'Exactly 30 responses required. Got {len(value)}.'
            )
        question_ids = [r['question_id'] for r in value]
        if len(set(question_ids)) != len(question_ids):
            raise serializers.ValidationError('Duplicate question_ids are not allowed.')
        valid_ids = set(RIASECQuestion.objects.values_list('id', flat=True))
        invalid = [qid for qid in question_ids if qid not in valid_ids]
        if invalid:
            raise serializers.ValidationError(
                f'Question ID(s) do not exist: {invalid}'
            )
        return value
