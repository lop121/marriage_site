import uuid

from django.db import models, transaction
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from users.models import Marriage, User, MarriageProposals


class MarriageSerializers(ModelSerializer):
    receiver_username = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    first_name = serializers.CharField(write_only=True, required=False)
    gender = serializers.ChoiceField(choices=User.Gender.choices, write_only=True, required=False)

    class Meta:
        model = MarriageProposals
        fields = ['receiver_username', 'first_name', 'last_name', 'gender', 'status']

    def validate(self, data):
        sender = self.context['request'].user
        has_username = 'receiver_username' in data
        has_fio = all(data.get(field) for field in ['last_name', 'first_name', 'gender'])

        # Validate input combination
        if not has_username and not has_fio:
            raise serializers.ValidationError("Provide either username or full name")
        if has_username and has_fio:
            raise serializers.ValidationError("Provide only one: username or full name")

        # Validate sender status
        if sender.is_married:
            raise serializers.ValidationError("You are already married")

        # Validate gender for new user
        if has_fio and int(data['gender']) == sender.gender:
            raise serializers.ValidationError("Same-sex marriage not allowed")

        return data

    def validate_receiver_username(self, value):
        try:
            receiver = User.objects.get(username=value)
            if receiver.is_married:
                raise serializers.ValidationError("This user is already married")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

class OffersSerializers(ModelSerializer):
    class Meta:
        model = MarriageProposals
        fields = '__all__'
        read_only_fields = ('sender', 'receiver', 'created_at')
        extra_kwargs = {
            'status': {'required': False}
        }

    def validate_status(self, value):
        if value == MarriageProposals.Status.COMPLETE:
            instance = self.instance

            if instance.sender.is_married:
                raise serializers.ValidationError("Отправитель уже в браке")

            if instance.receiver.is_married:
                raise serializers.ValidationError("Получатель уже в браке")

            if instance.status != MarriageProposals.Status.WAITING:
                raise serializers.ValidationError("Заявка уже обработана")

        return value

class DivorceSerializer(ModelSerializer):
    class Meta:
        model = Marriage
        fields = ['id', 'husband', 'wife', 'status']
        read_only_fields = ['husband', 'wife']

    def validate(self, data):
        return data