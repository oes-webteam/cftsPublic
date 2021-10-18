from cfts import settings
import os
import shutil
from datetime import datetime

# path to uploads folder
uploadsPath = settings.UPLOADS_DIR
pullsPath = settings.PULLS_DIR
tempFilesPath = settings.TEMP_FILES_DIR
scanPath = os.path.join(settings.BASE_DIR,"cfts\\scan")

# get all files in folder
def deleteFiles(directory, maxAge):
    with os.scandir(directory) as files:
        for file in files:
            if file.path.split("\\")[-1] != ".gitignore":
                # file last modified date
                modTime = datetime.fromtimestamp(file.stat().st_mtime)
                fileAge = datetime.fromtimestamp(datetime.now().timestamp())-modTime
                if fileAge.days > maxAge:
                    print("File %s is %s days old. Deleting..." %
                        (file.path, fileAge.days))
                    # delete upload if older than maxAge variable
                    if directory == uploadsPath:
                        shutil.rmtree(file.path)
                    # delete single files
                    else:
                        os.remove(file.path)
                        
                else:
                    daysRemaining = maxAge-fileAge.days
                    if daysRemaining == 0:
                        print("File %s will be deleted in 1 day." % file.path)

                    print("File %s will be deleted in %s days." %
                        (file.path, daysRemaining))


deleteFiles(uploadsPath, 30)
deleteFiles(pullsPath, 30)
deleteFiles(tempFilesPath, 1)
deleteFiles(scanPath, 1)
