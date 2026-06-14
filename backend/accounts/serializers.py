from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import School, StudentProfile, COUNTY_CHOICES

User = get_user_model()

VALID_COUNTIES = [c[0] for c in COUNTY_CHOICES]


class StudentRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    county = serializers.ChoiceField(choices=VALID_COUNTIES)
    grade = serializers.ChoiceField(choices=[9, 10])
    school_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=['student'])

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value.lower()

    def validate(self, attrs):
        school_code = attrs.get('school_code', '').strip()
        if school_code:
            try:
                school = School.objects.get(school_code=school_code)
            except School.DoesNotExist:
                raise serializers.ValidationError({'school_code': 'School code not found.'})
            if school.county != attrs['county']:
                raise serializers.ValidationError(
                    {'school_code': 'School county does not match your selected county.'}
                )
            attrs['school'] = school
            attrs['mode'] = 'school_linked'
        else:
            attrs['school'] = None
            attrs['mode'] = 'self_guided'
        return attrs

    def create(self, validated_data):
        school = validated_data.pop('school')
        mode = validated_data.pop('mode')
        validated_data.pop('school_code', None)
        password = validated_data.pop('password')
        grade = validated_data.pop('grade')

        user = User.objects.create_user(password=password, **validated_data)
        StudentProfile.objects.create(user=user, mode=mode, school=school, grade=grade)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'county', 'is_email_verified')
        read_only_fields = fields
