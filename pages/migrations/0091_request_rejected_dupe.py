# Generated by Django 3.2.8 on 2022-01-07 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0090_request_files_scanned'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='rejected_dupe',
            field=models.BooleanField(default=False),
        ),
    ]
