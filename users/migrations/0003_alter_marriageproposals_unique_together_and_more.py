# Generated by Django 5.2.3 on 2025-07-18 04:37

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_marriageproposals_status'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='marriageproposals',
            unique_together={('sender', 'receiver')},
        ),
        migrations.AddField(
            model_name='marriageproposals',
            name='receiver_fullname',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='FIO Unregistered user'),
        ),
        migrations.AlterField(
            model_name='marriageproposals',
            name='receiver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_receiver', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='marriageproposals',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_sender', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(max_length=150),
        ),
        migrations.AlterUniqueTogether(
            name='marriageproposals',
            unique_together={('sender', 'receiver'), ('sender', 'receiver_fullname')},
        ),
    ]
