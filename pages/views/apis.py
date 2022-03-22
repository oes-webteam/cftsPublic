# ====================================================================
# core
import json
import datetime
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
from django.contrib.auth.models import User as authUser
from django.db.models import Q

from pages.views.queue import createZip, updateFileReview
from pages.views.auth import superUserCheck, staffCheck
from pages.views.scan import scan

import hashlib

'''
if you want to send a custom message to the error logs then you can add 2 lines below to any view file.
to send the message do: logger.error("your message here")
'''
import logging
logger = logging.getLogger('django')
# ====================================================================

# function to reject all duplicates of a request, accessed by the "Reject All Duplicate Requests" button the the transfer request details page
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def setRejectDupes(request):

    postData = dict(request.POST.lists())
    dupeReason = Rejection.objects.get(name='Duplicate - No Email')

    keeperRequest = Request.objects.filter(request_id=postData['keeperRequest'][0]).update(is_dupe=False)
    dupeRequests = Request.objects.filter(request_id__in=postData['requestIDs[]'])

    # loop through all duplicate requests and reject all of their files, mark the rejector as a file reviewer for all files
    for rqst in dupeRequests:
        files = rqst.files.all()
        files.update(rejection_reason=dupeReason)
        for file in files:
            updateFileReview(request, file.file_id, rqst.request_id)

    # update flags on the duplicate requests, "rejected_dupe" will hide the requests from the queue
    dupeRequests.update(has_rejected=True, all_rejected=True, rejected_dupe=True)

    # clear out the Django messages array from all the calls we did to updateFileReview
    # messages are removed from the Django messages array when they are accessed from any python or html file
    list(messages.get_messages(request))

    messages.success(request, "All duplicate requests rejected")
    return HttpResponse("All rejected")

# function to reject one or many files
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def setReject(request):
    postData = dict(request.POST.lists())

    reject_id = postData['reject_id']
    request_id = postData['request_id']
    id_list = postData['id_list[]']

    # update the files to set the rejection
    files = File.objects.filter(file_id__in=id_list)
    files.update(rejection_reason_id=reject_id[0])

    # update request with the has_rejected flag
    rqst = Request.objects.filter(request_id=request_id[0])
    rqst.update(has_rejected=True)

    # update files review status, skipComplete will prevent a files review status from progressing forward when calling updateFileReview()
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

    messages.success(request, "Files rejected successfully")

    # recreate the zip file for the pull, this will exclude the newly rejected files
    network_name = rqst[0].network.name

    # see if the request is part of a pull, if it is call createZip()
    try:
        pull_number = rqst[0].pull.pull_id
        createZip(request, network_name, pull_number)

    # request wasn't part of a pull, no need to call createZip()
    except AttributeError:
        print("Request not found in any pull.")

    # normally rejecting a file would also generate an email to go along with it, but that gets really annoying when doing dev work so emails are disabled when DEBUG==True
    # if DEBUG==False then we call createEml() and return the email generated with a JSON response
    if DEBUG == True:
        if ready_to_pull == True:
            return JsonResponse({'debug': True, 'flash': False})
        else:
            return JsonResponse({'debug': True})
    else:
        eml = createEml(request, request_id, id_list, reject_id)
        if ready_to_pull == True:
            return JsonResponse({'eml': str(eml), 'flash': False})
        else:
            return JsonResponse({'eml': str(eml)})

# function to generate file rejection email
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def createEml(request, request_id, files_list, reject_id):

    # get the Request and Rejection object from args
    rqst = Request.objects.get(request_id=request_id[0])
    rejection = Rejection.objects.get(rejection_id=reject_id[0])

    # create a mailto link...
    # yeah, that's how we send out system emails because we aren't allowed to have an email relay server... thanks J6
    msgBody = "mailto:" + str(rqst.user.source_email) + "?cc=" + str(rqst.RHR_email) + "&subject=CFTS File Rejection&body=The following files have been rejected from your transfer request:%0D%0A"

    # list the names of all the files being rejected in the email
    files = File.objects.filter(file_id__in=files_list)
    for file in files:
        if file == files.last():
            msgBody += str(file.file_object).split("/")[-1] + " "
        else:
            msgBody += str(file.file_object).split("/")[-1] + ", "

    # this is the url that users can use to get more details about their request
    url = "https://" + str(request.get_host()) + "/request/" + str(rqst.request_id)

    # render out the email template and append it to the mailto link
    msgBody += render_to_string('partials/Queue_partials/rejectionEmailTemplate.html', {'rqst': rqst, 'rejection': rejection, 'firstName': rqst.user.name_first, 'url': url}, request)
   
    return msgBody

# function to remove a files rejection status/reason, this is almost the exact oposite of setReject()
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def unReject(request):
    postData = dict(request.POST.lists())

    request_id = postData['request_id']
    id_list = postData['id_list[]']

    # set rejection reason on file to None
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

    messages.success(request, "Files unrejected successfully")

    # recreate the zip file for the pull
    someRequest = Request.objects.get(request_id=request_id[0])
    network_name = someRequest.network.name

    try:
        pull_number = someRequest.pull.pull_id

        return redirect('create-zip', network_name=network_name, rejectPull=pull_number)

    except AttributeError:
        print("Request not found in any pull.")
        return JsonResponse({'Response': 'File not part of pull, reject status reset'})

# function to mark a file for encryption, this dosen't do any actual encryption but lets the transfer team know which files need to be sent encrypted
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def setEncrypt(request):
    postData = dict(request.POST.lists())

    request_id = postData['request_id']
    id_list = postData['id_list[]']

    # add is_pii flag to files
    File.objects.filter(file_id__in=id_list).update(is_pii=True)

    messages.success(request, "Files marked for encryption")

    # recreate the zip file for the pull
    someRequest = Request.objects.get(request_id=request_id[0])
    someRequest.has_encrypted = True
    someRequest.save()

    network_name = someRequest.network.name

    try:
        pull_number = someRequest.pull.pull_id

        return redirect('create-zip', network_name=network_name, rejectPull=pull_number)

    except AttributeError:
        print("Request not found in any pull.")
        return JsonResponse({'Response': 'File not part of pull, encryption status set'})


# function to collect various metrics for a certain date range, from /reports url path
def runNumbers(request, api_call=False):
    # initialize all our metrics
    unique_users = []
    banned_users = []
    warned_users = []

    '''
    ughhhh...
    So users all have a unique userID which is a hash of the "Subject Alternative Name" from the certificate on a users SIPR card, but trafic from users outside of USCENTCOM is sent throuh F5 boundery servers
    and somewhere along the line their user certificate is replaced with the server certificate for CFTS. Why? beats me, but the F5 team is taking their sweet time fixing the issue. What this all means is that
    internal USCENTCOM users have a hased userID as expected, but all external users would have the same hash as eachother. This wasn't apparent at first and took a while to find a work around which means that
    there are a ton of User objects in the database with the hash below. We wouldn't count any of these users in our metrics because many of these users we duplicate account. This isn't really a problem any
    more because now all users need to register an account to use CFTS, but this is a reminder of the days when all you needed to use CFTS was you SIPR card.
    '''
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
    org_counts = {
        "HQ": 0,
        "ARCENT": 0,
        "AFCENT": 0,
        "NAVCENT": 0,
        "MARCENT": 0,
        "SOCCENT": 0,
        "OTHER": 0,
    }
    file_size = 0

    if api_call == False:
        start_date = datetime.datetime.strptime(
            request.POST.get('start_date'), "%m/%d/%Y").date()
        end_date = datetime.datetime.strptime(
            request.POST.get('end_date'), "%m/%d/%Y").date()
    else:
        start_date = datetime.date.today() - datetime.timedelta(days=7)
        end_date = datetime.date.today()

    staffID = request.POST.get('staffUser')

    requests_in_range = Request.objects.filter(
        pull__date_complete__date__range=(start_date, end_date))

    for rqst in requests_in_range:
        if rqst.rejected_dupe == False:
            if staffID != "None":
                files_in_request = rqst.files.filter(Q(user_oneeye__id=staffID) | Q(user_twoeye__id=staffID))
                if files_in_request.exists() == False:
                    continue
            else:
                files_in_request = rqst.files.all()

            # if the user doesn't have one of the buggedPKI hashes and hasn't already been accounted for then add them
            if rqst.user.user_identifier not in skipUsers and rqst.user not in unique_users:
                unique_users.append(rqst.user)

                # if they are banned count add them to the banned users list
                if rqst.user.banned == True and rqst.user not in banned_users:
                    banned_users.append(rqst.user)

                if rqst.user.last_warned_on != None and rqst.user.last_warned_on.date() >= start_date and rqst.user.last_warned_on.date() <= end_date and rqst.user not in warned_users:
                    warned_users.append(rqst.user)

            for f in files_in_request:
                file_name = f.__str__()
                # get file extension from the file name, add it to the list of file extensions
                ext = str(file_name.split('.')[-1]).lower()
                file_types.append(ext)

                # add all files to file count, add combined file size to file size total
                files_reviewed += f.file_count
                file_size += f.file_size

                # exclude the rejects from the transfers numbers, they are counted separately
                if f.rejection_reason == None:
                    files_transfered += f.file_count

                    # if the file is from a CENTCOM org count it
                    if f.is_centcom == True:
                        centcom_files += f.file_count
                else:
                    files_rejected += f.file_count

                # count how many files were in zips
                if ext == "zip":
                    file_type_counts['zipContents'] += f.file_count

                # file count by organization
                org = str(f.org)
                if org != "":
                    if org == "CENTCOM HQ":
                        org = "HQ"
                    org_counts[org] += f.file_count

    # add up all file type counts
    pdfCount = file_types.count("pdf")
    file_type_counts["pdf"] = pdfCount

    excelCount = file_types.count("xlsx") + file_types.count("xls") + file_types.count("xlsm") + file_types.count("xlsb") + file_types.count("xltx") + file_types.count("xltm") + file_types.count("xlt") + file_types.count("csv")
    file_type_counts["excel"] = excelCount

    wordCount = file_types.count("doc") + file_types.count("docx")
    file_type_counts["word"] = wordCount

    textCount = file_types.count("txt")
    file_type_counts["text"] = textCount

    pptCount = file_types.count("ppt") + file_types.count("pptx") + file_types.count("pps")
    file_type_counts["ppt"] = pptCount

    imgCount = file_types.count("png") + file_types.count("jpg") + file_types.count("jpeg") + file_types.count("svg") + file_types.count("gif")
    file_type_counts["img"] = imgCount

    zipCount = file_types.count("zip")
    file_type_counts["zip"] = zipCount

    otherCount = len(file_types) - (pdfCount + excelCount + wordCount + imgCount + pptCount + textCount + zipCount)
    file_type_counts["other"] = otherCount

    # make bytes more human readable
    i = 0
    sizeSuffix = {0: 'Bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}

    while file_size > 1024:
        file_size /= 1024
        i += 1
    
    unique_users_count = len(unique_users)
    banned_users_count = len(banned_users)
    warned_users_count = len(warned_users)
    return JsonResponse({'org_counts': org_counts, 'files_reviewed': files_reviewed, 'files_transfered': files_transfered, 'files_rejected': files_rejected, 'centcom_files': centcom_files,
                         'file_types': file_type_counts, 'file_sizes': str(round(file_size, 2))+" "+sizeSuffix[i], 'user_count': unique_users_count, 'banned_count': banned_users_count, 'warned_count': warned_users_count})


# function to create Request and File objects from homepage transfer request form
def process(request):
    resp = {}

    if request.method == 'POST':
        form_data = request.POST
        form_files = request.FILES

        # this string is used to collect information about a request and generate a request hash that is used to detect duplicate requests submitted to the system
        requestData = ""

        # use the form data to create the necessary records for the request

        # the network the file was submitted on, pulls from the settings.py file
        sourceNet = Network.objects.get(name=NETWORK)

        # get or create a source Email object for the user
        try:
            source_email = Email.objects.get(address=form_data.get('userEmail'), network=sourceNet)

        # Email object dosen't exist, make one
        except Email.DoesNotExist:
            source_email = Email(address=form_data.get('userEmail'), network=sourceNet)
            source_email.save()

        # get() returned more than one Email object, use filter instead and use first object, update Email.network if needed
        except Email.MultipleObjectsReturned:
            source_email = Email.objects.filter(address=form_data.get('userEmail'))[0]

        if source_email.network == None:
            source_email.network = sourceNet
            source_email.save()

        # add source email to request hash
        requestData += form_data.get('userEmail')

        # get the destination Network object
        destinationNet = Network.objects.get(name=form_data.get('network'))

        # users used to be able to transfer to multiple email addresses, the code below should be refactored to assume only one destination email
        destination_list = form_data.get('targetEmail').split(",")
        destSplit_list = []

        target_list = []
        for destination in destination_list:
            # split emails at the "@", this is used along with the source email and will raise a flag if they do not match. needs to be imporved, causes a lot of false positives
            destSplit_list.append(destination.split("@")[0])

            # same process of get or create email but for destination instead of source
            try:
                target_email = Email.objects.get(address=destination, network=destinationNet)
            except Email.DoesNotExist:
                target_email = Email(address=destination, network=destinationNet)
                target_email.save()
            except Email.MultipleObjectsReturned:
                target_email = Email.objects.filter(address=destination, network=destinationNet)[0]

            # add destination email to request hash
            requestData += destination
            target_list.append(target_email)

        # add first and last name to request hash
        requestData += form_data.get('firstName').replace(" ", "").lower()
        requestData += form_data.get('lastName').replace(" ", "").lower()

        # importing two functions from auth.py, importing them at the top of the file was causing a circular import error and I was too lazy to fix it...
        from pages.views.auth import getCert, getOrCreateUser

        # get user cert info, use cert info to return a User object, see auth.py for details
        certInfo = getCert(request)
        cftsUser = getOrCreateUser(request, certInfo)

        # check to see if a user is banned, if so kick them to the home page
        if cftsUser.banned == True:
            return JsonResponse({'banned': True})

        # get users organization from request form
        org = form_data.get('organization')
        if form_data.get('organization') == "CENTCOM HQ":
            org = "HQ"

        # create the initial Request object
        rqst = Request(
            user=cftsUser,
            network=destinationNet,
            comments=form_data.get('comments'),
            org=org,
            is_centcom=form_data.get('isCentcom'),
            RHR_email=form_data.get('RHREmail')
        )
        rqst.save()

        # add destination network to request hash
        requestData += form_data.get('network')

        # add destination email to request object and raise email mismatch flag if needed
        rqst.target_email.add(*target_list)
        if form_data.get('network') == "NIPR":
            if form_data.get('userEmail').split("@")[0] not in destSplit_list:
                rqst.destFlag = True

        fileList = []

        staff_emails = authUser.objects.filter(is_staff=True).values_list('email', flat=True)

        if form_data.get('RHREmail') in staff_emails or form_data.get('RHREmail') == source_email.address or form_data.get('RHREmail') in destination_list:
            rqst.destFlag = True

        # get files from request form
        file_info = json.loads(form_data.get('fileInfo'))

        has_encrypted = False
        # create a File object for every file
        for i, f in enumerate(form_files.getlist("files")):
            if file_info[i]['encrypt'] == 'true':
                has_encrypted = True

            this_file = File(
                file_object=f,
                is_pii=file_info[i]['encrypt'] == 'true',
                org=form_data.get('organization'),
                is_centcom=form_data.get('isCentcom'),
            )

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
                    this_file.file_count = fileCount

                    # count the total uncompressed file size for all files in the zip
                    fileSize = 0
                    for file in info:
                        fileSize += file.file_size

                    this_file.file_size = fileSize

            else:
                # if its not a zip just get the file size from the file object, file count defaults to 1
                this_file.file_size = this_file.file_object.size

            # save the file, let Django strip illegal characters from the path, and trim the dir path from the filename
            this_file.save()
            this_file.file_name = str(this_file.file_object.name).split("/")[-1]
            this_file.save()

            # add the file to the request and the list of files used in the request hash
            rqst.files.add(this_file)
            rqst.has_encrypted = has_encrypted
            fileList.append(str(f))

        # sort the list of files so the order of files does not affect the duplicate checking
        fileList.sort()

        for file in fileList:
            requestData += file

        # create the request hash and add it to the Request object
        requestHash = hashlib.md5()
        requestHash.update(requestData.encode())
        requestHash = requestHash.hexdigest()
        rqst.request_hash = requestHash

        # check for any files with the same hash that have not been pulled yet
        dupes = Request.objects.filter(pull__date_complete=None, request_hash=requestHash)

        # update duplicate flags for all Request objects returned
        if dupes:
            rqst.is_dupe = True
            dupes.update(is_dupe=True)

        # if we have gotten this far without an error than this request is good to go, Requests where is_submitted == False are filtered out from the queue and pulls
        rqst.is_submitted = True
        rqst.save()

        # scan all files in request for any match of a DirtyWord object, append results to file, an error in a scan will NOT prevent the request from being submitted
        try:
            scan(request, rqst.request_id)
        except:
            pass

        resp = {'status': 'success', 'request_id': rqst.pk}

    else:
        resp = {'status': 'fail', 'reason': 'bad-request-type',
                'msg': "The 'api-processrequest' view only accepts POST requests."}

    return JsonResponse(resp)

# function to set the consent cookie for the current browser session, this cookie is required to reach any CFTS page
@never_cache
def setConsentCookie(request):
    request.session.__setitem__('consent', 'consent given')
    request.session.set_expiry(0)
    return HttpResponse("Consent Header Set")
