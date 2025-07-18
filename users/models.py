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
    last_name = models.CharField(max_length=150, blank=False, null=False)

    objects = UserManager()
    married = MarriedManager()

    REQUIRED_FIELDS = ['email', 'gender', 'first_name', 'last_name']

    def __str__(self):
        return self.username


class Marriage(models.Model):
    husband = models.OneToOneField('User', on_delete=models.CASCADE, related_name='husband')
    wife = models.OneToOneField('User', on_delete=models.CASCADE, related_name='wife')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('husband', 'wife')]

    def __str__(self):
        return f'{self.husband} + {self.wife}'

class MarriageProposals(models.Model):
    class Status(models.IntegerChoices):
        COMPLETE = 1, 'Approved'
        CANCELED = 0, 'Canceled'
        WAITING = -1, 'In waiting...'

    sender = models.ForeignKey('User', on_delete=models.CASCADE, related_name='user_sender')
    receiver = models.ForeignKey('User', on_delete=models.CASCADE, null=True, blank=True, related_name='user_receiver')
    receiver_fullname = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Unregistered user'
    )

    status = models.SmallIntegerField(choices=Status.choices, default=Status.WAITING,verbose_name='status')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('sender', 'receiver'), ('sender', 'receiver_fullname')]

    def __str__(self):
        return f'{self.sender} -> {self.receiver}'

    @property
    def status_display(self) -> str:
        return self.Status(self.status).name

    @property
    def display_receiver(self):
        if self.receiver:
            return self.receiver.get_full_name() or self.receiver.username
        return self.receiver_fullname or "Not found, shma"
