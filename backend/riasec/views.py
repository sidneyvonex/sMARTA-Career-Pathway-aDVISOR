from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from accounts.models import StudentProfile
from accounts.permissions import IsStudent, IsEmailVerified
from accounts.response import _success, _error
from parents.models import ParentStudentLink
from notifications.utils import create_notification
from .models import (
    RIASECQuestion, RIASECAssessment, RIASECResponse,
    RIASECScore, Pathway, Recommendation,
)
from .serializers import (
    RIASECQuestionSerializer, AssessmentResultSerializer, AssessmentSubmitSerializer,
)
from .scoring import compute_dim_scores, holland_code, compute_pathway_fits


class QuestionListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        questions = RIASECQuestion.objects.order_by('order')
        return _success(data=RIASECQuestionSerializer(questions, many=True).data)


class AssessmentView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        profile = StudentProfile.objects.get(user=request.user)
        assessments = (
            RIASECAssessment.objects
            .filter(student_profile=profile)
            .prefetch_related('scores', 'recommendations__pathway')
        )
        return _success(data=AssessmentResultSerializer(assessments, many=True).data)

    def post(self, request):
        serializer = AssessmentSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return _error(serializer.errors)

        profile = StudentProfile.objects.get(user=request.user)
        responses_data = serializer.validated_data['responses']
        responses = {r['question_id']: r['score'] for r in responses_data}

        questions = list(RIASECQuestion.objects.values('id', 'dimension'))
        dim_scores = compute_dim_scores(responses, questions)

        pathways = list(Pathway.objects.values(
            'id', 'name', 'description',
            'weight_r', 'weight_i', 'weight_a', 'weight_s', 'weight_e', 'weight_c',
        ))
        pathway_fits = compute_pathway_fits(dim_scores, pathways)

        with transaction.atomic():
            assessment = RIASECAssessment.objects.create(student_profile=profile)

            RIASECResponse.objects.bulk_create([
                RIASECResponse(assessment=assessment, question_id=qid, score=score)
                for qid, score in responses.items()
            ])

            RIASECScore.objects.bulk_create([
                RIASECScore(assessment=assessment, dimension=dim, raw_score=score)
                for dim, score in dim_scores.items()
            ])

            pathway_objs = {p.id: p for p in Pathway.objects.all()}
            Recommendation.objects.bulk_create([
                Recommendation(
                    assessment=assessment,
                    pathway=pathway_objs[fit['pathway']['id']],
                    rank=fit['rank'],
                    fit_score=fit['fit_score'],
                    fit_pct=fit['fit_pct'],
                )
                for fit in pathway_fits
            ])

        try:
            parent_links = ParentStudentLink.objects.filter(student=request.user)
            student_name = f'{request.user.first_name} {request.user.last_name}'.strip()
            for link in parent_links:
                create_notification(
                    user=link.parent,
                    type_code='child_assessment_complete',
                    message=f'{student_name} has completed their career personality assessment.',
                )
        except Exception:
            pass

        assessment = (
            RIASECAssessment.objects
            .prefetch_related('scores', 'recommendations__pathway')
            .get(pk=assessment.pk)
        )
        return _success(
            data=AssessmentResultSerializer(assessment).data,
            message='Assessment complete.',
            status_code=status.HTTP_201_CREATED,
        )


class AssessmentLatestView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        profile = StudentProfile.objects.get(user=request.user)
        try:
            assessment = (
                RIASECAssessment.objects
                .filter(student_profile=profile)
                .prefetch_related('scores', 'recommendations__pathway')
                .latest('submitted_at')
            )
        except RIASECAssessment.DoesNotExist:
            return _error('No assessment found.', status.HTTP_404_NOT_FOUND)
        return _success(data=AssessmentResultSerializer(assessment).data)
