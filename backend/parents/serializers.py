from rest_framework import serializers
from riasec.models import RIASECAssessment, Recommendation
from counselors.models import CounselorAssignment


class LinkedChildSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='student.id')
    first_name = serializers.CharField(source='student.first_name')
    last_name = serializers.CharField(source='student.last_name')
    grade = serializers.SerializerMethodField()
    county = serializers.CharField(source='student.county')
    photo_url = serializers.SerializerMethodField()
    quiz_status = serializers.SerializerMethodField()
    subject_count = serializers.SerializerMethodField()
    counselor_assigned = serializers.SerializerMethodField()
    last_active = serializers.SerializerMethodField()
    top_pathway = serializers.SerializerMethodField()
    fit_pct = serializers.SerializerMethodField()

    def _profile(self, obj):
        return getattr(obj.student, 'student_profile', None)

    def get_grade(self, obj):
        p = self._profile(obj)
        return p.grade if p else None

    def get_photo_url(self, obj):
        p = self._profile(obj)
        return p.photo_url if p else None

    def get_quiz_status(self, obj):
        p = self._profile(obj)
        if not p:
            return 'pending'
        return 'done' if RIASECAssessment.objects.filter(student_profile=p).exists() else 'pending'

    def get_subject_count(self, obj):
        p = self._profile(obj)
        return p.enrolled_subjects.count() if p else 0

    def get_counselor_assigned(self, obj):
        p = self._profile(obj)
        if not p:
            return False
        return CounselorAssignment.objects.filter(student_profile=p, is_active=True).exists()

    def get_last_active(self, obj):
        return obj.student.updated_at.isoformat() if obj.student.updated_at else None

    def get_top_pathway(self, obj):
        p = self._profile(obj)
        if not p:
            return None
        assessment = RIASECAssessment.objects.filter(student_profile=p).order_by('-submitted_at').first()
        if not assessment:
            return None
        rec = Recommendation.objects.filter(assessment=assessment, rank=1).select_related('pathway').first()
        return rec.pathway.name if rec else None

    def get_fit_pct(self, obj):
        p = self._profile(obj)
        if not p:
            return None
        assessment = RIASECAssessment.objects.filter(student_profile=p).order_by('-submitted_at').first()
        if not assessment:
            return None
        rec = Recommendation.objects.filter(assessment=assessment, rank=1).first()
        return rec.fit_pct if rec else None
