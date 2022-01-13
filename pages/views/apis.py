# ====================================================================
# core
import json
from datetime import datetime
from zipfile import ZipFile
from django.http.response import HttpResponse
from django.contrib import messages

# decorators
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache

# responses
from django.shortcuts import redirect
from django.template.loader import render_to_string

# , HttpResponse, FileResponse
from django.http import JsonResponse, HttpResponse

# cfts settings
from cfts.settings import NETWORK, DEBUG
# model/database stuff
from pages.models import *

from pages.views.queue import createZip, updateFileReview
from pages.views.auth import superUserCheck, staffCheck
from pages.views.scan import scan

import hashlib

import logging


logger = logging.getLogger('django')
# ====================================================================


@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def setRejectDupes(request):

    data = dict(request.POST.lists())
    dupeReason = Rejection.objects.get(name='Duplicate - No Email')
    
    keeperRequest = Request.objects.filter(request_id=data['keeperRequest'][0]).update(is_dupe=False)
    dupeRequests = Request.objects.filter(request_id__in=data['requestIDs[]'])

    for rqst in dupeRequests:
        files = rqst.files.all()
        files.update(rejection_reason=dupeReason)
        for file in files:
            updateFileReview(request, file.file_id, rqst.request_id)
    
    dupeRequests.update(has_rejected=True, all_rejected=True, rejected_dupe=True)
    
    list(messages.get_messages(request))
    messages.success(request, "All duplicate requests rejected")
    return HttpResponse("All rejected")

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def setReject(request):
    thestuff = dict(request.POST.lists())

    reject_id = thestuff['reject_id']
    request_id = thestuff['request_id']
    id_list = thestuff['id_list[]']

    # update the files to set the rejection
    files = File.objects.filter(file_id__in=id_list)
    files.update(rejection_reason_id=reject_id[0])

    # update request with the has_rejected flag
    rqst = Request.objects.filter(request_id=request_id[0])
    rqst.update(has_rejected=True)

    # update files review status
    for file in files:
        ready_to_pull = updateFileReview(request, file.file_id, request_id[0], skipComplete=True)

    # check if all files in the request are rejected
    files = rqst[0].files.all()
    all_rejected = True

    for file in files:
        if file.rejection_reason_id == None:
            all_rejected = False

    if all_rejected == True:
        rqst.update(all_rejected=True)

    # recreate the zip file for the pull
    network_name = rqst[0].network.name

    messages.success(request, "Files rejected successfully")

    try:
        pull_number = rqst[0].pull.pull_id
        createZip(request, network_name, pull_number)

    except AttributeError:
        print("Request not found in any pull.")
    if DEBUG == True:
        if ready_to_pull == True:
            return JsonResponse({'debug': True, 'flash': False})
        else:
            return JsonResponse({'debug': True})
    else:
        eml = createEml(request,request_id,id_list,reject_id)
        if ready_to_pull == True:
            return JsonResponse({'eml': str(eml), 'flash': False})
        else:
            return JsonResponse({'eml': str(eml)})

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def createEml( request, request_id, files_list, reject_id ):

    rqst = Request.objects.get(request_id=request_id[0])
    rejection = Rejection.objects.get(rejection_id=reject_id[0])

    msgBody = "mailto:" + str(rqst.user.source_email) + "?subject=CFTS File Rejection&body=The following files have been rejected from your transfer request:%0D%0A"

    files = File.objects.filter(file_id__in=files_list)
    for file in files:
        if file == files.last():
            msgBody += str(file.file_object).split("/")[-1] + " "
        else:
            msgBody += str(file.file_object).split("/")[-1] + ", "


    url = "https://"+str(request.get_host())+"/request/"+str(rqst.request_id)
    msgBody += render_to_string('partials/Queue_partials/rejectionEmailTemplate.html', {'rqst': rqst, 'rejection': rejection, 'firstName': rqst.user.name_first, 'url':url}, request)

    return msgBody

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def unReject(request):
    thestuff = dict(request.POST.lists())

    request_id = thestuff['request_id']
    id_list = thestuff['id_list[]']

    # update the files to set the rejection
    files = File.objects.filter(file_id__in=id_list)

    files.update(rejection_reason_id=None)

    for file in files:
        updateFileReview(request, file.file_id, request_id[0], skipComplete=True)

    # check if the request has rejected files in it
    files = Request.objects.get(request_id=request_id[0]).files.all()
    has_rejected = False

    for file in files:
        if file.rejection_reason_id != None:
            has_rejected = True

    if has_rejected == False:
        Request.objects.filter(request_id=request_id[0]).update(has_rejected=False)

    # remove all_rejected flag from request
    Request.objects.filter(request_id=request_id[0]).update(all_rejected=False, rejected_dupe=False)


    # recreate the zip file for the pull
    someRequest = Request.objects.get(request_id=request_id[0])
    network_name = someRequest.network.name

    messages.success(request, "Files unrejected successfully")
    try:
        pull_number = someRequest.pull.pull_id

        return redirect('create-zip',network_name=network_name,rejectPull=pull_number)

    except AttributeError:
        print("Request not found in any pull.")
        return JsonResponse({'Response': 'File not part of pull, reject status reset'})

    return JsonResponse({'error': 'error'})

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def setEncrypt(request):
    thestuff = dict(request.POST.lists())

    request_id = thestuff['request_id']
    id_list = thestuff['id_list[]']

    # update the files to set the rejection
    File.objects.filter(file_id__in=id_list).update(
        is_pii=True)

    # recreate the zip file for the pull
    someRequest = Request.objects.get(request_id=request_id[0])
    network_name = someRequest.network.name

    messages.success(request, "Files marked for encryption")
    
    try:
        pull_number = someRequest.pull.pull_id

        return redirect('create-zip',network_name=network_name,rejectPull=pull_number)

    except AttributeError:
        print("Request not found in any pull.")
    return JsonResponse({'mystring': 'isgreat'})

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def getUser(request, id):
    user = User.objects.get(user_id=id)
    data = {
        'user_id': user.user_id,
        'first_name': user.name_first,
        'last_name': user.name_last,
        'email': user.source_email.address
    }
    return JsonResponse(data)

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def runNumbers(request):
    unique_users = []
    banned_users = []
    skipUsers = ['2ab155e3a751644ee4073972fc4534be158aa0891e8a8df6cd1631f56c61f06073d288fed905d0932fde78155c83208deb661361e64eb1a0f3d736ed04a7e4dc', '00000.0000.0.0000000']
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
        "zip": 0,
        "zipContents": 0,
        "other": 0
    }
    org_counts= {
        "HQ": 0,
        "ARCENT": 0,
        "AFCENT": 0,
        "NAVCENT": 0,
        "MARCENT": 0,
        "SOCCENT": 0,
        "OTHER": 0,
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

        if rqst.user.user_identifier not in skipUsers and rqst.user not in unique_users:
            unique_users.append(rqst.user)
            if rqst.user.banned == True and rqst.user not in banned_users:
                banned_users.append(rqst.user)

        files_in_request = rqst.files.all()

        for f in files_in_request:
            file_name = f.__str__()
            ext = str(file_name.split('.')[-1]).lower()
            file_types.append(ext)



            files_reviewed+= f.file_count
            file_size+= f.file_size

            # exclude the rejects from the transfers numbers
            if f.rejection_reason == None:
                files_transfered+= f.file_count
                
                if f.is_centcom == True:
                    centcom_files+= f.file_count
            else:
                files_rejected+= f.file_count

            if ext == "zip":
                    file_type_counts['zipContents']+= f.file_count

            org = str(f.org)
            if org != "":
                if org == "CENTCOM HQ":
                    org = "HQ"
                org_counts[org]+=f.file_count

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
    file_type_counts["zip"] = zipCount

    otherCount = len(file_types) - (pdfCount + excelCount + wordCount + imgCount + pptCount + textCount + zipCount)
    file_type_counts["other"] = otherCount

    # make bytes more human readable
    i = 0
    sizeSuffix = {0 : 'Bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}

    while file_size > 1024:
        file_size /= 1024
        i += 1

    unique_users_count = len(unique_users)
    banned_users_count = len(banned_users)
    return JsonResponse({'org_counts': org_counts,'files_reviewed': files_reviewed, 'files_transfered': files_transfered, 'files_rejected': files_rejected, 'centcom_files': centcom_files,
    'file_types': file_type_counts, 'file_sizes': str(round(file_size,2))+" "+sizeSuffix[i], 'user_count': unique_users_count, 'banned_count':banned_users_count})

def process ( request ):
    resp = {}

    if request.method == 'POST':
        form_data = request.POST
        form_files = request.FILES
        requestData = ""

        # use the form data to create the necessary records for the request
        sourceNet = Network.objects.get(name=NETWORK)
        try:
            source_email = Email.objects.get(address=form_data.get('userEmail'), network=sourceNet)

        except Email.DoesNotExist:
            source_email = Email(address=form_data.get('userEmail'), network=sourceNet)
            source_email.save()
        except Email.MultipleObjectsReturned:
            source_email = Email.objects.filter(address=form_data.get('userEmail'))[0]
            
        if source_email.network == None:
            source_email.network = sourceNet
            source_email.save()

        requestData += form_data.get('userEmail')

        # log why some users are getting a Network object error, what does their form contain???
        try:
            destinationNet = Network.objects.get( name = form_data.get( 'network' ) )
        except Network.DoesNotExist:
            # log their form 'network' value but cause the error again, because I still don't want their submission to go through
            logger.error("Network object does not exist, network value from form: " + str(form_data.get( 'network' )))
            destinationNet = Network.objects.get( name = form_data.get( 'network' ) )

        destination_list = form_data.get( 'targetEmail' ).split( "," )
        destSplit_list = []

        target_list = []
        for destination in destination_list:
            destSplit_list.append(destination.split("@")[0])
            try:
                target_email = Email.objects.get(address=destination, network=destinationNet)
            except Email.DoesNotExist:
                target_email = Email(address=destination, network=destinationNet)
                target_email.save()
            except Email.MultipleObjectsReturned:
                target_email = Email.objects.filter(address=destination, network=destinationNet)[0]

            requestData += destination
            target_list.append( target_email )

        # only check for unique users if userID is provided

        requestData += form_data.get('firstName').replace(" ","").lower()
        requestData += form_data.get('lastName').replace(" ","").lower()

        from pages.views.auth import getCert, getOrCreateUser

        certInfo = getCert(request)
        cftsUser = getOrCreateUser(request, certInfo)

        org = form_data.get( 'organization' )
        if form_data.get( 'organization' ) =="CENTCOM HQ":
            org = "HQ"
            
        rqst = Request(
            user = cftsUser,
            network = destinationNet,
            comments = form_data.get( 'comments' ),
            org = org,
            is_centcom = form_data.get( 'isCentcom' )
        )
        rqst.save()

        requestData += form_data.get( 'network' )

        rqst.target_email.add( *target_list )
        if form_data.get( 'network' ) == "NIPR":
            if form_data.get('userEmail').split("@")[0] not in destSplit_list:
                rqst.destFlag = True

        fileList=[]

        # add files to the request
        file_info =  json.loads( form_data.get( 'fileInfo' ) )
        # print( form_files.getlist( "files" ) )
        for i, f in enumerate( form_files.getlist( "files" )):
            this_file = File(
                file_object = f,
                # classification = Classification.objects.get( abbrev = file_info[ i ][ 'classification' ] ),
                is_pii = file_info[ i ][ 'encrypt' ] == 'true',
                org = form_data.get( 'organization' ),
                is_centcom = form_data.get( 'isCentcom' ),
            )

            # if the uploaded file is a zip get the info of the contente
            if str(f).split('.')[-1] == "zip":
                with ZipFile(f, 'r') as zip:
                    # get info for all files
                    info = zip.infolist()
                    fileCount = 0

                    for entry in info:
                        if entry.is_dir() == False:
                            fileCount += 1

                    # count of all files in zip
                    this_file.file_count = fileCount

                    # count the total uncompressed file size for all files in the zip
                    fileSize = 0
                    for file in info:
                        fileSize+=file.file_size

                    this_file.file_size = fileSize

            else:
                # if its not a zip just get the file size from the file object, file count defaults to 1
                this_file.file_size = this_file.file_object.size

            this_file.save()
            this_file.file_name = str(this_file.file_object.name).split("/")[-1]
            this_file.save()

            rqst.files.add( this_file )
            fileList.append(str(f))

        fileList.sort()

        for file in fileList:
            requestData += file


        requestHash = hashlib.md5()
        requestHash.update(requestData.encode())
        requestHash = requestHash.hexdigest()
        rqst.request_hash = requestHash

        dupes = Request.objects.filter(pull__date_complete=None, request_hash=requestHash)
        if dupes:
            rqst.is_dupe=True
            dupes.update(is_dupe=True)

        rqst.is_submitted = True
        rqst.save()

        # scan all files in request, append results to file
        try:
            scan(request, rqst.request_id)
        except:
            pass

        resp = {'status': 'success', 'request_id': rqst.pk}

    else:
        resp = {'status': 'fail', 'reason': 'bad-request-type',
                'msg': "The 'api-processrequest' view only accepts POST requests."}


    return JsonResponse(resp)

@never_cache
def setConsentCookie(request):
    request.session.__setitem__('consent','consent given')
    request.session.set_expiry(0)
    return HttpResponse("Consent Header Set")
