from django.contrib.auth import get_user_model
from django.forms import HiddenInput
from rest_framework import serializers
from rest_framework.fields import HiddenField, CharField
from rest_framework.serializers import ModelSerializer

from users.models import Marriage, User


class MarriageSerializers(ModelSerializer):
    receiver_username = serializers.CharField(write_only=True)

    class Meta:
        model = Marriage
        fields = ['receiver_username',  'is_approved']

    def validate_receiver_username(self, value):
        if not User.objects.filter(username=value).exists():
            raise serializers.ValidationError("User not found")
        return value

    def create(self, validated_data):
        receiver_username = validated_data.pop('receiver_username')
        receiver = User.objects.get(username=receiver_username)
        sender = self.context['request'].user

        if Marriage.objects.filter(sender=sender, receiver=receiver).exists():
            raise serializers.ValidationError("You have already sent an offer")

        if sender == receiver:
            raise serializers.ValidationError("You can't send it to yourself")

        return Marriage.objects.create(sender=sender, receiver=receiver, **validated_data)

