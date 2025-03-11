# ====================================================================
# core
import random
from datetime import datetime, timedelta
from django.contrib import messages
from django.templatetags.static import static
from zipfile import ZipFile
from django.utils import timezone
from cfts import settings as cftsSettings
from django.core.mail import EmailMessage

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
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache

from pages.views.auth import superUserCheck, staffCheck

# responses
from django.shortcuts import redirect, render
from django.template.loader import render_to_string

from django.http import JsonResponse, FileResponse, HttpResponse

# model/database stuff
from pages.models import *
from django.db.models import Count, Q
from django.contrib.auth.models import User as authUser


import logging

logger = logging.getLogger('django')

# ====================================================================
# I really don't want to comment this file, there is so much hacky shit going on here

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
@ensure_csrf_cookie
@never_cache
def queue(request):
    """
    It takes a request object, queries the database for all the requests that are not part of a
    completed pull, and then organizes them into a list of dictionaries that are then passed to the
    template

    :param request: The request object that was sent to the view
    :return: The render function is returning a HttpResponse object.
    """
    # Instansiate the list that will contain all of the dictionaries of Request objects per network
    xfer_queues = []

    # Used to determine which network tab on the queue shuold be selected by default
    activeTab = True

    # If else statement used to activate the easter egg on the queue page when the queue is completely empty
    # /queue/cookie will take the user to a cookie card matching game
    if str(request.path) == '/queue/cookie':
        # List of "cards" for the matching game
        cookieList1 = [
            {'name': "Chocolate Chip", 'path': static('img/cookies/cookie.png')},
            {'name': "Dark Chocolate Chip", 'path': static('img/cookies/darkChoc.png')},
            {'name': "Fortune", 'path': static('img/cookies/fortune.png')},
            {'name': "Iced Sugar", 'path': static('img/cookies/icedSugar.png')},
            {'name': "White Chocolate Macadamia Nut", 'path': static('img/cookies/macadamia.png')},
            {'name': "M&M", 'path': static('img/cookies/MnM.png')},
            {'name': "Oreo", 'path': static('img/cookies/oreo.png')},
            {'name': "Red Velvet", 'path': static('img/cookies/redVelvet.png')},
            {'name': "Sugar", 'path': static('img/cookies/sugar.png')},
            {'name': "Thin Mint", 'path': static('img/cookies/thinMint.png')},
        ]

        # Second list of "cards"
        cookieList2 = random.sample(cookieList1, len(cookieList1))

        # Combine and shuffle the cards
        random.shuffle(cookieList1)
        empty = cookieList1+cookieList2

        # Sort the list of network queues into network order
        xfer_queues = sorted(xfer_queues, key=lambda k: k['order_by'], reverse=False)

        # Create the request context
        rc = {'queues': xfer_queues, 'empty': empty, 'easterEgg': activeTab}

        # roll that beautiful bean footage
        # ^-- I've always wondered what he meant by that, never did ask him
        return render(request, 'pages/queue.html', {'rc': rc})

    # Send a message to the empty queue page, kinda like a fortune cookie
    else:
        empty = random.choice([
            'These pipes are clean.',
            'LZ is clear.',
            'Nothing here. Why not work on metadata?',
            'Queue is empty -- just like my wallet.',
            "There's nothing here? Huh. That's gotta be an error ... ",
            "Xander was here.",
            "Is PKI working yet?",
            "It's probably the weekend right?",
            "Shoot a dart at Ron, tell him Xander told you to.",
            "I'll code tetris into this page one day.",
            "Don't let Jason ban everyone, 'cause he'll do it.",
            "Now anyone can be banned, so much power!",
            "A bug? In my code? Impossible.",
            "Deleting database... Just kidding",
            "Slow day?",
            "Pretty cards.",
            "Ban anyone today?",
            "Card games are fun too."
        ])

        # Filter for requests that are not part of a completed pull, and then prefetching related files
        # and target emails. It is also selecting related user. It is then annotating the query with the
        # number of files in the request, the number of files that need review, and the number of files
        # that the user is reviewing. It is then ordering the query by date created.
        ds_requests = Request.objects.filter(is_submitted=True, pull__date_complete__isnull=True).prefetch_related('files', 'target_email').select_related('user').annotate(
            files_in_request=Count('files__file_id'),
            needs_review=Count('files', filter=Q(files__user_oneeye=None) | Q(files__user_twoeye=None) & ~Q(files__user_oneeye=request.user)) -
            Count('files', filter=~Q(files__rejection_reasons=None) & ~Q(files__user_oneeye=request.user) & ~Q(files__user_twoeye=request.user)),
            user_reviewing=Count('files', filter=Q(files__user_oneeye=request.user) & Q(files__date_oneeye=None) & Q(files__rejection_reasons=None)) +
            Count('files', filter=Q(files__user_twoeye=request.user) & Q(files__date_twoeye=None) & Q(files__rejection_reasons=None))).order_by('date_created')

        # Getting all the network_id's from the ds_requests and then filtering the ds_networks based on
        # the network_id's.
        pending_nets = ds_requests.values_list('network', flat=True)
        ds_networks = Network.objects.filter(network_id__in=pending_nets)

        # For every network
        for net in ds_networks:
            # Get information about the last pull that was done on this network
            last_pull = Pull.objects.values(
                'pull_number',
                'date_pulled',
                'user_pulled__username'
            ).filter(network__name=net.name).order_by('-date_pulled')[:1]

            queue = {
                'name': net.name,
                'order_by': net.sort_order,

                'count': 0,
                'file_count': 0,
                'activeNet': activeTab,
                'pending': 0,
                'centcom': 0,
                'other': 0,
                'pullable': 0,
                'hidden_dupes_pullable': 0,
                'hidden_dupes_pulled': 0,
                'pulled': 0,

                # The actual set of Request objects
                'q': [],
                'o': [],
                'a': [],
                'p': [],
                'last_pull': last_pull,
            }

            activeTab = False

            # ... and add it to the list
            xfer_queues.append(queue)

        # Counting the number of requests in each queue group, appending request to the appropreate list.
        for rqst in ds_requests:
            # Iterating through the list of queues and finding the queue that matches the name of the network.
            for queue in xfer_queues:
                if queue['name'] == rqst.network.name:
                    match_queue = queue
                    break

            match_queue['count'] += 1

            if rqst.pull != None:
                match_queue['pulled'] += 1

                if rqst.rejected_dupe == True:
                    match_queue['hidden_dupes_pulled'] += 1
                elif rqst.rejected_dupe == False:
                    match_queue['p'].append(rqst)

            else:
                match_queue['file_count'] += rqst.files_in_request
                match_queue['pending'] += 1

                if rqst.ready_to_pull == True:
                    match_queue['pullable'] += 1

                    if rqst.rejected_dupe == True:
                        match_queue['hidden_dupes_pullable'] += 1
                    elif rqst.rejected_dupe == False:
                        match_queue['a'].append(rqst)

                elif rqst.is_centcom == True:
                    match_queue['centcom'] += 1
                    match_queue['q'].append(rqst)

                elif rqst.is_centcom == False:
                    match_queue['other'] += 1
                    match_queue['o'].append(rqst)

        # Sort the list of network queues into network order
        xfer_queues = sorted(xfer_queues, key=lambda k: k['order_by'], reverse=False)

        # Create the request context
        rc = {'queues': xfer_queues, 'empty': empty, 'easterEgg': not activeTab}

    # roll that beautiful bean footage
    # ^-- I've always wondered what he meant by that, never did ask him
    return render(request, 'pages/queue.html', {'rc': rc})

@login_required
@never_cache
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def transferRequest(request, id):
    """
    It takes a request ID, finds the request, finds any other requests with the same hash, and then
    renders a template with the request and the other requests

    :param request: The request object
    :param id: the request_id of the request to be transferred
    :return: a render object.
    """
    try:
        rqst = Request.objects.get(request_id=id)
    except Request.DoesNotExist:
        messages.warning(request, "Could not find the request you were looking for, it may have been deleted.")
        return redirect('/queue')

    dupes = Request.objects.filter(pull__date_complete=None, request_hash=rqst.request_hash).exclude(request_id=rqst.request_id).order_by('-date_created')

    mostRecentDupe = False

    if dupes.count() > 0:
        if rqst.date_created > dupes[0].date_created:
            mostRecentDupe = True

    ds_rejections = Rejection.objects.filter(visible=True)
    rejections = []

    for row in ds_rejections:
        rejections.append({
            'rejection_id': row.rejection_id,
            'name': row.name,
            'subject': row.subject,
            'text': row.text
        })

    emailFlags = {
        'sourceDestFlag': False,
        'RHRFlag': False,
        'RHRStaffFlag': False,
        'RHRSourceFlag': False,
        'RHRDestFlag': False,
    }

    destSplit = rqst.target_email.all()[0].address.split("@")[0]

    if rqst.destFlag == True:
        if rqst.user.source_email.address.split("@")[0] != destSplit:
            emailFlags['sourceDestFlag'] = True

    # Getting all the staff emails from the database
    staff_emails = [x.lower() for x in authUser.objects.filter(is_staff=True).values_list('email', flat=True)]
    rhr = rqst.RHR_email.lower()

    # Checking if the RHR email address in the form is in the staff_emails list, or if it is the same as the
    # source or destination email address. If any of those are true, then it sets the destFlag to True.

    if rhr == rqst.user.source_email.address.lower():
        emailFlags['RHRSourceFlag'] = True
        emailFlags['RHRFlag'] = True

    if rhr == rqst.target_email.all()[0].address.lower():
        emailFlags['RHRDestFlag'] = True
        emailFlags['RHRFlag'] = True

    if rhr in staff_emails:
        emailFlags['RHRStaffFlag'] = True
        emailFlags['RHRFlag'] = True

    return render(request, 'pages/transfer-request.html', {'rqst': rqst, 'emailFlags': emailFlags, 'dupes': dupes, 'mostRecentDupe': mostRecentDupe, 'rejections': rejections,
                                                           'centcom': rqst.is_centcom, 'notes': rqst.notes, "user_id": rqst.user.user_id, 'debug': cftsSettings.DEBUG})

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def getRejectModal(request, fileID):
    file = File.objects.get(file_id=fileID)
    rejections = Rejection.objects.filter(visible=True)
    return render(request, 'partials/Queue_partials/rejectionModalTemplate.html', {'file': file, 'rejections': rejections})

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def getReviewModal(request, fileID):
    file = File.objects.get(file_id=fileID)
    return render(request, 'partials/Queue_partials/reviewEditModalTemplate.html', {'file': file, })


@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def requestNotes(request, requestid):
    """
    The function takes the notes entered on the request details page, updates the notes field on the
    Request object, and then calls for a pull zip to be rewritten if needed

    :param request: the request object
    :param requestid: the request_id of the request that the notes are being saved to
    :return: The response is a JsonResponse object.
    """
    # Get notes entered from request details page.
    # This will be a combination of any previously entered notes and the most recently entered in note
    postData = dict(request.POST.lists())
    notes = postData['notes'][0]

    # update the notes field on the Request object
    Request.objects.filter(request_id=requestid).update(notes=notes)
    rqst = Request.objects.get(request_id=requestid)
    messages.success(request, "Notes Saved")

    # call for a pull zip to be rewritten, Requests objects with notes will generate a _notes.txt in the pull zip
    try:
        pull_number = rqst.pull.pull_id
        createZip(request, rqst.network.name, pull_number)
    except AttributeError:
        print("Request not found in any pull.")

    return JsonResponse({'response': "Notes saved"})


@login_required
@user_passes_test(staffCheck, login_url='queue', redirect_field_name=None)
def banUser(request, userid, requestid, ignore_strikes=False, perma_ban=False):
    """
    It bans a user based on their strike count, stike count is ignored based on passed in args

    :param request: the request object
    :param userid: the user id of the user to ban
    :param requestid: the id of the transfer request that warrented the ban
    :param ignore_strikes: this will ignore the strike count and just ban them for 1 day if True and perma_ban is False, defaults to False (optional)
    :param perma_ban: will perma ban user if True and ignore_strikes is also True, defaults to False (optional)
    :return: The redirect is returning a string, which is the url to redirect to.
    """

    userToBan = User.objects.filter(user_id=userid)[0]

    strikes = userToBan.strikes

    # Used in the success message
    days = 0

    # Ban a user for 1 day or permanently
    if ignore_strikes == "True":
        if perma_ban == "True":
            User.objects.filter(user_id=userid).update(banned=True, strikes=4, banned_until=datetime.date.today().replace(year=datetime.date.today().year+1000))
        elif userToBan.banned == False and perma_ban == "False":
            User.objects.filter(user_id=userid).update(banned=True, temp_ban_count=F('temp_ban_count') + 1, banned_until=datetime.date.today() + datetime.timedelta(days=1))
            days = 1
        else:
            messages.error(request, "User may have already been banned, check user information below.")
            return redirect('/transfer-request/' + str(requestid))
    # Checking the number of strikes a user has and then banning them for a certain amount of time.
    else:
        # Users first ban, 3 days
        if strikes == 0:
            User.objects.filter(user_id=userid).update(banned=True, strikes=1, banned_until=datetime.date.today() + datetime.timedelta(days=3))
            days = 3
        # Second ban, 7 days
        elif strikes == 1:
            User.objects.filter(user_id=userid).update(banned=True, strikes=2, banned_until=datetime.date.today() + datetime.timedelta(days=7))
            days = 7
        # Third ban, 30 days
        elif strikes == 2:
            User.objects.filter(user_id=userid).update(banned=True, strikes=3, banned_until=datetime.date.today() + datetime.timedelta(days=30))
            days = 30
        # Fourth ban, lifetime... assuming the user isn't alive 1000 years from now. I sure hope I'm not...
        elif strikes == 3:
            User.objects.filter(user_id=userid).update(banned=True, strikes=4, banned_until=datetime.date.today().replace(year=datetime.date.today().year+1000))
        # Just incase any other stike number comes in
        else:
            pass

    if cftsSettings.EMAIL_HOST != '':
        if days == 0:
            messages.success(request, "User banned for a really long time, email sent to user")
        else:
            messages.success(request, "User banned for " + str(days) + " days, email sent to user")
    else:
        if days == 0:
            messages.success(request, "User banned for a really long time")
        else:
            messages.success(request, "User banned for " + str(days) + " days")

    if cftsSettings.DEBUG == True:
        return redirect('/transfer-request/' + str(requestid))
    else:
        # Generate a ban email template, but only when DEBUG == False... for my sanity
        if cftsSettings.EMAIL_HOST != '':
            eml = banEml(request, requestid, ignore_strikes, perma_ban)
            return redirect('/transfer-request/' + str(requestid))
        else:
            eml = banEml(request, requestid, ignore_strikes, perma_ban)
            return redirect('/transfer-request/' + str(requestid) + "?eml=" + eml)


@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def banEml(request, request_id, ignore_strikes, perma_ban):
    """
    It takes in a request object, a request_id, a boolean for ignoring strikes, and a boolean for
    perma_ban. It then gets the request object from the database, and creates a mailto link with the
    user's email address as the recipient, and the subject and body of the email are rendered from a
    template

    :param request: the request object
    :param request_id: The ID of the request that the user is being banned for
    :param ignore_strikes: Will tell the template not to use a users strike count to generate the email body
    :param perma_ban: Will tell the template to generate the perma ban notification for the email body
    :return: The return value is a string that is the body of an email.
    """
    rqst = Request.objects.get(request_id=request_id)
    if cftsSettings.EMAIL_HOST != '':
        msgBody = render_to_string('partials/Queue_partials/banTemplate.html', {'rqst': rqst, 'ignore_strikes': ignore_strikes, 'perma_ban': perma_ban, 'EMAIL_HOST': cftsSettings.EMAIL_HOST,
                                                                                        'EMAIL_CLASSIFICATION': cftsSettings.EMAIL_CLASSIFICATION}, request)

        email = EmailMessage(
            '[' + cftsSettings.EMAIL_CLASSIFICATION + '] CFTS User Account Suspension',
            msgBody,
            "Combined File Transfer Service <" + cftsSettings.EMAIL_FROM_ADDRESS + ">",
            [str(rqst.user.source_email), ],
            reply_to=[cftsSettings.IM_ORGBOX_EMAIL, ],
        )

        email.send(fail_silently=False)

    else:
        msgBody = "mailto:" + str(rqst.user.source_email) + "?subject=[" + cftsSettings.EMAIL_CLASSIFICATION + "] CFTS User Account Suspension&body="
        msgBody += render_to_string('partials/Queue_partials/banTemplate.html', {'rqst': rqst, 'ignore_strikes': ignore_strikes, 'perma_ban': perma_ban, 'EMAIL_HOST': cftsSettings.EMAIL_HOST,
                                                                                        'EMAIL_CLASSIFICATION': cftsSettings.EMAIL_CLASSIFICATION}, request)
    
    return msgBody


@login_required
@user_passes_test(staffCheck, login_url='queue', redirect_field_name=None)
def warnUser(request, userid, requestid, confirmWarn=False):
    """
    If the user has already been warned today, ask for confirmation before issuing a second warning. If
    the user has not been warned today, issue a warning

    :param request: The request object
    :param userid: The user's ID
    :param requestid: The ID of the request that the user is being warned for
    :param confirmWarn: If the user has already been warned today, this will be set to True to confirm
    the second warning, defaults to False (optional)
    :return: The redirect is returning a string.
    """
    userToWarn = User.objects.filter(user_id=userid)

    if userToWarn[0].last_warned_on != None and userToWarn[0].last_warned_on.date() == timezone.now().date() and confirmWarn == False:
        messages.warning(request, "User already warned today. Issue second warning? Click the warning button again to confirm.")

        return redirect('/transfer-request/' + str(requestid) + '?warning=true')
    else:
        userToWarn.update(account_warning_count=userToWarn[0].account_warning_count+1, last_warned_on=timezone.now())

        if cftsSettings.EMAIL_HOST != '':
            messages.success(request, "User warning issued, email sent to user")
        else:
            messages.success(request, "User warning issued")

        if cftsSettings.DEBUG == True:
            return redirect('/transfer-request/' + str(requestid))
        else:
            eml = warningEml(request, userToWarn[0].account_warning_count, userToWarn[0].source_email)
            if cftsSettings.EMAIL_HOST != '':
                return redirect('/transfer-request/' + str(requestid))
            else:
                return redirect('/transfer-request/' + str(requestid) + "?eml=" + eml)


@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def warningEml(request, warningCount, source_email):
    """
    It takes a request, a warning count, and a source email address, and returns a mailto link with the
    source email address as the recipient, a subject line, and a body that contains the warning count
    and a template.

    :param request: the request object
    :param warningCount: The number of warnings the user has received
    :param source_email: the email address of the user who is being warned
    :return: The return value is a string.
    """

    if cftsSettings.EMAIL_HOST != '':
        msgBody = render_to_string('partials/Queue_partials/userWarningTemplate.html', {'warningCount': warningCount, 'EMAIL_HOST': cftsSettings.EMAIL_HOST,
                                                                                        'EMAIL_CLASSIFICATION': cftsSettings.EMAIL_CLASSIFICATION}, request)

        email = EmailMessage(
            '[' + cftsSettings.EMAIL_CLASSIFICATION + '] CFTS User Account Warning',
            msgBody,
            "Combined File Transfer Service <" + cftsSettings.EMAIL_FROM_ADDRESS + ">",
            [str(source_email), ],
            reply_to=[cftsSettings.IM_ORGBOX_EMAIL, ],
        )

        email.send(fail_silently=False)
    else:
        msgBody = "mailto:" + str(source_email) + "?subject=[" + cftsSettings.EMAIL_CLASSIFICATION + "] CFTS User Account Warning&body="
        msgBody += render_to_string('partials/Queue_partials/userWarningTemplate.html', {'warningCount': warningCount, 'EMAIL_HOST': cftsSettings.EMAIL_HOST,
                                                                                        'EMAIL_CLASSIFICATION': cftsSettings.EMAIL_CLASSIFICATION}, request)

    return msgBody


def encryptPhrase(byte_phrase, dest_network):
    keyPath = os.path.join(cftsSettings.KEYS_DIR, dest_network+"_PUB_KEY.pem")
    with open(keyPath, "rb") as dest_pub_pem:
        dest_pub_key = load_pem_public_key(dest_pub_pem.read())
        dest_pub_pem.close()

    return dest_pub_key.encrypt(byte_phrase, padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None))


def encryptFile(salt, nonce, byte_phrase, source_file):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
    key = kdf.derive(byte_phrase)

    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
    encryptor = cipher.encryptor()

    with open(source_file, "rb") as inFile:
        cipherText = encryptor.update(inFile.read()) + encryptor.finalize()
        inFile.close()

    return cipherText


# function to create a zip file containing all pullable File objects for a given network
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def createZip(request, network_name, rejectPull):
    """
    It creates a zip file containing all of the files in a pull

    :param request: the request object
    :param network_name: the name of the network the pull is being created for
    :param rejectPull: this is the pull_id of the pull we are modifying if a pulled file is rejected, if we are creating a new pull then this will be 'false'
    :return: The pullNumber, datePulled, and userPulled are being returned.
    """

    # This variable is a bit misleading, rejectPull is used to determine wheter we are creating a completely new pull or modifying an already existing pull
    # In this case we are creating a new pull
    if rejectPull == 'false':
        # Getting the last pull number for the current network
        try:
            # get the last pull number for the current network
            destNetwork = Network.objects.get(name=network_name)
            maxPull = Pull.objects.filter(network=destNetwork).latest('date_pulled')

            # Reset the pull number everyday
            
            # Kevin: Commented Code below to fix pull_number issues. Need to test on staging.
            # pulled_date = maxPull.date_pulled 
            # tomorrow = datetime.now() + timedelta(days=1)
            # if( tomorrow > pulled_date ):
            if(datetime.now().date() > maxPull.date_pulled.date()):
                pull_number = 1
            else:
                if maxPull.pull_number == None:
                    pull_number = 1
                else:
                    pull_number = maxPull.pull_number + 1

        except Pull.DoesNotExist:
            pull_number = 1

        # Create the Pull object
        new_pull = Pull(
            pull_number=pull_number,
            network=destNetwork,
            date_pulled=timezone.now(),
            user_pulled=request.user,
        )

        # Get all pullable requests for the current network
        qs = Request.objects.filter(
            network__name=network_name, pull=None, ready_to_pull=True, is_submitted=True)
        new_pull.save()

        pull = new_pull

    # We are modifying an already existing pull zip
    else:
        # Get the pull and all its requests
        qs = Request.objects.filter(pull=rejectPull)
        pull = Pull.objects.filter(pull_id=rejectPull)[0]
        pull_number = pull.pull_number

    # Creating a zip file in the PULLS_DIR directory.
    zipPath = os.path.join(cftsSettings.PULLS_DIR+"\\") + network_name + "_" + str(pull_number) + " " + str(pull.date_pulled.astimezone().strftime("%d%b %H%M")) + ".zip"

    zip = ZipFile(zipPath, "w")

    # Zip folder structure looks like this, pull/user/request_#/files
    # List to keep track of which folder paths have been created so we don't overlap
    requestDirs = []

    # Create a zip folder for every Request object
    for rqst in qs:
        zip_folder = str(rqst.user) + "/request_1"
        # Get all non-rejected files in the current request
        theseFiles = rqst.files.filter(rejection_reasons=None)
        # if the is_pii field is True on any of the File objects then encryptRequests will become true
        # Only create a folder for a request if it has non-rejected files, we don't want empty folders because every file got rejected
        if theseFiles.exists():
            # If a user had multiple Request objects in a pull they will all need their own folder, this loop will create the unique request folder for the user
            i = 2
            while zip_folder in requestDirs:
                zip_folder = str(rqst.user) + "/request_" + str(i)
                i += 1

            requestDirs.append(zip_folder)

            if destNetwork.cfts_deployed == True:
                phrase = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(32))
                byte_phrase = str.encode(phrase, 'utf-8')
                crypt_info = {'salt': os.urandom(16),
                              'nonce': os.urandom(16),
                              'encryptedPhrase': encryptPhrase(byte_phrase, rqst.network.name),
                              'email': rqst.target_email.all()[0].address,
                              'user_id': rqst.user.user_identifier}

                rqst_info_file_path = zip_folder + "/_request_info.txt"

                with zip.open(rqst_info_file_path, 'w') as fp:
                    fp.write(str(crypt_info).encode('utf-8'))
                    fp.close()

            elif destNetwork.cfts_deployed == False:
                if rqst.has_encrypted == True:
                    email_file_name = '_encrypt.txt'
                elif rqst.has_encrypted == False:
                    email_file_name = '_email.txt'

                email_file_path = zip_folder + "/" + email_file_name

                # originally a user could submit a request with multiple destination email addresses, that is no longer the case but the target_email field remains a many-to-many field
                # this loop was used to add all of the email addresses to a single file, but now it only ever loops through 1 Email object
                with zip.open(email_file_path, 'w') as fp:
                    emailString = rqst.target_email.all()[0].address

                    fp.write(emailString.encode('utf-8'))
                    fp.close()

            # write all of the File objects to the folder we just created
            for f in theseFiles:
                if destNetwork.cfts_deployed == True:
                    cipherText = encryptFile(crypt_info['salt'], crypt_info['nonce'], byte_phrase, f.file_object.path)
                    encrypt_file_path = zip_folder + "/" + str(f)
                    with zip.open(encrypt_file_path, 'w') as outFile:
                        outFile.write(cipherText)
                        outFile.close()
                else:
                    zip_path = os.path.join(zip_folder, str(f))
                    zip.write(f.file_object.path, zip_path)

            #######################################################################################################################################
            if rqst.notes != "" and rqst.notes != None:

                notes_file_name = zip_folder + "/_notes.txt"

                with zip.open(notes_file_name, 'w') as nfp:
                    notes = rqst.notes
                    nfp.write(notes.encode('utf-8'))
                    nfp.close()

        else:
            print("all files in request rejected")

        # Updating the pull information for the Request and File models if a new pull was created.
        if rejectPull == "false":
            rqst.pull_id = new_pull.pull_id
            rqst.date_pulled = new_pull.date_pulled
            rqst.save()
            files = rqst.files.all()
            files.update(pull=new_pull)

    zip.close()

    if rejectPull == "false":
        messages.success(request, "Pull " + str(new_pull) + " successfully created")
        return JsonResponse({'pullNumber': new_pull.pull_number, 'datePulled': new_pull.date_pulled.strftime("%d%b %H%M").upper(), 'userPulled': str(new_pull.user_pulled)})
    else:
        return JsonResponse({'pullNumber': pull.pull_number, 'datePulled': pull.date_pulled.strftime("%d%b %H%M").upper(), 'userPulled': str(pull.user_pulled)})

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def getFile(request, folder, fileID, fileName):
    """
    It takes a request, a folder, a fileID, and a fileName, and returns a response that contains the
    file

    :param request: The request object
    :param folder: the folder where the file is located, uploads dir or drops dir
    :param fileID: the name of the folder that contains the file, uuid folder
    :param fileName: The name of the file to be downloaded
    :return: A file response object.
    """
    if folder == "uploads" or folder == "drops":
        response = FileResponse(
            open(os.path.join(folder, fileID, fileName), 'rb'))
        return response


@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def updateFileReview(request, fileID, rqstID, completeReview="False", quit="None", skipComplete=False):
    """
    It checks if the user is the first reviewer, if so, it sets the user_oneeye to the current user. If
    the user is the second reviewer, it sets the user_twoeye to the current user

    :param request: The request object
    :param fileID: The ID of the file being reviewed
    :param rqstID: The ID of the request
    :param completeReview: If the user is completing the review, this is set to "True", defaults to
    False (optional)
    :param quit: If the user is quitting the review, this is set to "True", defaults to None (optional)
    :param skipComplete: If True, the function will return a boolean value instead of redirecting to a
    page, defaults to False (optional)
    :return: a redirect to the transfer request page with the appropriate query parameters.
    """

    # Getting the request and file objects from the database.
    rqst = Request.objects.get(request_id=rqstID)
    file = File.objects.get(file_id=fileID)
    open_file = False
    save = True

    # Checking if the user is the first reviewer, if so, it sets the user_oneeye to the current user.
    # If the user is the second reviewer, it sets the user_twoeye to the current user.
    if file.user_oneeye == None and quit != "True":
        file.user_oneeye = request.user
        open_file = True
    elif file.user_oneeye == request.user and file.date_oneeye == None:
        if quit == "True":
            if file.user_twoeye != None:
                file.user_oneeye = file.user_twoeye
                file.date_oneeye = file.date_twoeye
                file.user_twoeye = None
                file.date_twoeye = None
            else:
                file.user_oneeye = None
                file.date_oneeye = None
        elif skipComplete == False and completeReview == "True":
            file.date_oneeye = timezone.now()
    elif file.user_twoeye == None and file.user_oneeye != request.user and quit != "True":
        file.user_twoeye = request.user
        open_file = True
    elif file.user_twoeye == request.user and file.date_twoeye == None:
        if quit == "True":
            file.user_twoeye = None
        elif skipComplete == False and completeReview == "True":
            file.date_twoeye = timezone.now()

    # All review slots are taken, don't make any File changes
    else:
        save = False

    if save == True:
        file.save()

    # Checking if the request is pullable.
    ready_to_pull = checkPullable(rqst)

    # If a File is modified remove the request from the pullable group
    if save == False and ready_to_pull == True and rqst.pull != None:
        rqst.pull = None
        rqst.save()

    # Redirect to the transfer request page with the appropriate query parameters
    if open_file == True and cftsSettings.DEBUG == False:
        return redirect('/transfer-request/' + str(rqstID) + '?file=' + str(fileID))
    elif ready_to_pull == True:
        if skipComplete == True:
            return ready_to_pull
        else:
            messages.success(request, "All files in request have been fully reviewed. Request ready to pull")
            return redirect('/transfer-request/' + str(rqstID) + '?flash=false')
    else:
        return redirect('/transfer-request/' + str(rqstID))


def checkPullable(rqst):
    """
    If all files have a date_twoeye and date_oneeye, then the request is ready to pull.
    A rejected file is considered complete and will not prevent a request from being
    ready to pull.

    :param rqst: the request object
    :return: a boolean value.
    """

    # Checking if the date_twoeye and date_oneeye are not null and if the rejection_reason is null. If
    # any of these conditions are true, it sets ready_to_pull to false.
    ready_to_pull = True
    if rqst.network.skip_file_review == False:
        for file in rqst.files.all():
            if file.date_twoeye == None:
                if not file.rejection_reasons.all():
                    ready_to_pull = False
                    break
            elif file.date_oneeye == None:
                if not file.rejection_reasons.all():
                    ready_to_pull = False
                    break

    if rqst.ready_to_pull != ready_to_pull:
        rqst.ready_to_pull = ready_to_pull
        rqst.save()

    return ready_to_pull


@login_required
@user_passes_test(superUserCheck, login_url='frontend', redirect_field_name=None)
def removeFileReviewer(request, stage):
    """
    It removes a reviewer from a file

    :param request: The request object
    :param stage: 1 or 2, depending on which reviewer you want removed
    :return: The response is being returned as a string.
    """

    # Getting the list of files that are checked in the form.
    post = dict(request.POST.lists())
    rqst = Request.objects.get(request_id=post['rqst_id'][0])

    id_list = post['id_list[]']

    files = File.objects.filter(file_id__in=id_list)

    try:
        # Removing the reviewer from the File object.
        if stage == 1:
            for file in files:
                if file.user_twoeye != None:
                    file.user_oneeye = file.user_twoeye
                    file.date_oneeye = file.date_twoeye
                    file.user_twoeye = None
                    file.date_twoeye = None
                else:
                    file.user_oneeye = None
                    file.date_oneeye = None
                file.save()
            messages.success(request, 'Selected files have had their one eye reviewer removed')
        elif stage == 2:
            files.update(user_twoeye=None, date_twoeye=None)
            messages.success(request, 'Selected files have had their two eye reviewer removed')
    except:
        messages.error(request, 'Good job, you broke it. Something went wrong')

    # Checking if the request is pullable. If it is not, the request is removed from the pull it is a part of.
    if checkPullable(rqst) == False and rqst.pull != None:
        rqst.pull = None
        rqst.save()

    return HttpResponse({'response': 'Selected files have had their ' + str(stage) + ' eye review removed'})