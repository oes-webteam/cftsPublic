# Generated by Django 2.1.12 on 2021-09-16 13:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0063_rejection_visible'),
    ]

    operations = [
        migrations.AddField(
            model_name='network',
            name='visible',
            field=models.BooleanField(default=True),
        ),
    ]
