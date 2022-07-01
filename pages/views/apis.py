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

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def setRejectDupes(request):
    """
    Reject all requests using the request ids from the POST request. Change is_dupe to False for the keeperRequest

    :param request: the request object
    :return: an HttpResponse object
    """

    postData = dict(request.POST.lists())
    dupeReason = Rejection.objects.get(name='Duplicate - No Email')

    # Updating the is_dupe field of the keeperRequest to False.
    keeperRequest = Request.objects.filter(request_id=postData['keeperRequest'][0]).update(is_dupe=False)

    # Filtering the Request objects by the request_id in the postData.
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

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def setReject(request):
    """
    It updates the database with the rejection reason for the files that were rejected, then it checks
    if all files in the request were rejected, if they were then it updates the request with the
    all_rejected flag and makes the request pullable

    :param request: the request object
    :return: a JsonResponse object.
    """

    postData = dict(request.POST.lists())

    reject_id = postData['reject_id']
    request_id = postData['request_id']
    id_list = postData['id_list[]']

    # Update the files to set the rejection
    files = File.objects.filter(file_id__in=id_list)
    files.update(rejection_reason_id=reject_id[0])

    # update request with the has_rejected flag
    rqst = Request.objects.filter(request_id=request_id[0])
    rqst.update(has_rejected=True)

    # Update files review status because a rejected file counts as fully reviewed
    # skipComplete will prevent a files review status from progressing forward when calling updateFileReview()
    for file in files:
        ready_to_pull = updateFileReview(request, file.file_id, request_id[0], skipComplete=True)

    # Check if all files in the request are rejected
    files = rqst[0].files.all()
    all_rejected = True

    for file in files:
        if file.rejection_reason_id == None:
            all_rejected = False

    if all_rejected == True:
        rqst.update(all_rejected=True)

    messages.success(request, "Files rejected successfully")

    # Recreate the zip file for the pull, this will exclude the newly rejected files
    network_name = rqst[0].network.name

    # Checking if the request is part of a pull. If it is, it will call createZip()
    try:
        pull_number = rqst[0].pull.pull_id
        createZip(request, network_name, pull_number)

    # Request wasn't part of a pull, no need to call createZip()
    except AttributeError:
        print("Request not found in any pull.")

    # Normally rejecting a file would also generate an email to go along with it, but that gets really annoying when doing dev work so emails are disabled when DEBUG==True
    # If DEBUG==False then we call createEml() and return the email generated with a JSON response
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

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def createEml(request, request_id, files_list, reject_id):
    """
    It takes in a request object, a request id, a list of file ids, and a rejection id. It then gets the
    Request and Rejection objects from the database, creates a mailto link, lists the names of all the
    files being rejected in the email, creates a url that users can use to get more details about their
    request, and renders out the email template and appends it to the mailto link

    :param request: the request object
    :param request_id: the id of the request that the files are being rejected from
    :param files_list: a list of file_ids that are being rejected
    :param reject_id: the id of the rejection object
    :return: The mailto link is being returned.
    """

    # Get the Request and Rejection objects
    rqst = Request.objects.get(request_id=request_id[0])
    rejection = Rejection.objects.get(rejection_id=reject_id[0])

    # Create a mailto link...
    # Yeah, that's how we send out system emails because we aren't allowed to have an email relay server... thanks J6
    msgBody = "mailto:" + str(rqst.user.source_email) + "?cc=" + str(rqst.RHR_email) + "&subject=CFTS File Rejection&body=The following files have been rejected from your transfer request:%0D%0A"

    # List the names of all the files being rejected in the email
    files = File.objects.filter(file_id__in=files_list)
    for file in files:
        if file == files.last():
            msgBody += str(file.file_object).split("/")[-1] + " "
        else:
            msgBody += str(file.file_object).split("/")[-1] + ", "

    # This is the url that users can use to get more details about their request
    url = "https://" + str(request.get_host()) + "/request/" + str(rqst.request_id)

    # Render out the email template and append it to the mailto link
    msgBody += render_to_string('partials/Queue_partials/rejectionEmailTemplate.html', {'rqst': rqst, 'rejection': rejection, 'firstName': rqst.user.name_first, 'url': url}, request)

    return msgBody

# function to remove a files rejection status/reason, this is almost the exact oposite of setReject()
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def unReject(request):
    """
    Remove rejection from all files ids in the POST request, and check if the request still has rejected files

    :param request: The request object
    :return: The return is a redirect to the create-zip view.
    """
    postData = dict(request.POST.lists())

    request_id = postData['request_id']
    id_list = postData['id_list[]']

    # Updating the rejection_reason_id to None for all the files in the list.
    files = File.objects.filter(file_id__in=id_list)
    files.update(rejection_reason_id=None)

    # Updating the file review status for each file in the list
    # For safety any unrejected file is no longer considered reviewed
    for file in files:
        updateFileReview(request, file.file_id, request_id[0], skipComplete=True)

    # Checking if any of the files in the request has a rejection reason. If it does, it sets the
    # has_rejected field to True. If it doesn't, it sets the has_rejected field to False.
    files = Request.objects.get(request_id=request_id[0]).files.all()
    has_rejected = False

    for file in files:
        if file.rejection_reason_id != None:
            has_rejected = True

    if has_rejected == False:
        Request.objects.filter(request_id=request_id[0]).update(has_rejected=False)

    # Remove all_rejected flag from request
    Request.objects.filter(request_id=request_id[0]).update(all_rejected=False, rejected_dupe=False)

    messages.success(request, "Files unrejected successfully")

    # Recreate the zip file for the pull
    someRequest = Request.objects.get(request_id=request_id[0])
    network_name = someRequest.network.name

    try:
        pull_number = someRequest.pull.pull_id

        return redirect('create-zip', network_name=network_name, rejectPull=pull_number)

    except AttributeError:
        print("Request not found in any pull.")
        return JsonResponse({'Response': 'File not part of pull, reject status reset'})

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def setEncrypt(request):
    """
    Marks all files in POST request for encryption, this dosen't do any actual encryption but lets the transfer team know which files need to be sent encrypted

    :param request: the request object
    :return: The return is a redirect to the create-zip view.
    """

    postData = dict(request.POST.lists())

    request_id = postData['request_id']
    id_list = postData['id_list[]']

    # Updating the is_pii field of the File model to True for all the files whose file_id is in the
    # id_list.
    File.objects.filter(file_id__in=id_list).update(is_pii=True)

    messages.success(request, "Files marked for encryption")

    # Recreate the zip file for the pull
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


def runNumbers(request, api_call=False):
    """
    It takes a start and end date and returns a JSON object with a bunch of metrics about the files that
    were transfered during that time period

    Optionally takes a Django User object to further filter metrics

    :param request: the request object from the view
    :param api_call: if the function is being called from the API or not, defaults to False (optional)
    :return: A JSON object with the following keys:
    """

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

    # Checking if the request is coming from the API or not. If it is coming from the API, it will set
    # the start_date and end_date to the current date minus 7 days and the current date respectively.
    # If it is not coming from the API, it will set the start_date and end_date to the values that are
    # passed in the request.
    if api_call == False:
        start_date = datetime.datetime.strptime(
            request.POST.get('start_date'), "%m/%d/%Y").date()
        end_date = datetime.datetime.strptime(
            request.POST.get('end_date'), "%m/%d/%Y").date()
    else:
        start_date = datetime.date.today() - datetime.timedelta(days=7)
        end_date = datetime.date.today()

    # Getting the staffID from the form.
    staffID = request.POST.get('staffUser')

    # Get all requests in the date range that are part of a completed pull.
    requests_in_range = Request.objects.filter(pull__date_complete__date__range=(start_date, end_date))

    for rqst in requests_in_range:
        # Don't include rejected duplicate requests in metrics
        if rqst.rejected_dupe == False:
            # If a staff user was passed as a filter check if the request has any files reviewed by that user to gather metrics on, if not then skip to the next request
            # If no staff user was passed as a filter then gather metrics on all files in the request
            if staffID != "None":
                files_in_request = rqst.files.filter(Q(user_oneeye__id=staffID) | Q(user_twoeye__id=staffID))
                if files_in_request.exists() == False:
                    continue
            else:
                files_in_request = rqst.files.all()

            # If the user doesn't have one of the buggedPKI hashes and hasn't already been accounted for then add them
            if rqst.user.user_identifier not in skipUsers and rqst.user not in unique_users:
                unique_users.append(rqst.user)

                # If they are banned count add them to the banned users list
                if rqst.user.banned == True and rqst.user not in banned_users:
                    banned_users.append(rqst.user)

                # If the users last_warned_on date is between the request date range then add the to the warned users list
                # Yes, that means that the warned user count metric has time senesitive accuracy
                if rqst.user.last_warned_on != None and rqst.user.last_warned_on.date() >= start_date and rqst.user.last_warned_on.date() <= end_date and rqst.user not in warned_users:
                    warned_users.append(rqst.user)

            for f in files_in_request:
                file_name = f.__str__()
                # Get file extension from the file name, add it to the list of file extensions
                ext = str(file_name.split('.')[-1]).lower()
                file_types.append(ext)

                # Add all files to file count, add combined file size to file size total
                files_reviewed += f.file_count
                file_size += f.file_size

                # Exclude the rejects from the transfers numbers, they are counted separately
                if f.rejection_reason == None:
                    files_transfered += f.file_count

                    # If the file is from a CENTCOM org count it
                    if f.is_centcom == True:
                        centcom_files += f.file_count
                else:
                    files_rejected += f.file_count

                # Count how many files were in zips
                if ext == "zip":
                    file_type_counts['zipContents'] += f.file_count

                # File count by organization
                org = str(f.org)
                if org != "":
                    if org == "CENTCOM HQ":
                        org = "HQ"
                    org_counts[org] += f.file_count

    # Add up all file type counts
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

    # Converting the file size into KB, MB, GB, TB.
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


def process(request):
    """
    Creates a Request object based on POST data, creates File objects for each file in the request, and
    then scans the files for any matches of a DirtyWord object.

    :param request: The request object
    :return: A JsonResponse object
    """

    if request.method == 'POST':
        # Getting the form data and files from the request.
        form_data = request.POST
        form_files = request.FILES

        # This string is used to collect information about a request and generate a request hash that is used to detect duplicate requests submitted to the system
        requestData = ""

        # Use the form data to create the necessary records for the request

        # The network the file was submitted on, pulls from the settings.py file which pulls form the network.py
        sourceNet = Network.objects.get(name=NETWORK)

        # Trying to get an email object from the database. If it doesn't exist, it creates a new one.
        try:
            source_email = Email.objects.get(address=form_data.get('userEmail'), network=sourceNet)
        except Email.DoesNotExist:
            source_email = Email(address=form_data.get('userEmail'), network=sourceNet)
            source_email.save()
        # get() returned more than one Email object, use filter instead and use first object, update Email.network if needed
        except Email.MultipleObjectsReturned:
            source_email = Email.objects.filter(address=form_data.get('userEmail'))[0]

        if source_email.network == None:
            source_email.network = sourceNet
            source_email.save()

        # Add source email to request hash
        requestData += form_data.get('userEmail')

        # Get the destination Network object
        destinationNet = Network.objects.get(name=form_data.get('network'))

        # Users used to be able to transfer to multiple email addresses, the code below should be refactored to assume only one destination email
        destination_list = form_data.get('targetEmail').split(",")
        destSplit_list = []

        target_list = []
        for destination in destination_list:
            # Split emails at the "@", this is used along with the source email and will raise a flag if they do not match. needs to be imporved, causes a lot of false positives
            destSplit_list.append(destination.split("@")[0])

            # Same process as get or create email but for destination instead of source
            try:
                target_email = Email.objects.get(address=destination, network=destinationNet)
            except Email.DoesNotExist:
                target_email = Email(address=destination, network=destinationNet)
                target_email.save()
            except Email.MultipleObjectsReturned:
                target_email = Email.objects.filter(address=destination, network=destinationNet)[0]

            # Add destination email to request hash
            requestData += destination
            target_list.append(target_email)

        # Add first and last name to request hash
        requestData += form_data.get('firstName').replace(" ", "").lower()
        requestData += form_data.get('lastName').replace(" ", "").lower()

        # Importing two functions from auth.py, importing them at the top of the file was causing a circular import error and I was too lazy to fix it...
        from pages.views.auth import getCert, getOrCreateUser

        # Get user cert info, use cert info to return a User object, see auth.py for details
        certInfo = getCert(request)
        cftsUser = getOrCreateUser(request, certInfo)

        # Check to see if a user is banned, if so kick them to the home page
        if cftsUser.banned == True:
            return JsonResponse({'banned': True})

        # Get users organization from request form
        org = form_data.get('organization')
        if form_data.get('organization') == "CENTCOM HQ":
            org = "HQ"

        # Create the initial Request object so that we can start creating object relationships
        rqst = Request(
            user=cftsUser,
            network=destinationNet,
            comments=form_data.get('comments'),
            org=org,
            is_centcom=form_data.get('isCentcom'),
            RHR_email=form_data.get('RHREmail'),
            ready_to_pull=destinationNet.skip_file_review,
        )
        rqst.save()

        # Add destination network to request hash
        requestData += form_data.get('network')

        # Add destination email to request object and raise email mismatch flag if needed
        rqst.target_email.add(*target_list)
        if form_data.get('network') == "NIPR" or form_data.get('network') == "SIPR":
            if form_data.get('userEmail').split("@")[0] not in destSplit_list:
                rqst.destFlag = True

        fileList = []

        # Getting all the staff emails from the database
        staff_emails = [x.lower() for x in authUser.objects.filter(is_staff=True).values_list('email', flat=True)]
        rhr = form_data.get('RHREmail').lower()

        # Checking if the RHR email address in the form is in the staff_emails list, or if it is the same as the
        # source or destination email address. If any of those are true, then it sets the destFlag to True.
        if rhr in staff_emails or rhr == source_email.address.lower() or rhr in [x.lower() for x in destination_list]:
            rqst.destFlag = True

        # Loading the fileInfo from the form_data.
        file_info = json.loads(form_data.get('fileInfo'))

        has_encrypted = False

        # Create a File object for every file in the request
        for i, f in enumerate(form_files.getlist("files")):
            if file_info[i]['encrypt'] == 'true':
                has_encrypted = True

            this_file = File(
                file_object=f,
                is_pii=file_info[i]['encrypt'] == 'true',
                org=form_data.get('organization'),
                is_centcom=form_data.get('isCentcom'),
            )

            # Counting the number of files in a zip file and the total size of the files in the zip file.
            if str(f).split('.')[-1] == "zip":
                with ZipFile(f, 'r') as zip:
                    # Get info for all files
                    info = zip.infolist()
                    fileCount = 0

                    # Only count files, not folders
                    for entry in info:
                        if entry.is_dir() == False:
                            fileCount += 1

                    # Count of all files in zip
                    this_file.file_count = fileCount

                    # Count the total uncompressed file size for all files in the zip
                    fileSize = 0
                    for file in info:
                        fileSize += file.file_size

                    this_file.file_size = fileSize

            else:
                # If its not a zip just get the file size from the file object, file count defaults to 1
                this_file.file_size = this_file.file_object.size

            # Save the file, let Django strip illegal characters from the path, and trim the dir path from the filename
            this_file.save()
            this_file.file_name = str(this_file.file_object.name).split("/")[-1]
            this_file.save()

            # Add the file to the request and the list of files used in the request hash
            rqst.files.add(this_file)
            rqst.has_encrypted = has_encrypted
            fileList.append(str(f))

        # Sort the list of files so the order of files does not affect the duplicate checking
        fileList.sort()

        # Add all filenames to request hash
        for file in fileList:
            requestData += file

        # Create the request hash and add it to the Request object
        requestHash = hashlib.md5()
        requestHash.update(requestData.encode())
        requestHash = requestHash.hexdigest()
        rqst.request_hash = requestHash

        # Check for any files with the same hash that have not been pulled yet
        dupes = Request.objects.filter(pull__date_complete=None, request_hash=requestHash)

        # Updating the is_dupe field to True for all the duplicate records.
        if dupes:
            rqst.is_dupe = True
            dupes.update(is_dupe=True)

        # If we have gotten this far without an error than this request is good to go, Requests where is_submitted == False are filtered out from the queue and pulls
        rqst.is_submitted = True
        rqst.save()

        # Scan all files in request for any match of a DirtyWord object, append results to file, an error in a scan will NOT prevent the request from being submitted
        try:
            scan(request, rqst.request_id)
        except:
            pass

        # We did it!!! The request is submitted, return the request is as part of the response
        resp = {'status': 'success', 'request_id': rqst.pk}

    else:
        resp = {'status': 'fail', 'reason': 'bad-request-type',
                'msg': "The 'api-processrequest' view only accepts POST requests."}

    return JsonResponse(resp)

@never_cache
def setConsentCookie(request):
    """
    The function sets a session cookie called 'consent' with a value of 'consent given' and sets the
    cookie to expire when the browser is closed

    :param request: The request object
    :return: an HttpResponse object.
    """
    request.session.__setitem__('consent', 'consent given')
    request.session.set_expiry(0)
    return HttpResponse("Consent Header Set")
