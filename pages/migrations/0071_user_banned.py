# Generated by Django 3.2.8 on 2021-10-21 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0070_merge_20211014_0643'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='banned',
            field=models.BooleanField(default=False),
        ),
    ]