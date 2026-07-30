from django.contrib import admin

from .models import FrameworkVersion, PathwayTrack, SchoolOffering, SubjectCombination


@admin.register(FrameworkVersion)
class FrameworkVersionAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'effective_date', 'is_active')
    list_filter = ('is_active', 'effective_date')
    search_fields = ('code', 'title')


@admin.register(PathwayTrack)
class PathwayTrackAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'pathway', 'framework_version', 'is_active')
    list_filter = ('framework_version', 'pathway', 'is_active')
    search_fields = ('code', 'name')


@admin.register(SubjectCombination)
class SubjectCombinationAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'track', 'framework_version', 'is_active')
    list_filter = ('framework_version', 'track', 'is_active')
    search_fields = (
        'code',
        'title',
        'subject_one__name',
        'subject_two__name',
        'subject_three__name',
    )


@admin.register(SchoolOffering)
class SchoolOfferingAdmin(admin.ModelAdmin):
    list_display = ('school', 'combination', 'is_active', 'updated_at')
    list_filter = ('is_active', 'school__county')
    search_fields = ('school__name', 'school__school_code', 'combination__title')
