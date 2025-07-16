from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class MarriedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(user_sender__is_approved=True)


class User(AbstractUser):
    class Gender(models.IntegerChoices):
        MAN = 1,
        WOMAN = 0

    is_married = models.BooleanField(default=False, verbose_name='Married')
    gender = models.BooleanField(
        choices=tuple(map(lambda x: (bool(x[0]), x[1]), Gender.choices)),
        default=None, blank=True
    )
    first_name = models.CharField(max_length=150, blank=False, null=False)
    
    objects = UserManager()
    married = MarriedManager()

    REQUIRED_FIELDS = ['email', 'gender', 'first_name']

    def __str__(self):
        return self.username


class Marriage(models.Model):
    sender = models.OneToOneField('User', on_delete=models.CASCADE, null=True, blank=True, related_name='user_sender')
    receiver = models.OneToOneField('User', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='user_receiver')

    is_approved = models.BooleanField(default=False, verbose_name='Approved')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('sender', 'receiver')]
