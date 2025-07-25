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


    def update(self, instance, validated_data):
        if (instance.status == MarriageProposals.Status.WAITING and validated_data.get('status') ==
                MarriageProposals.Status.COMPLETE):
            if instance.sender.gender == User.Gender.MAN:
                Marriage.objects.create(
                    husband=instance.sender,
                    wife=instance.receiver,
                )
            else:
                Marriage.objects.create(
                    husband=instance.receiver,
                    wife=instance.sender,
                )

            instance.sender.is_married = True
            instance.receiver.is_married = True
            instance.sender.save()
            instance.receiver.save()

            MarriageProposals.objects.filter(
                models.Q(sender=instance.sender) |
                models.Q(sender=instance.receiver) |
                models.Q(receiver=instance.sender) |
                models.Q(receiver=instance.receiver),
                status=MarriageProposals.Status.WAITING
            ).exclude(id=instance.id).update(status=MarriageProposals.Status.CANCELED)

        return super().update(instance,validated_data)

    def validate_status(self, value):
        if value == MarriageProposals.Status.COMPLETE:
            instance = self.instance

            # Отправитель не женат
            if instance.sender.is_married:
                raise serializers.ValidationError("Отправитель уже в браке")

            # Получатель не женат
            if instance.receiver.is_married:
                raise serializers.ValidationError("Получатель уже в браке")

            # Заявка ещё не обработана
            if instance.status != MarriageProposals.Status.WAITING:
                raise serializers.ValidationError("Заявка уже обработана")

        return value

