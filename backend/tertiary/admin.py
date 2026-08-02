from django.contrib import admin

from .models import (
    HistoricalAdmissionReference,
    Institution,
    LearnerEducationGoal,
    Programme,
    ProgrammeSubjectReference,
)


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution_type', 'admission_cycle', 'verification_status')
    search_fields = ('name', 'external_key')
    list_filter = ('institution_type', 'verification_status', 'admission_cycle')


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'code', 'admission_cycle', 'verification_status')
    search_fields = ('name', 'code', 'external_key', 'institution__name')
    list_filter = ('verification_status', 'admission_cycle')


admin.site.register(ProgrammeSubjectReference)
admin.site.register(HistoricalAdmissionReference)
admin.site.register(LearnerEducationGoal)
