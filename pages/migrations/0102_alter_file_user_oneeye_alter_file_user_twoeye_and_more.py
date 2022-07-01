# Generated by Django 4.0.3 on 2022-06-29 13:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pages', '0101_remove_drop_request_has_encrypted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='user_oneeye',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='file_user_oneeye', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='file',
            name='user_twoeye',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='file_user_twoeye', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='pull',
            name='user_complete',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='request_user_complete', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='pull',
            name='user_oneeye',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='request_user_oneeye', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='pull',
            name='user_pulled',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='request_user_pulled', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='pull',
            name='user_twoeye',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='request_user_twoeye', to=settings.AUTH_USER_MODEL),
        ),
    ]