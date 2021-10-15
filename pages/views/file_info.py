from django.http.response import HttpResponse
from pages.models import *
from zipfile import BadZipFile, ZipFile
from django.contrib.auth.decorators import login_required

# get all file records and update their file_name, file_size, and file_count fields

@login_required
def updateFiles(request):
    # if the uploaded file is a zip get the info of the contente
    files = File.objects.all()
    for f in files:
        try:
            if str(f.file_object).split('.')[-1] == "zip":
                try:
                    with ZipFile(f.file_object, 'r') as zip:
                        # get info for all files
                        info = zip.infolist()
                        # count of all files in zip + 1 for the zip file itself, gotta pump those numbers
                        f.file_count = len(info)+1

                        # count the total uncompressed file size for all files in the zip
                        fileSize = 0
                        for file in info:
                            fileSize+=file.file_size
                        
                        f.file_size = fileSize
                except BadZipFile:
                    print("could not extract zip file: " + str(f.file_object))
                    
            else:
                # if its not a zip just get the file size from the file object, file count defaults to 1
                f.file_size = f.file_object.size
            
            f.file_name = str(f.file_object).split('/')[-1]

            f.save()
        except FileNotFoundError:
            print("couldn not find file: " + str(f.file_object))
            pass

    return HttpResponse("File info updated")