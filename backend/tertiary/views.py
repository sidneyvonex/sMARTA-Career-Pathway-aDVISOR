from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.models import StudentProfile
from accounts.permissions import IsEmailVerified, IsStudent
from accounts.response import _error, _success

from .models import Institution, LearnerEducationGoal, Programme
from .serializers import (
    InstitutionSerializer,
    LearnerEducationGoalSerializer,
    LearnerEducationGoalWriteSerializer,
    ProgrammeDetailSerializer,
    ProgrammeSummarySerializer,
)


MAX_CATALOGUE_RESULTS = 100
MAX_QUERY_LENGTH = 100


def _bounded(value):
    return (value or '').strip()[:MAX_QUERY_LENGTH]


class InstitutionListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        queryset = Institution.objects.all()
        search = _bounded(request.query_params.get('search'))
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(external_key__icontains=search))
        for parameter, field in (
            ('county', 'county'),
            ('framework', 'education_framework'),
            ('cycle', 'admission_cycle'),
            ('verification_status', 'verification_status'),
        ):
            value = _bounded(request.query_params.get(parameter))
            if value:
                queryset = queryset.filter(**{f'{field}__iexact': value})
        return _success(InstitutionSerializer(queryset[:MAX_CATALOGUE_RESULTS], many=True).data)


class ProgrammeListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        queryset = Programme.objects.select_related('institution')
        search = _bounded(request.query_params.get('search'))
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search) | Q(external_key__icontains=search)
            )
        institution = _bounded(request.query_params.get('institution'))
        if institution:
            if not institution.isdigit():
                return _error({'institution': ['A numeric institution id is required.']})
            queryset = queryset.filter(institution_id=int(institution))
        for parameter, field in (
            ('framework', 'education_framework'),
            ('cycle', 'admission_cycle'),
            ('verification_status', 'verification_status'),
        ):
            value = _bounded(request.query_params.get(parameter))
            if value:
                queryset = queryset.filter(**{f'{field}__iexact': value})
        return _success(ProgrammeSummarySerializer(queryset[:MAX_CATALOGUE_RESULTS], many=True).data)


class ProgrammeDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request, programme_id):
        programme = get_object_or_404(
            Programme.objects.select_related('institution').prefetch_related(
                'subject_references', 'historical_admission_references'
            ),
            pk=programme_id,
        )
        return _success(ProgrammeDetailSerializer(programme).data)


def _goal_queryset(learner):
    return LearnerEducationGoal.objects.filter(learner=learner).select_related(
        'institution', 'programme', 'programme__institution'
    )


class EducationGoalListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        learner = get_object_or_404(StudentProfile, user=request.user)
        return _success(LearnerEducationGoalSerializer(_goal_queryset(learner), many=True).data)

    def post(self, request):
        try:
            with transaction.atomic():
                learner = StudentProfile.objects.select_for_update().get(user=request.user)
                serializer = LearnerEducationGoalWriteSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                goal = serializer.save(learner=learner, created_by=request.user)
        except IntegrityError:
            return _error('That education-goal slot is already in use.')
        return _success(
            LearnerEducationGoalSerializer(goal).data,
            'Education goal saved.',
            status.HTTP_201_CREATED,
        )


class EducationGoalDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def patch(self, request, goal_id):
        try:
            with transaction.atomic():
                learner = StudentProfile.objects.select_for_update().get(user=request.user)
                goal = get_object_or_404(
                    LearnerEducationGoal.objects.select_for_update(),
                    pk=goal_id,
                    learner=learner,
                )
                serializer = LearnerEducationGoalWriteSerializer(
                    goal, data=request.data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                goal = serializer.save()
        except IntegrityError:
            return _error('That education-goal slot is already in use.')
        return _success(LearnerEducationGoalSerializer(goal).data, 'Education goal updated.')

    def delete(self, request, goal_id):
        with transaction.atomic():
            learner = StudentProfile.objects.select_for_update().get(user=request.user)
            goal = get_object_or_404(
                LearnerEducationGoal.objects.select_for_update(),
                pk=goal_id,
                learner=learner,
            )
            goal.delete()
        return _success(None, 'Education goal removed.')
