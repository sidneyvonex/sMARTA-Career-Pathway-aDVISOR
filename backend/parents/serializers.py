from rest_framework import serializers
from riasec.models import RIASECAssessment
from riasec.serializers import AssessmentResultSerializer
from counselors.models import CounselorAssignment, CounselorNote
from students.models import StudentSubject, CBCGrade
from students.summaries import next_action_for, profile_completion_summary
from guidance.models import LearnerCombinationChoice, LearnerPlan
from parents.models import ParentStudentLink


class ParentAccessSerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()
    parent_email = serializers.EmailField(source='parent.email')
    relationship_label = serializers.CharField(
        source='get_claimed_relationship_display',
    )

    class Meta:
        model = ParentStudentLink
        fields = (
            'id',
            'parent_name',
            'parent_email',
            'claimed_relationship',
            'relationship_label',
            'status',
            'learner_approved_at',
            'revoked_at',
            'created_at',
        )

    def get_parent_name(self, obj):
        return (
            f'{obj.parent.first_name} {obj.parent.last_name}'.strip()
            or obj.parent.email
        )


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
    access_status = serializers.CharField(source='status')
    next_action = serializers.SerializerMethodField()
    provisional_combination = serializers.SerializerMethodField()
    plan_status = serializers.SerializerMethodField()
    plan_progress = serializers.SerializerMethodField()
    upcoming_milestone = serializers.SerializerMethodField()
    conversation_prompt = serializers.SerializerMethodField()

    def _profile(self, obj):
        return getattr(obj.student, 'student_profile', None)

    def _top_recommendation(self, profile):
        if not hasattr(self, '_rec_cache'):
            self._rec_cache = {}
        key = profile.pk
        if key not in self._rec_cache:
            assessments = list(profile.riasec_assessments.all())
            assessment = assessments[0] if assessments else None
            if assessment:
                recommendations = list(assessment.recommendations.all())
                self._rec_cache[key] = (
                    assessment,
                    recommendations[0] if recommendations else None,
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
        return len(list(p.enrolled_subjects.all())) if p else 0

    def get_counselor_assigned(self, obj):
        p = self._profile(obj)
        if not p:
            return False
        return bool(getattr(p, 'active_parent_assignments', []))

    def get_last_active(self, obj):
        return obj.student.updated_at.isoformat() if obj.student.updated_at else None

    def get_top_pathway(self, obj):
        p = self._profile(obj)
        if not p:
            return None
        _, rec = self._top_recommendation(p)
        return rec.pathway.name if rec else None

    def _plan(self, profile):
        try:
            return profile.learner_plan
        except LearnerPlan.DoesNotExist:
            return None

    def _choices(self, profile):
        return list(profile.combination_choices.all())

    def _evidence(self, profile):
        if not hasattr(self, '_evidence_cache'):
            self._evidence_cache = {}
        if profile.pk not in self._evidence_cache:
            enrollments = list(profile.enrolled_subjects.all())
            grade_counts = [len(list(item.grades.all())) for item in enrollments]
            total_subjects = len(enrollments)
            subjects_with_evidence = sum(count > 0 for count in grade_counts)
            total_grades = sum(grade_counts)
            if total_subjects >= 3 and subjects_with_evidence == total_subjects:
                academic_status = 'ready'
            elif total_subjects or total_grades:
                academic_status = 'in_progress'
            else:
                academic_status = 'not_started'
            assessment, _ = self._top_recommendation(profile)
            choices = self._choices(profile)
            plan = self._plan(profile)
            self._evidence_cache[profile.pk] = {
                'profile': profile_completion_summary(profile),
                'academic': {
                    'status': academic_status,
                    'total_subjects': total_subjects,
                    'subjects_with_evidence': subjects_with_evidence,
                    'total_grade_records': total_grades,
                },
                'assessment': {
                    'status': 'complete' if assessment else 'not_started',
                    'instrument_version': (
                        assessment.instrument_version if assessment else None
                    ),
                    'submitted_at': (
                        assessment.submitted_at.isoformat() if assessment else None
                    ),
                },
                'choices': choices,
                'plan': plan,
            }
        return self._evidence_cache[profile.pk]

    def get_next_action(self, obj):
        profile = self._profile(obj)
        if not profile:
            return {
                'code': 'complete_profile',
                'title': 'Complete the learner profile',
            }
        evidence = self._evidence(profile)
        choices = evidence['choices']
        plan = evidence['plan']
        action = next_action_for(
            evidence['profile'],
            evidence['academic'],
            evidence['assessment'],
            len(choices),
            has_provisional_choice=any(
                choice.status == LearnerCombinationChoice.STATUS_PROVISIONAL
                for choice in choices
            ),
            plan_status=plan.review_status if plan else 'not_started',
        )
        return {'code': action['code'], 'title': action['title']}

    def get_provisional_combination(self, obj):
        profile = self._profile(obj)
        if not profile:
            return None
        evidence = self._evidence(profile)
        plan = evidence['plan']
        choice = plan.provisional_choice if plan else next(
            (
                item for item in evidence['choices']
                if item.status == LearnerCombinationChoice.STATUS_PROVISIONAL
            ),
            None,
        )
        if choice is None:
            return None
        combination = choice.combination
        return {
            'id': combination.id,
            'code': combination.code,
            'title': combination.title,
            'pathway': combination.track.pathway.name,
            'track': combination.track.name,
        }

    def get_plan_status(self, obj):
        profile = self._profile(obj)
        plan = self._plan(profile) if profile else None
        return plan.review_status if plan else 'not_started'

    def get_plan_progress(self, obj):
        profile = self._profile(obj)
        plan = self._plan(profile) if profile else None
        if plan is None:
            return {'completed': 0, 'total': 0}
        milestones = list(plan.milestones.all())
        return {
            'completed': sum(item.is_complete for item in milestones),
            'total': len(milestones),
        }

    def get_upcoming_milestone(self, obj):
        profile = self._profile(obj)
        plan = self._plan(profile) if profile else None
        if plan is None:
            return None
        milestone = next(
            (item for item in plan.milestones.all() if not item.is_complete),
            None,
        )
        if milestone is None:
            return None
        return {
            'id': milestone.id,
            'title': milestone.title,
            'due_date': (
                milestone.due_date.isoformat() if milestone.due_date else None
            ),
        }

    def get_conversation_prompt(self, obj):
        profile = self._profile(obj)
        if not profile:
            return 'What would help you complete your learner profile?'
        action = self.get_next_action(obj)
        prompts = {
            'complete_profile': 'What interests or goals would you like to add to your profile?',
            'add_academic_evidence': 'Which subjects feel strongest, and where would support help?',
            'complete_interest_assessment': 'Which activities make you feel curious or energized?',
            'explore_combinations': 'Which subject combinations would you like to explore together?',
            'compare_combinations': 'What matters most as you compare your saved choices?',
            'create_plan': 'What is one practical step you can add to your plan?',
            'review_plan': 'How can I support your next plan milestone?',
        }
        return prompts[action['code']]


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
