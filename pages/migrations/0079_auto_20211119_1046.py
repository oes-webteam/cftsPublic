# Generated by Django 3.2.8 on 2021-11-19 15:46

from django.db import migrations
import hashlib

def sha512Wrapper(apps, schema_editor):
    User = apps.get_model("pages", "User")
    db_alias = schema_editor.connection.alias

    for user in User.objects.using(db_alias).all():
        if user.user_identifier == "00000.0000.0.0000000":
            user.user_identifier = None

        else:
            md5Hash = user.user_identifier

            sha512Hash = hashlib.sha512()
            sha512Hash.update(md5Hash.encode())
            sha512Hash = sha512Hash.hexdigest()

            user.user_identifier = sha512Hash
        
        user.save()
        
class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0078_alter_user_user_identifier'),
    ]

    operations = [
        migrations.RunPython(sha512Wrapper),
    ]
