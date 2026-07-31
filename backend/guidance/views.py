from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from accounts.response import _error, _success
from riasec.models import Pathway

from .models import (
    FrameworkVersion,
    PathwayTrack,
)
from .selectors import active_combination_queryset
from .serializers import (
    FrameworkVersionSerializer,
    PathwayCatalogueSerializer,
    SubjectCombinationSerializer,
)

class PublicGuidanceView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]


class CurrentFrameworkView(PublicGuidanceView):
    def get(self, request):
        framework = FrameworkVersion.objects.current()
        if framework is None:
            return _error('No active guidance framework found.', 404)
        return _success(data=FrameworkVersionSerializer(framework).data)


class PathwayListView(PublicGuidanceView):
    def get(self, request):
        framework = FrameworkVersion.objects.current()
        if framework is None:
            return _success(data=[])

        active_tracks = (
            PathwayTrack.objects.filter(
                framework_version=framework,
                is_active=True,
            )
            .select_related('pathway')
            .order_by('name')
        )
        pathways = (
            Pathway.objects.filter(
                framework_tracks__framework_version=framework,
                framework_tracks__is_active=True,
            )
            .distinct()
            .order_by('name')
            .prefetch_related(
                Prefetch(
                    'framework_tracks',
                    queryset=active_tracks,
                    to_attr='active_framework_tracks',
                )
            )
        )
        return _success(data=PathwayCatalogueSerializer(pathways, many=True).data)


class CombinationListView(PublicGuidanceView):
    def get(self, request):
        framework = FrameworkVersion.objects.current()
        if framework is None:
            return _success(data=[])

        combinations = active_combination_queryset(framework)
        pathway = request.query_params.get('pathway', '').strip()
        track = request.query_params.get('track', '').strip()
        county = request.query_params.get('county', '').strip()
        school = request.query_params.get('school', '').strip()
        search = request.query_params.get('search', '').strip()

        if pathway:
            if pathway.isdigit():
                combinations = combinations.filter(track__pathway_id=int(pathway))
            else:
                combinations = combinations.filter(
                    track__pathway__name__iexact=pathway
                )
        if track:
            if track.isdigit():
                combinations = combinations.filter(track_id=int(track))
            else:
                combinations = combinations.filter(track__code__iexact=track)
        if county:
            combinations = combinations.filter(
                school_offerings__is_active=True,
                school_offerings__verification_status='verified',
                school_offerings__school__is_active=True,
                school_offerings__school__verification_status='verified',
                school_offerings__school__county__iexact=county,
            )
        if school:
            school_filter = Q(school_offerings__school__school_code__iexact=school)
            if school.isdigit():
                school_filter |= Q(school_offerings__school_id=int(school))
            combinations = combinations.filter(
                school_filter,
                school_offerings__is_active=True,
                school_offerings__verification_status='verified',
                school_offerings__school__is_active=True,
                school_offerings__school__verification_status='verified',
            )
        if search:
            combinations = combinations.filter(
                Q(code__icontains=search)
                | Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(subject_one__name__icontains=search)
                | Q(subject_two__name__icontains=search)
                | Q(subject_three__name__icontains=search)
            )

        combinations = combinations.distinct()
        return _success(
            data=SubjectCombinationSerializer(combinations, many=True).data
        )


class CombinationDetailView(PublicGuidanceView):
    def get(self, request, combination_id):
        framework = FrameworkVersion.objects.current()
        if framework is None:
            return _error('No active guidance framework found.', 404)
        combination = get_object_or_404(
            active_combination_queryset(framework),
            pk=combination_id,
        )
        return _success(data=SubjectCombinationSerializer(combination).data)
