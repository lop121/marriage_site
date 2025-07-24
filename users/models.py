from django.conf import settings
from django.contrib.auth import get_user_model
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
    gender = models.SmallIntegerField(
        choices=Gender.choices,
        default=None
    )
    first_name = models.CharField(max_length=150, blank=False, null=False)
    last_name = models.CharField(max_length=150, blank=False, null=False)

    photo = models.ImageField(upload_to='photos/%Y/%m/%d/', default=None, blank=True, null=True, verbose_name='Photo')

    objects = UserManager()
    married = MarriedManager()

    REQUIRED_FIELDS = ['gender', 'first_name', 'last_name']

    @property
    def partner(self):
        marriage = Marriage.objects.filter(
            models.Q(husband=self) | models.Q(wife=self)
        ).first()
        if marriage:
            return marriage.display_partner(self)
        return None

    @property
    def has_photo(self):
        user = get_user_model().objects.get(pk=self.pk)
        if user.photo:
            try:
                return user.photo.url
            except ValueError:
                pass
        return f"{settings.MEDIA_URL}users/default.png"


    def __str__(self):
        return self.username


class Marriage(models.Model):
    class Status(models.IntegerChoices):
        ACTIVE = 1,
        DIVORCED = 0,

    husband = models.ForeignKey('User', on_delete=models.CASCADE, related_name='husband')
    wife = models.ForeignKey('User', on_delete=models.CASCADE, related_name='wife')

    status = models.SmallIntegerField(choices=Status.choices, default=Status.ACTIVE,verbose_name='status')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['husband', 'status'],
                condition=models.Q(status=1),
                name='unique_active_husband'
            ),
            models.UniqueConstraint(
                fields=['wife', 'status'],
                condition=models.Q(status=1),
                name='unique_active_wife'
            ),
        ]

    def display_partner(self, user):
        if user == self.husband:
            return self.wife.get_full_name() or self.wife.username
        elif user == self.wife:
            return self.husband.get_full_name() or self.husband.username
        return None



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

