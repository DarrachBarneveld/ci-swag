# Generated by Django 4.2.10 on 2024-03-02 12:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_subscription_userprofile_active_subscription_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='superuser',
            field=models.BooleanField(default=False),
        ),
    ]
