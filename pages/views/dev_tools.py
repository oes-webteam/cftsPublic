# ====================================================================
from pages.models import *
from django.contrib.auth.decorators import login_required, user_passes_test
from cfts import settings
import os
import shutil
from datetime import datetime
from django.contrib import messages
import traceback
from pages.views.auth import superUserCheck, staffCheck
from django.utils import timezone
# ====================================================================

# function called from fileCleanup() to delete files in a directory that are over a number of days old
def deleteFiles(directory, maxAge):
    # get all files in directory passed in from args
    with os.scandir(directory) as files:
        for file in files:
            # don't delete the gitignore
            if file.path.split("\\")[-1] != ".gitignore":
                # calculate age of file from the files 'last modified' time
                modTime = datetime.fromtimestamp(file.stat().st_mtime)
                fileAge = datetime.fromtimestamp(datetime.now().timestamp())-modTime
                # if file is older that maxAge passed in from args then delete it and any parent folders
                if fileAge.days > maxAge:
                    print("File %s is %s days old. Deleting..." % (file.path, fileAge.days))
                    # delete upload if older than maxAge variable
                    try:
                        shutil.rmtree(file.path)
                    # delete single files
                    except:
                        try:
                            os.remove(file.path)
                        except:
                            pass


def deleteDrops():
    oldDrops = Drop_Request.objects.filter(delete_on__lte=timezone.now())

    for drop in oldDrops:
        print("Deleting drop_request %s" % (drop.request_id))
        for file in drop.files.all():
            print("Deleting drop_file %s" % (file.file_id))
            file.delete()
        drop.delete()

# function to call deleteFiles() from a url, only available to superusers
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def fileCleanup(request):
    # paths to directories you want to nuke
    uploadsPath = settings.UPLOADS_DIR
    pullsPath = settings.PULLS_DIR
    scanPath = os.path.join(settings.BASE_DIR, "cfts\\scan")
    dropsPath = settings.DROPS_DIR

    # call deleteFiles() with a path and maximum file age
    try:
        deleteFiles(uploadsPath, 30)
        deleteFiles(pullsPath, 30)
        deleteFiles(scanPath, 1)
        deleteFiles(dropsPath, 5)
        deleteDrops()
    except Exception as e:
        messages.error(request, "Could not perform scheduled file deletion." + str(traceback.format_exc()))


# function to update all users update_info field to force them to update their user info.
# this is meant to by imported into a blank db migration, python manage.py makemigrations --empty appName
# in the operations list of the migration call RunPython() with resetUpdateInfo() and reverseFunction() as args
# the migration can be deleted once migrated
def resetUpdateInfo(apps, schema_editor):
    User = apps.get_model("pages", "User")
    db_alias = schema_editor.connection.alias

    for user in User.objects.using(db_alias).all():
        user.update_info = True
        user.save()


def reverseFunction(apps, schema_editor):
    pass
