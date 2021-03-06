# Generated by Django 4.0.2 on 2022-03-31 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0096_merge_0095_message_0095_request_rhr_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='account_warning_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='last_warned_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
