from django.contrib import admin

from .models import (
    AcademicGoal,
    AssessmentFramework,
    CBCGrade,
    PerformanceLevelDefinition,
    StudentSubject,
    Subject,
)


class PerformanceLevelDefinitionInline(admin.TabularInline):
    model = PerformanceLevelDefinition
    extra = 0
    ordering = ('-rank',)


@admin.register(AssessmentFramework)
class AssessmentFrameworkAdmin(admin.ModelAdmin):
    list_display = ('code', 'version', 'title', 'scope', 'status', 'effective_date')
    list_filter = ('scope', 'status', 'effective_date')
    search_fields = ('code', 'version', 'title')
    inlines = (PerformanceLevelDefinitionInline,)


@admin.register(PerformanceLevelDefinition)
class PerformanceLevelDefinitionAdmin(admin.ModelAdmin):
    list_display = ('code', 'label', 'framework', 'rank')
    list_filter = ('framework',)
    search_fields = ('code', 'label', 'framework__code', 'framework__version')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'continuity_code', 'name', 'grade', 'category', 'is_active')
    list_filter = ('grade', 'category', 'is_active')
    search_fields = ('code', 'name')


@admin.register(StudentSubject)
class StudentSubjectAdmin(admin.ModelAdmin):
    list_display = (
        'student_profile',
        'subject',
        'continuity_code',
        'academic_grade',
        'academic_year',
        'is_active',
        'ended_at',
        'created_at',
    )
    search_fields = ('student_profile__user__email', 'subject__code', 'subject__name')


@admin.register(CBCGrade)
class CBCGradeAdmin(admin.ModelAdmin):
    list_display = (
        'student_subject',
        'academic_grade',
        'term',
        'year',
        'level',
        'source',
        'framework',
        'verified_school',
    )
    list_filter = ('framework', 'academic_grade', 'term', 'level', 'source')
    search_fields = (
        'student_subject__student_profile__user__email',
        'student_subject__subject__code',
    )
    readonly_fields = (
        'verified_by',
        'verified_at',
        'verified_school',
        'created_at',
        'updated_at',
    )


@admin.register(AcademicGoal)
class AcademicGoalAdmin(admin.ModelAdmin):
    list_display = (
        'learner',
        'continuity_code',
        'current_level_code',
        'target_level_code',
        'target_term',
        'target_year',
        'status',
        'updated_at',
    )

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.role == 'system_admin'

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    list_filter = ('status', 'target_academic_grade', 'target_year', 'target_term')
    search_fields = ('learner__user__email', 'continuity_code')
    readonly_fields = (
        'active_identity',
        'current_evidence',
        'current_level_definition',
        'current_level_code',
        'current_level_rank',
        'current_framework_code',
        'current_framework_version',
        'target_level_code',
        'target_level_rank',
        'target_framework_code',
        'target_framework_version',
        'created_by',
        'achieved_at',
        'closed_at',
        'created_at',
        'updated_at',
    )
