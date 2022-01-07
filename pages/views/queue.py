# ====================================================================
# core
from email import generator
import random
import datetime
from django.contrib import messages
from django.db.models.expressions import Subquery, When
from django.db.models.fields import IntegerField
import pytz
from django.templatetags.static import static
# from io import BytesIO, StringIO
from zipfile import ZipFile
from django.conf import settings
from django.utils.functional import empty
from django.utils import timezone
from cfts import settings as cftsSettings
from django.core.serializers import serialize


# decorators
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache

from pages.views.auth import superUserCheck, staffCheck

# responses
from django.shortcuts import redirect, render, reverse
from django.http import JsonResponse, FileResponse, response, HttpResponse

# model/database stuff
from pages.models import *
from django.db.models import Max, Count, Q, Sum
from django.db.models import Case, When

import logging

logger = logging.getLogger('django')
# ====================================================================

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
@ensure_csrf_cookie
@never_cache
def queue(request):
    xfer_queues = []
    ds_networks = Network.objects.all()
    activeSelected = False
    if str(request.path) == '/queue/cookie':
        cookieList1 = [
            {'name': "Chocolate Chip", 'path':static('img/cookies/cookie.png')},
            {'name': "Dark Chocolate Chip", 'path':static('img/cookies/darkChoc.png')},
            {'name': "Fortune", 'path':static('img/cookies/fortune.png')},
            {'name': "Iced Sugar", 'path':static('img/cookies/icedSugar.png')},
            {'name': "White Chocolate Macadamia Nut", 'path':static('img/cookies/macadamia.png')},
            {'name': "M&M", 'path':static('img/cookies/MnM.png')},
            {'name': "Oreo", 'path':static('img/cookies/oreo.png')},
            {'name': "Red Velvet", 'path':static('img/cookies/redVelvet.png')},
            {'name': "Sugar", 'path':static('img/cookies/sugar.png')},
            {'name': "Thin Mint", 'path':static('img/cookies/thinMint.png')},
            ]
        cookieList2 = random.sample(cookieList1, len(cookieList1))
        random.shuffle(cookieList1)
        empty = cookieList1+cookieList2

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

    ########################
    # FOR EACH NETWORK ... #
    ########################
    for net in ds_networks:
        # get information about the last pull that was done on each network
        last_pull = Pull.objects.values(
            'pull_number',
            'date_pulled',
            'user_pulled__username'
        ).filter(network__name=net.name).order_by('-date_pulled')[:1]

        # get all the xfer requests (pending and pulled) submitted for this network
        ds_requests_centcom = Request.objects.filter(
            network__name=net.name,
            is_submitted=True,
            pull__isnull=True,
            ready_to_pull=False,
            is_centcom=True,
        ).annotate(
            needs_review=Count('files', filter=Q(files__user_oneeye=None) | Q(files__user_twoeye=None) & ~Q(files__user_oneeye=request.user))-Count('files', filter=~Q(files__rejection_reason=None) & ~Q(files__user_oneeye=request.user) & ~Q(files__user_twoeye=request.user)), 
            user_reviewing=Count('files', filter=Q(files__user_oneeye=request.user) & Q(files__date_oneeye=None) & Q(files__rejection_reason=None))+Count('files', filter=Q(files__user_twoeye=request.user) & Q(files__date_twoeye=None) & Q(files__rejection_reason=None))).order_by('date_created')

        ds_requests_other = Request.objects.filter(
            network__name=net.name,
            is_submitted=True,
            pull__isnull=True,
            ready_to_pull=False,
            is_centcom=False,
        ).annotate(
            needs_review=Count('files', filter=Q(files__user_oneeye=None) | Q(files__user_twoeye=None) & ~Q(files__user_oneeye=request.user))-Count('files', filter=~Q(files__rejection_reason=None) & ~Q(files__user_oneeye=request.user) & ~Q(files__user_twoeye=request.user)), 
            user_reviewing=Count('files', filter=Q(files__user_oneeye=request.user) & Q(files__date_oneeye=None) & Q(files__rejection_reason=None))+Count('files', filter=Q(files__user_twoeye=request.user) & Q(files__date_twoeye=None) & Q(files__rejection_reason=None))).order_by('date_created')

        pullable_requests = Request.objects.filter(
            network__name=net.name,
            is_submitted=True,
            pull__isnull=True,
            ready_to_pull=True,
            pull__date_complete__isnull=True,
        ).order_by('user__str__')

        pulled_requests = Request.objects.filter(
            network__name=net.name,
            is_submitted=True,
            pull__isnull=False,
            pull__date_complete__isnull=True,
        ).order_by('pull','user__str__')

        # count how many total files are in all the requests requests
        file_count_centcom = ds_requests_centcom.annotate(
            files_in_request=Count('files__file_id')).aggregate(count=Sum('files_in_request'))['count']
        
        if file_count_centcom == None:
            file_count_centcom = 0

        file_count_other = ds_requests_other.annotate(
            files_in_request=Count('files__file_id')).aggregate(count=Sum('files_in_request'))['count']

        if file_count_other == None:
            file_count_other = 0

        file_count_pullable = pullable_requests.annotate(
            files_in_request=Count('files__file_id')).aggregate(count=Sum('files_in_request'))['count']

        hidden_dupes = pullable_requests.filter(all_rejected=True, is_dupe=True, rejected_dupe=True).count()

        if file_count_pullable == None:
            file_count_pullable = 0

        file_count_pulled = pulled_requests.annotate(
            files_in_request=Count('files__file_id')).aggregate(count=Sum('files_in_request'))['count']

        if file_count_pulled == None:
            file_count_pulled = 0

        # smoosh all the info together into one big, beautiful data object ...
        queue = {
            'name': net.name,
            'order_by': net.sort_order,
            'count': ds_requests_centcom.count() + ds_requests_other.count() + pullable_requests.count() + pulled_requests.count(),
            'file_count': file_count_centcom + file_count_other + file_count_pullable,
            'activeNet': False,
            'pending': ds_requests_centcom.count() + ds_requests_other.count() + pullable_requests.count(),
            'centcom': ds_requests_centcom.count(),
            'other': ds_requests_other.count(),
            'pullable': pullable_requests.count(),
            'hidden_dupes': hidden_dupes,
            'pulled': pulled_requests.count(),
            'q': ds_requests_centcom,
            'o': ds_requests_other,
            'a': pullable_requests.filter(rejected_dupe=False),
            'p': pulled_requests,
            'last_pull': last_pull,
            'orgs': ds_requests_centcom.filter(pull__date_pulled__isnull=True).values_list('org', flat=True)
        }

        if activeSelected == False and queue['count'] > 0:
            queue['activeNet'] = True
            activeSelected = True
        
        # ... and add it to the list
        xfer_queues.append(queue)

    # sort the list of network queues into network order
    xfer_queues = sorted(
        xfer_queues, key=lambda k: k['order_by'], reverse=False)

    # create the request context
    rc = {'queues': xfer_queues, 'empty': empty, 'easterEgg': activeSelected}

    # roll that beautiful bean footage
    return render(request, 'pages/queue.html', {'rc': rc})


@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def transferRequest( request, id ):
    rqst = Request.objects.get( request_id = id )
    user = User.objects.get( user_id = rqst.user.user_id )
    dupes = Request.objects.filter(pull__date_complete=None, request_hash=rqst.request_hash).exclude(request_id=rqst.request_id).order_by('-date_created')
    
    mostRecentDupe = False

    if dupes.count() > 0:
        if rqst.date_created > dupes[0].date_created:
            mostRecentDupe = True

    # get list of Rejections for the "Reject Files" button
    ds_rejections = Rejection.objects.filter(visible=True)
    rejections = []
    for row in ds_rejections:
        rejections.append({
            'rejection_id': row.rejection_id,
            'name': row.name,
            'subject': row.subject,
            'text': row.text
        })
        
    rc = { 
        #'User': str(user) + " ("+ str(user.auth_user.username) +")",
        'Date Submitted': rqst.date_created,
        'Email': user.source_email,
        'Phone': user.phone,
        'Network': Network.objects.get( network_id = rqst.network.network_id ),
        'target_email': rqst.target_email.all()[0],
        'org': rqst.org,
    }
    return render(request, 'pages/transfer-request.html', {'rqst': rqst, 'rc':rc, 'dupes': dupes, 'mostRecentDupe': mostRecentDupe, 'rejections': rejections ,'centcom': rqst.is_centcom, 'notes': rqst.notes, "user_id": user.user_id, 'debug': cftsSettings.DEBUG})

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def requestNotes( request, requestid ):
    postData = dict(request.POST.lists())
    notes = postData['notes'][0]
    Request.objects.filter(request_id=requestid).update(notes=notes)
    rqst = Request.objects.get(request_id=requestid)

    try:
        pull_number = rqst.pull.pull_id
        createZip(request, rqst.network.name, rqst.is_centcom, pull_number)
    except AttributeError:
                print("Request not found in any pull.")

    return JsonResponse({'response': "Notes saved"})

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def removeCentcom( request, id ):
    Request.objects.filter(request_id = id).update(is_centcom=False)
    return redirect('queue')

@login_required
@user_passes_test(superUserCheck, login_url='queue', redirect_field_name=None)
def banUser(request, userid, requestid, temp=False):
    userToBan = User.objects.filter(user_id=userid)[0]
    strikes = userToBan.strikes
    
    if temp == "True":
        User.objects.filter(user_id=userid).update(banned=True, banned_until=datetime.date.today() + datetime.timedelta(days=1))
    else:
        # users first ban, 3 days
        if strikes == 0:
            User.objects.filter(user_id=userid).update(banned=True, strikes=1, banned_until=datetime.date.today() + datetime.timedelta(days=3))
        # second ban, 7 days
        elif strikes == 1:
            User.objects.filter(user_id=userid).update(banned=True, strikes=2, banned_until=datetime.date.today() + datetime.timedelta(days=7))
        # third ban, 30 days
        elif strikes == 2:
            User.objects.filter(user_id=userid).update(banned=True, strikes=3, banned_until=datetime.date.today() + datetime.timedelta(days=30))
        # fourth ban, lifetime
        elif strikes == 3:
            User.objects.filter(user_id=userid).update(banned=True, strikes=4, banned_until=datetime.date.today().replace(year=datetime.date.today().year+1000))
        # just incase any other stike number comes in
        else:
            pass
    
    return redirect('transfer-request', requestid)

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def createZip(request, network_name, rejectPull):
    if rejectPull == 'false':
        
        # create pull
        try:
            maxPull = Pull.objects.filter(network=Network.objects.get(name=network_name)).latest('date_pulled')#.aggregate(Max('pull_number'),Max('date_pulled'))
            
            if(datetime.datetime.now().date() > maxPull.date_pulled.date()):
                pull_number = 1
            else:
                pull_number = 1 if maxPull.pull_number == None else maxPull.pull_number + 1
                
        except Pull.DoesNotExist:
            pull_number = 1

        new_pull = Pull(
            pull_number=pull_number,
            network=Network.objects.get(name=network_name),
            #date_pulled=datetime.datetime.now(),
            date_pulled=timezone.now(),
            user_pulled=request.user,
        )

        qs = Request.objects.filter(
            network__name=network_name, pull=None, ready_to_pull=True, is_submitted=True)
        new_pull.save()
        
        pull=new_pull

    else:
        qs = Request.objects.filter(pull=rejectPull)
        pull = Pull.objects.filter(pull_id=rejectPull)[0]
        pull_number = pull.pull_number

    # create/overwrite zip file
    zipPath = os.path.join(cftsSettings.PULLS_DIR+"\\") + network_name + "_" + str(pull_number)+ " " + str(pull.date_pulled.astimezone().strftime("%d%b %H%M")) + ".zip"
    
    zip = ZipFile(zipPath, "w")

    # for each xfer request ...

    requestDirs = []
    for rqst in qs:
        zip_folder = str(rqst.user) + "/request_1"
        theseFiles = rqst.files.filter(rejection_reason=None)
        encryptRequest = False

        if theseFiles.exists():
            i = 2
            while zip_folder in requestDirs:
                zip_folder = str(rqst.user) + "/request_" + str(i)
                i+=1

            requestDirs.append(zip_folder)

            # add their files to the zip in the folder of their name
            for f in theseFiles:
                if f.is_pii == True:
                    encryptRequest = True
                    
                zip_path = os.path.join(zip_folder, str(f))
                zip.write(f.file_object.path, zip_path)

            # create and add the target email file

            if encryptRequest == True:
                email_file_name = '_encrypt.txt'
                
            elif encryptRequest == False:
                email_file_name = '_email.txt'

            notes_file_name = zip_folder + "/_notes.txt"
            
            
            email_file_path = zip_folder + "/" + email_file_name

            if email_file_path in zip.namelist():
                i = 1
                print("txt file exists")
                while True:
                    if encryptRequest == True:
                        email_file_name = "_encrypt"+str(i)+".txt"
                    else:  
                        email_file_name = "_email"+str(i)+".txt"

                    email_file_path = zip_folder + "/" + email_file_name

                    print("Trying " + email_file_name)
                    if email_file_path in zip.namelist():
                        i = i + 1
                    else:
                        break
            
                
            with zip.open(email_file_path, 'w') as fp:
                emailString = ""

                for this_email in rqst.target_email.all():
                    emailString = emailString + this_email.address + '\n'
                
                fp.write(emailString.encode('utf-8'))
                fp.close()

            if rqst.notes != None:
                with zip.open(notes_file_name, 'w') as nfp:
                    notes = rqst.notes
                    print(notes)
                    nfp.write(notes.encode('utf-8'))
                    nfp.close()
            
            
        else:
            print("all files in request rejected")
        # update the record
        if rejectPull == "false":
            rqst.pull_id = new_pull.pull_id
            rqst.date_pulled = new_pull.date_pulled
            rqst.save()
            files = rqst.files.all()
            files.update(pull=new_pull)



    zip.close()

    # see if we can't provide something more useful to the analysts - maybe the new pull number?
    if rejectPull == "false":
        return JsonResponse({'pullNumber': new_pull.pull_number, 'datePulled': new_pull.date_pulled.strftime("%d%b %H%M").upper(), 'userPulled': str(new_pull.user_pulled)})
    else:
        return JsonResponse({'pullNumber': pull.pull_number, 'datePulled': pull.date_pulled.strftime("%d%b %H%M").upper(), 'userPulled': str(pull.user_pulled)})

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def getFile(request, fileID, fileName):
    response = FileResponse(
        open(os.path.join("uploads", fileID, fileName), 'rb'))
    return response

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def updateFileReview(request, fileID, rqstID, quit="None", skipComplete=False):
    rqst = Request.objects.get(request_id=rqstID)
    file = File.objects.get(file_id=fileID)
    open_file = False
    save = True

    if file.user_oneeye == None:
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
        elif skipComplete == False:
            file.date_oneeye = timezone.now()
    elif file.user_twoeye == None:
        file.user_twoeye = request.user
        open_file = True
    elif file.user_twoeye == request.user and file.date_twoeye == None:
        if quit == "True":
            file.user_twoeye = None
        elif skipComplete == False:
            file.date_twoeye = timezone.now()
    else:
        save = False

    if save == True:
        file.save()

    ready_to_pull = checkPullable(rqst)

    if open_file == True and cftsSettings.DEBUG == False:
        return redirect('/transfer-request/' + str(rqstID) + '?' + str(fileID))
    elif ready_to_pull == True:
        return redirect('/transfer-request/' + str(rqstID) + '?false')
    else:
        return redirect('/transfer-request/' + str(rqstID))

def checkPullable(rqst):
    ready_to_pull = True
    for file in rqst.files.all():
        if file.date_twoeye == None:
            if file.rejection_reason == None:
                ready_to_pull = False
                break
        elif file.date_oneeye == None:
            if file.rejection_reason == None:
                ready_to_pull = False
                break
    
    if rqst.ready_to_pull != ready_to_pull:
        rqst.ready_to_pull = ready_to_pull
        rqst.save()
    
    return ready_to_pull

@login_required
@user_passes_test(superUserCheck, login_url='frontend', redirect_field_name=None)
def removeFileReviewer(request, stage):
    post = dict(request.POST.lists())
    rqst = Request.objects.get(request_id=post['rqst_id'][0])

    id_list = post['id_list[]']

    files = File.objects.filter(file_id__in=id_list)

    try:
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

    checkPullable(rqst)

    return HttpResponse({'response': 'Selected files have had their ' + str(stage) + ' eye review removed'})