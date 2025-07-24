from django.db import models
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from users.models import Marriage, User, MarriageProposals


class MarriageSerializers(ModelSerializer):
    receiver_username = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    first_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = MarriageProposals
        fields = ['receiver_username', 'first_name','last_name', 'status']

    def validate(self, data):
        has_username = data.get('receiver_username') is not None
        has_fio = all([
            data.get('last_name'),
            data.get('first_name')
        ])

        if not has_username and not has_fio:
            raise serializers.ValidationError(
                "Provide either username or full name"
            )

        if has_username and has_fio:
            raise serializers.ValidationError(
                "Provide only one: username or full name"
            )

        sender = self.context['request'].user
        if sender.is_married:
            raise serializers.ValidationError({'name':"You are already married"})

        return data

    def validate_receiver_username(self, value):
        if not User.objects.filter(username=value).exists():
            raise serializers.ValidationError("User not found")

        receiver = User.objects.get(username=value)
        if receiver.is_married:
            raise serializers.ValidationError("This user is already married")

        return value

    def create(self, validated_data):
        receiver_fullname = None
        receiver = None
        sender = self.context['request'].user

        if 'receiver_username' in validated_data:
            username = validated_data.pop('receiver_username')
            receiver = User.objects.get(username=username)
        else:
            first_name = validated_data.pop('first_name')
            last_name = validated_data.pop('last_name')
            receiver_fullname = f"{first_name} {last_name} ".strip()

        if MarriageProposals.objects.filter(
                sender=sender,
                status=MarriageProposals.Status.WAITING
        ).exists():
            raise serializers.ValidationError("You have already sent an offer")

        if receiver and sender == receiver:
            raise serializers.ValidationError("You can't send it to yourself")

        return MarriageProposals.objects.create(
            sender=sender,
            receiver=receiver,
            receiver_fullname=receiver_fullname,
            status=validated_data.get('status', MarriageProposals.Status.WAITING)
        )

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

class MarriagesListSerializers(ModelSerializer):
    pass
