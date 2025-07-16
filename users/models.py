from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from jedi.inference.flow_analysis import Status


class MarriedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(husband__isnull=False)


class User(AbstractUser):
    class Gender(models.IntegerChoices):
        MAN = 1,
        WOMAN = 0

    is_married = models.BooleanField(default=False, verbose_name='Married')
    gender = models.BooleanField(
        choices=tuple(map(lambda x: (bool(x[0]), x[1]), Gender.choices)),
        default=None
    )
    first_name = models.CharField(max_length=150, blank=False, null=False)
    
    objects = UserManager()
    married = MarriedManager()

    REQUIRED_FIELDS = ['email', 'gender', 'first_name']

    def __str__(self):
        return self.username


class Marriage(models.Model):
    husband = models.OneToOneField('User', on_delete=models.CASCADE, related_name='husband')
    wife = models.OneToOneField('User', on_delete=models.CASCADE, related_name='wife')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('husband', 'wife')]

class MarriageProposals(models.Model):
    class Status(models.IntegerChoices):
        COMPLETE = 1,
        CANCELED = 0,
        WAIT = -1,

    sender = models.ForeignKey('User', on_delete=models.CASCADE, unique=True, related_name='user_sender')
    receiver = models.ForeignKey('User', on_delete=models.CASCADE, related_name='user_receiver')

    status = models.SmallIntegerField(choices=Status.choices, default=Status.WAIT,verbose_name='status')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('sender', 'receiver')]
