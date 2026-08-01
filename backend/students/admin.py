from django.contrib import admin

from .models import (
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
    list_display = ('code', 'name', 'grade', 'category', 'is_active')
    list_filter = ('grade', 'category', 'is_active')
    search_fields = ('code', 'name')


@admin.register(StudentSubject)
class StudentSubjectAdmin(admin.ModelAdmin):
    list_display = ('student_profile', 'subject', 'created_at')
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
