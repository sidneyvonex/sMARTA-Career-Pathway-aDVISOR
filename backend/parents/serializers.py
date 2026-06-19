from rest_framework import serializers
from riasec.models import RIASECAssessment, Recommendation
from riasec.serializers import AssessmentResultSerializer
from counselors.models import CounselorAssignment, CounselorNote
from students.models import StudentSubject, CBCGrade


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

    def _top_recommendation(self, profile):
        if not hasattr(self, '_rec_cache'):
            self._rec_cache = {}
        key = profile.pk
        if key not in self._rec_cache:
            assessment = (
                RIASECAssessment.objects
                .filter(student_profile=profile)
                .order_by('-submitted_at')
                .first()
            )
            if assessment:
                self._rec_cache[key] = (
                    assessment,
                    Recommendation.objects.filter(assessment=assessment, rank=1)
                    .select_related('pathway').first(),
                )
            else:
                self._rec_cache[key] = (None, None)
        return self._rec_cache[key]

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
        assessment, _ = self._top_recommendation(p)
        return 'done' if assessment else 'pending'

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
        _, rec = self._top_recommendation(p)
        return rec.pathway.name if rec else None

    def get_fit_pct(self, obj):
        p = self._profile(obj)
        if not p:
            return None
        _, rec = self._top_recommendation(p)
        return rec.fit_pct if rec else None


class ChildProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='user.id')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    county = serializers.CharField(source='user.county', allow_null=True)
    grade = serializers.IntegerField()
    mode = serializers.CharField()
    bio = serializers.CharField(allow_blank=True)
    date_of_birth = serializers.DateField(allow_null=True)
    career_interests = serializers.CharField(allow_blank=True)
    photo_url = serializers.URLField(allow_null=True)


class ChildGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CBCGrade
        fields = ('id', 'term', 'year', 'level')


class ChildSubjectSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='subject.id')
    name = serializers.CharField(source='subject.name')
    code = serializers.CharField(source='subject.code')
    category = serializers.CharField(source='subject.category')
    grades = serializers.SerializerMethodField()

    def get_grades(self, obj):
        return ChildGradeSerializer(obj.grades.all(), many=True).data


class ChildCounselorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()


class ChildNoteSerializer(serializers.Serializer):
    body = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class ChildDetailSerializer(serializers.Serializer):
    profile = serializers.SerializerMethodField()
    subjects = serializers.SerializerMethodField()
    assessment = serializers.SerializerMethodField()
    counselor = serializers.SerializerMethodField()
    latest_note = serializers.SerializerMethodField()

    def get_profile(self, profile):
        return ChildProfileSerializer(profile).data

    def get_subjects(self, profile):
        subjects = (
            StudentSubject.objects
            .filter(student_profile=profile)
            .select_related('subject')
            .prefetch_related('grades')
        )
        return ChildSubjectSerializer(subjects, many=True).data

    def get_assessment(self, profile):
        assessment = (
            RIASECAssessment.objects
            .filter(student_profile=profile)
            .prefetch_related('scores', 'recommendations__pathway')
            .order_by('-submitted_at')
            .first()
        )
        if not assessment:
            return None
        return AssessmentResultSerializer(assessment).data

    def get_counselor(self, profile):
        assignment = (
            CounselorAssignment.objects
            .filter(student_profile=profile, is_active=True)
            .select_related('counselor')
            .first()
        )
        if not assignment:
            return None
        return ChildCounselorSerializer(assignment.counselor).data

    def get_latest_note(self, profile):
        note = (
            CounselorNote.objects
            .filter(
                student=profile.user,
                visible_to_parent=True,
                deleted_at__isnull=True,
            )
            .order_by('-created_at')
            .first()
        )
        if not note:
            return None
        return ChildNoteSerializer(note).data
