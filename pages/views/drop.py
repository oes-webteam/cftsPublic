# ====================================================================
# core
import ast
import datetime
import shutil
from django.contrib import messages
from django.core import paginator
from django.core.files import File as DjangoFile
from django.templatetags.static import static
from zipfile import ZipFile
from django.utils import timezone
from cfts import settings as cftsSettings

# cryptography
import os
import string
import random
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

# decorators
from django.contrib.auth.decorators import login_required, user_passes_test

from pages.views.auth import staffCheck, getOrCreateEmail

# responses
from django.shortcuts import redirect, render
from django.template.loader import render_to_string

from django.http import JsonResponse, FileResponse, HttpResponse

# model/database stuff
from pages.models import *

import logging

logger = logging.getLogger('django')

# function to collect Request objects and serve the transfer queue page, only available to staff users
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def dropZone(request):
    dropRequests = Drop_Request.objects.filter(email_sent=False)

    requestPage = paginator.Paginator(dropRequests, 10)
    pageNum = request.GET.get('page')
    pageObj = requestPage.get_page(pageNum)
    return render(request, 'pages/drop-zone.html', context={'dropRequests': pageObj})

def treeScan(requestPaths, path):
    for dir in os.scandir(path):
        if dir.is_file():
            requestPaths.append(os.path.dirname(dir.path))
        else:
            treeScan(requestPaths, dir)
    return requestPaths

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def processDrop(request):
    try:
        request_files = request.FILES
        i, f = list(enumerate(request_files.getlist("dropZip")))[0]

        drop_folder = cftsSettings.DROPS_DIR+"\\drop_1"

        i = 2
        while True:
            if os.path.isdir(drop_folder):
                drop_folder = cftsSettings.DROPS_DIR+"\\drop_"+str(i)
                i += 1
            else:
                break

        zip = ZipFile(f, 'r')
        zip.extractall(drop_folder)

        requestPaths = set(treeScan([], drop_folder))

        request_info_re = re.compile('_request_info.txt')
        for path in requestPaths:
            with open(path+"\\_request_info.txt", 'rb') as infile:
                request_info = ast.literal_eval(infile.read().decode('utf-8'))
                infile.close()

            # *******************change the hard coded network******************************
            dropRequest = Drop_Request(
                target_email=getOrCreateEmail(request, request_info['email'], "NIPR"),
                has_encrypted=request_info['encrypted'],
                request_info=request_info,
                delete_on=timezone.now() + datetime.timedelta(days=3),
                request_code=''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(8)),
            )
            dropRequest.save()

            for f in os.scandir(path):
                filePath = f.path

                if request_info_re.match(filePath.split("\\")[-1]) == None:
                    with open(filePath, mode='rb') as inFile:
                        fileObj = DjangoFile(inFile, name=f.name)
                        dropFile = Drop_File(
                            file_object=fileObj,
                        )

                        dropFile.save()

                    # if the uploaded file is a zip get the info of the contents
                    if str(f).split('.')[-1] == "zip":
                        with ZipFile(f, 'r') as zip:
                            # get info for all files
                            info = zip.infolist()
                            fileCount = 0

                            # only count files, not folders
                            for entry in info:
                                if entry.is_dir() == False:
                                    fileCount += 1

                            # count of all files in zip
                            dropFile.file_count = fileCount

                            # count the total uncompressed file size for all files in the zip
                            fileSize = 0
                            for file in info:
                                fileSize += file.file_size

                            dropFile.file_size = fileSize

                    # save the file, let Django strip illegal characters from the path, and trim the dir path from the filename

                    dropFile.file_name = str(dropFile.file_object.name).split("/")[-1]
                    dropFile.file_size = dropFile.file_object.size

                    dropFile.save()

                    # add the file to the request and the list of files used in the request hash
                    dropRequest.files.add(dropFile)
                    dropRequest.save()

        shutil.rmtree(drop_folder)
        messages.success(request, "Requests Upload Successful")

    except Exception as e:
        messages.error(request, "Error Creating Requests")
    return HttpResponse(set(requestPaths))


def dropDetails(request, id, PIN=None):
    drop = Drop_Request.objects.get(request_id=id)

    if PIN == None:
        return render(request, 'pages/dropDetails.html', {'status': "prompt"})
    elif PIN == drop.request_code:
        return render(request, 'pages/dropDetails.html', {'status': "authorized", 'drop': drop, 'encrypted': ast.literal_eval(drop.request_info)['encrypted']})
    else:
        return render(request, 'pages/dropDetails.html', {'status': "not authorized"})
