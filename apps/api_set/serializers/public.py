from rest_framework import serializers

from apps.dashboard.custom.models import ReturnReason


class ReturnReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnReason
        fields = ('title', 'subtitle', 'position',)



