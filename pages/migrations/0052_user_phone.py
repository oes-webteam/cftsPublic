# Generated by Django 2.1.12 on 2021-05-19 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0051_user_is_centcom'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.CharField(default='000-000-0000', max_length=50),
        ),
    ]
