# Generated by Django 3.2.8 on 2021-12-09 17:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0087_auto_20211209_0904'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='pull',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='pages.pull'),
        ),
    ]
