from datetime import date
from rest_framework import serializers
from accounts.models import StudentProfile
from .models import Subject, StudentSubject, CBCGrade


class StudentProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    county = serializers.CharField(source='user.county', read_only=True)

    class Meta:
        model = StudentProfile
        fields = (
            'id', 'email', 'first_name', 'last_name', 'county',
            'grade', 'mode', 'bio', 'date_of_birth', 'career_interests', 'photo_url',
        )
        read_only_fields = (
            'id', 'email', 'first_name', 'last_name', 'county',
            'grade', 'mode', 'photo_url',
        )

    def validate_bio(self, value):
        if len(value) > 500:
            raise serializers.ValidationError('Bio must be 500 characters or less.')
        return value

    def validate_career_interests(self, value):
        if len(value) > 500:
            raise serializers.ValidationError('Career interests must be 500 characters or less.')
        return value


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name', 'code', 'grade', 'category')


class StudentSubjectSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source='subject', write_only=True
    )

    class Meta:
        model = StudentSubject
        fields = ('id', 'subject', 'subject_id', 'created_at')
        read_only_fields = ('id', 'subject', 'created_at')


class CBCGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CBCGrade
        fields = ('id', 'term', 'year', 'level', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_year(self, value):
        current_year = date.today().year
        if value < current_year - 5 or value > current_year + 1:
            raise serializers.ValidationError(
                f'Year must be between {current_year - 5} and {current_year + 1}.'
            )
        return value
