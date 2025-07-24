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
        # sender = self.context['request'].user
        # has_username = 'receiver_username' in data
        # has_fio = all(data.get(field) for field in ['last_name', 'first_name', 'gender'])
        #
        # # Validate input combination
        # if not has_username and not has_fio:
        #     raise serializers.ValidationError("Provide either username or full name")
        # if has_username and has_fio:
        #     raise serializers.ValidationError("Provide only one: username or full name")
        #
        # # Validate sender status
        # if sender.is_married:
        #     raise serializers.ValidationError("You are already married")
        #
        # # Validate gender for new user
        # if has_fio and int(data['gender']) == sender.gender:
        #     raise serializers.ValidationError("Same-sex marriage not allowed")

        return data

    def validate_receiver_username(self, value):
        try:
            receiver = User.objects.get(username=value)
            if receiver.is_married:
                raise serializers.ValidationError("This user is already married")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

    def create(self, validated_data):
        sender = self.context['request'].user
        receiver = None
        receiver_fullname = None

        with transaction.atomic():
            # Check for existing waiting proposals
            if MarriageProposals.objects.filter(sender=sender, status=MarriageProposals.Status.WAITING).exists():
                raise serializers.ValidationError("You have already sent an offer")

            if 'receiver_username' in validated_data:
                # Existing user case
                username = validated_data.pop('receiver_username')
                receiver = User.objects.get(username=username)

                if sender == receiver:
                    raise serializers.ValidationError("You can't send it to yourself")

                if receiver.gender == sender.gender:
                    raise serializers.ValidationError("You can't send to same-sex user")
            else:
                # New user case
                first_name = validated_data.pop('first_name')
                last_name = validated_data.pop('last_name')
                gender = validated_data.pop('gender')
                receiver_fullname = f"{first_name} {last_name}".strip()

                if sender.get_full_name() == receiver_fullname:
                    raise serializers.ValidationError("You can't send it to yourself")

                receiver = User.objects.create(
                    username=f"user_{uuid.uuid4().hex[:8]}",
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    is_active=True
                )

                # For new users, automatically complete the marriage
                validated_data['status'] = MarriageProposals.Status.COMPLETE

            # Create marriage if status is COMPLETE
            if validated_data.get('status') == MarriageProposals.Status.COMPLETE:
                husband, wife = (sender, receiver) if sender.gender == User.Gender.MAN else (receiver, sender)
                User.objects.filter(pk__in=[sender.pk, receiver.pk]).update(is_married=True)
                Marriage.objects.create(husband=husband, wife=wife)

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

