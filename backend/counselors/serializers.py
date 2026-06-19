from rest_framework import serializers
from .models import CounselorNote


class CounselorNoteSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = CounselorNote
        fields = ('id', 'student', 'student_name', 'body', 'visible_to_parent', 'created_at', 'updated_at')
        read_only_fields = ('id', 'student', 'student_name', 'created_at', 'updated_at')

    def get_student_name(self, obj):
        return f'{obj.student.first_name} {obj.student.last_name}'.strip()


class CounselorNoteCreateSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    body = serializers.CharField(max_length=2000)
    visible_to_parent = serializers.BooleanField(default=False, required=False)
