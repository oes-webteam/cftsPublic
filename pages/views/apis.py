# ====================================================================
# core
import json
import os
from datetime import datetime
from zipfile import ZipFile
from django.conf import settings

# utilities
from django.utils.dateparse import parse_date

# decorators
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

# responses
from django.shortcuts import render, redirect
# , HttpResponse, FileResponse
from django.http import JsonResponse, HttpResponseRedirect

# cfts settings
from cfts import settings as Settings
# model/database stuff
from pages.models import *

import hashlib

import logging
logger = logging.getLogger('django')
# ====================================================================


@login_required
def setReject(request):
    thestuff = dict(request.POST.lists())

    reject_id = thestuff['reject_id']
    request_id = thestuff['request_id']
    id_list = thestuff['id_list[]']
    
    logger.error("Reject request ID: " + str(request_id))
    logger.error("Reject file IDs: " + str(id_list))

    # update the files to set the rejection
    File.objects.filter(file_id__in=id_list).update(
        rejection_reason_id=reject_id[0])

    # recreate the zip file for the pull
    someRequest = Request.objects.get(request_id=request_id[0])
    network_name = someRequest.network.name
    
    try:
        pull_number = someRequest.pull.pull_id

        url = 'create-zip/'+ str(network_name) +'/'+ str(someRequest.is_centcom)+'/'+ str(pull_number)
        return redirect('create-zip',network_name=network_name,isCentcom=someRequest.is_centcom,rejectPull=pull_number)

    except AttributeError:
        print("Request not found in any pull.")
    return JsonResponse({'mystring': 'isgreat'})

@login_required
def setEncrypt(request):
    thestuff = dict(request.POST.lists())

    request_id = thestuff['request_id']
    id_list = thestuff['id_list[]']
    
    logger.error("Encrypt request ID: " + str(request_id))
    logger.error("Encrypt file IDs: " + str(id_list))
    
    # update the files to set the rejection
    File.objects.filter(file_id__in=id_list).update(
        is_pii=True)

    # recreate the zip file for the pull
    someRequest = Request.objects.get(request_id=request_id[0])
    network_name = someRequest.network.name
    
    try:
        pull_number = someRequest.pull.pull_id

        url = 'create-zip/'+ str(network_name) +'/'+ str(someRequest.is_centcom)+'/'+ str(pull_number)
        return redirect('create-zip',network_name=network_name,isCentcom=someRequest.is_centcom,rejectPull=pull_number)

    except AttributeError:
        print("Request not found in any pull.")
    return JsonResponse({'mystring': 'isgreat'})

@login_required
def getUser(request, id):
    user = User.objects.get(user_id=id)
    data = {
        'user_id': user.user_id,
        'first_name': user.name_first,
        'last_name': user.name_last,
        'email': user.email.address
    }
    return JsonResponse(data)

def runNumbers(request):
    files_reviewed = 0
    files_transfered = 0
    files_rejected = 0
    centcom_files = 0
    file_types = []
    file_type_counts = {
        "pdf": 0,
        "excel": 0,
        "word": 0,
        "ppt": 0,
        "text": 0,
        "img": 0,
        "other": 0
    }
    file_size = 0

    start_date = datetime.strptime(
        request.POST.get('start_date'), "%m/%d/%Y").date()
    end_date = datetime.strptime(
        request.POST.get('end_date'), "%m/%d/%Y").date()

    # only the completed requests, tyvm
    requests_in_range = Request.objects.filter(
        pull__date_complete__date__range=(start_date, end_date))

    for rqst in requests_in_range:

        files_in_request = rqst.files.all()

        for f in files_in_request:
            file_count = 1
            file_name = f.__str__()
            ext = str(file_name.split('.')[-1]).lower()
            file_types.append(ext)
            

            # if it's a zip ...
            if ext == 'zip':
                # ... count all the files in the zip ...
                path = f.file_object.path
                with ZipFile(path, 'r') as zip:
                    contents = zip.namelist()
                    # ... minus the folders
                    for c in contents:
                        if c[-1] == "/" or c[-1] == "\\":
                            contents.remove(c)

                        ext = str(c.split('.')[-1]).lower()
                        file_types.append(ext)
                        file_size = file_size + zip.getinfo(c).file_size
                    file_count = len(contents)
            else:
                file_size = file_size + os.stat(f.file_object.path).st_size            

            # sum it all up
            files_reviewed = files_reviewed + file_count
            # exclude the rejects from the transfers numbers
            if f.rejection_reason == None:
                files_transfered = files_transfered + file_count
                if f.is_centcom == True:
                    centcom_files = centcom_files + file_count
            else:
                files_rejected = files_rejected + file_count

    # add up all file type counts
    pdfCount = file_types.count("pdf")
    file_type_counts["pdf"] = pdfCount

    excelCount = file_types.count("xlsx")+file_types.count("xls")+file_types.count("xlsm")+file_types.count("xlsb")+file_types.count("xltx")+file_types.count("xltm")+file_types.count("xlt")+file_types.count("csv")
    file_type_counts["excel"] = excelCount

    wordCount = file_types.count("doc")+file_types.count("docx")
    file_type_counts["word"] = wordCount

    textCount = file_types.count("txt")
    file_type_counts["text"] = textCount

    pptCount = file_types.count("ppt")+file_types.count("pptx")+file_types.count("pps")
    file_type_counts["ppt"] = pptCount

    imgCount = file_types.count("png")+file_types.count("jpg")+file_types.count("jpeg")+file_types.count("svg")+file_types.count("gif")
    file_type_counts["img"] = imgCount

    zipCount = file_types.count("zip")

    otherCount = len(file_types) - (pdfCount + excelCount + wordCount + imgCount + pptCount + textCount + zipCount)
    file_type_counts["other"] = otherCount

    # make bytes more human readable
    i = 0
    sizeSuffix = {0 : 'Bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}

    while file_size > 1024:
        file_size /= 1024
        i += 1

    return JsonResponse({'files_reviewed': files_reviewed, 'files_transfered': files_transfered, 'files_rejected': files_rejected, 'centcom_files': centcom_files, 'file_types': file_type_counts, 'file_sizes': str(round(file_size,2))+" "+sizeSuffix[i] })

def process ( request ):
    resp = {}
    logger.error('Request Process Initiated')
    
    if request.method == 'POST':
        form_data = request.POST
        form_files = request.FILES
        requestData = ""

        # use the form data to create the necessary records for the request
        try:
            source_email = Email.objects.get(
                address=form_data.get('userEmail'))
        except Email.DoesNotExist:
            source_email = Email(address=form_data.get('userEmail'))
            source_email.save()

        requestData += form_data.get('userEmail')
        
        destination_list = form_data.get( 'targetEmail' ).split( "," )
        target_list = []
        for destination in destination_list:
            try:
                target_email = Email.objects.get(address=destination)
            except Email.DoesNotExist:
                target_email = Email(address=destination)
                target_email.save()
                
            requestData += destination
            target_list.append( target_email )

        # only check for unique users if userID is provided

        buggedPKIs = ['f7d359ebb99a6a8aac39b297745b741b'] #[ acutally bugged hash, my hash for testing]

        requestData += form_data.get('firstName').replace(" ","").lower()
        requestData += form_data.get('lastName').replace(" ","").lower()

        
        if form_data.get('userID') == "":
            print("Not able to get user ID, may create duplicate user.")

            user = User(
                name_first=form_data.get('firstName'),
                name_last=form_data.get('lastName'),
                email=source_email,
                phone=form_data.get('userPhone')
            )
            user.save()
            
        # Make the check for the bugged PKI hash here
        elif form_data.get('userID') in buggedPKIs:
            print("Bugged user ID hash found")

            user = User(
                name_first=form_data.get('firstName')+ "_buggedPKI",
                name_last=form_data.get('lastName'),
                email=source_email,
                phone=form_data.get('userPhone'),
                notes=form_data.get('PKIinfo')
            )
            user.save()
            
        else:
            try:
                User.objects.filter(
                    user_identifier=form_data.get('userID')).update(email=source_email,phone=form_data.get('userPhone'))
                    
                user = User.objects.get(
                    user_identifier=form_data.get('userID'))

                print("User already exists")
                print("Updating user email and phone")
                

            except User.DoesNotExist:
                print("No user found with ID")
                user = User(
                    name_first=form_data.get('firstName'),
                    name_last=form_data.get('lastName'),
                    email=source_email,
                    phone=form_data.get('userPhone'),
                    user_identifier=form_data.get('userID')
                )
                
                user.save()
        request = Request( 
            user = user, 
            network = Network.objects.get( name = form_data.get( 'network' ) ),  
            comments = form_data.get( 'comments' ),
            is_centcom = form_data.get( 'isCentcom' )
        )
        request.save()
        request.target_email.add( *target_list )

        fileList=[]
        
        # add files to the request
        file_info =  json.loads( form_data.get( 'fileInfo' ) )
        print( form_files.getlist( "files" ) )
        for i, f in enumerate( form_files.getlist( "files" )):
            this_file = File(
                file_object = f,
                classification = Classification.objects.get( abbrev = file_info[ i ][ 'classification' ] ),
                is_pii = file_info[ i ][ 'encrypt' ] == 'true',
                is_centcom = form_data.get( 'isCentcom' )
            )
            this_file.save()
            request.files.add( this_file )
            fileList.append(str(f))

        fileList.sort()
        
        for file in fileList:
            requestData += file

        
        requestHash = hashlib.md5()
        requestHash.update(requestData.encode())
        requestHash = requestHash.hexdigest()
        request.request_hash = requestHash
        
        if Request.objects.filter(request_hash=requestHash):
            request.is_dupe=True
        
        request.is_submitted = True
        request.save()
        
        resp = {'status': 'success', 'request_id': request.pk}
        logger.error('Request Process Successful')


    else:
        resp = {'status': 'fail', 'reason': 'bad-request-type',
                'msg': "The 'api-processrequest' view only accepts POST requests."}
        logger.error('Request Process Failed')


    return JsonResponse(resp)

@never_cache
def setConsentCookie(request):
    request.session.__setitem__('consent','consent given')
    request.session.set_expiry(0)
    return redirect('frontend')