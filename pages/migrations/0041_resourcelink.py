# Generated by Django 2.1.12 on 2020-10-09 17:45

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0040_auto_20200513_1024'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceLink',
            fields=[
                ('resourcelink_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('url_path', models.CharField(max_length=255)),
                ('sort_order', models.IntegerField()),
            ],
            options={
                'ordering': ['sort_order'],
            },
        ),
    ]
