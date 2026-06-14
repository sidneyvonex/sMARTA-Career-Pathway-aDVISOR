from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, School, StudentProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'county', 'is_email_verified', 'is_active')
    list_filter = ('role', 'county', 'is_email_verified', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'role', 'county')}),
        ('Status', {'fields': ('is_email_verified', 'is_active', 'is_staff', 'is_superuser')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
    readonly_fields = ('last_login', 'created_at', 'updated_at')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'county', 'first_name', 'last_name'),
        }),
    )


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'county', 'school_code', 'created_at')
    search_fields = ('name', 'school_code')
    list_filter = ('county',)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mode', 'school', 'grade')
    list_filter = ('mode', 'grade')
