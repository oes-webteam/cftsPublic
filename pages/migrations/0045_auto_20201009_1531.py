# Generated by Django 2.1.12 on 2020-10-09 19:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0044_auto_20201009_1458'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcelink',
            name='file_object',
            field=models.FileField(blank=True, null=True, upload_to='templates/partials/files/'),
        ),
    ]
