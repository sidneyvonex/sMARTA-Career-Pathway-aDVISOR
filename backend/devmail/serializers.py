from rest_framework import serializers

from .models import CapturedEmail


class CapturedEmailListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapturedEmail
        fields = ['id', 'to_email', 'subject', 'created_at']


class CapturedEmailDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapturedEmail
        fields = ['id', 'to_email', 'from_email', 'subject', 'body', 'created_at']
