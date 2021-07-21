import os
import shutil
from datetime import datetime

# path to uploads folder
uploadsPath = os.path.join(os.path.dirname(os.getcwd()), 'uploads')
print("Uploads folder path: ", uploadsPath)

# get all files in folder
with os.scandir(uploadsPath) as files:
    for file in files:
        # file last modified date
        modTime = datetime.fromtimestamp(file.stat().st_mtime)
        fileAge = datetime.fromtimestamp(datetime.now().timestamp())-modTime
        if fileAge.days > 30:
            print("File %s is %s days old. Deleting..." %
                  (file.path, fileAge.days))
            # delete upload if older than 30 days
            shutil.rmtree(file.path)
        else:
            daysRemaining = 30-fileAge.days
            if daysRemaining == 0:
                print("File %s will be deleted in 1 day." % file.path)

            print("File %s will be deleted in %s days." %
                  (file.path, daysRemaining))
