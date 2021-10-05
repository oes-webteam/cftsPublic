# ====================================================================
# core
from email import generator
import random
import datetime
from django.db.models.expressions import When
from django.db.models.fields import IntegerField
import pytz
# from io import BytesIO, StringIO
from zipfile import ZipFile
from django.conf import settings
from django.utils.functional import empty
from django.utils import timezone
from cfts import settings as cftsSettings
from django.core.serializers import serialize


# decorators
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache


# responses
from django.shortcuts import redirect, render
from django.http import JsonResponse, FileResponse, response  # , HttpResponse,

# model/database stuff
from pages.models import *
from django.db.models import Max, Count, Q, Sum
from django.db.models import Case, When

import logging

logger = logging.getLogger('django')
# ====================================================================


@login_required
@ensure_csrf_cookie
@never_cache
def queue(request):
    xfer_queues = []
    ds_networks = Network.objects.all()
    activeSelected = False
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
        "I'll code tetris into this page one day."
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
        ds_requests = Request.objects.filter(
            network__name=net.name,
            is_submitted=True,
            pull__date_complete__isnull=True,
            #files__in=File.objects.filter( rejection_reason__isnull=True )
        ).annotate(org_order = Case(
            When(org='HQ', then=1), 
            When(org='AFCENT', then=2), 
            When(org='ARCENT', then=3), 
            When(org='MARCENT', then=4), 
            When(org='NAVCENT', then=5), 
            When(org='SOCCENT', then=6), 
            When(org='OTHER', then=7), output_field=IntegerField())).order_by('org_order', 'user__str__','-date_created')

        # count how many total files are in all the pending requests (excluding ones that have already been pulled)
        file_count = ds_requests.annotate(
            files_in_request=Count('files__file_id', filter=Q(
                pull__date_pulled__isnull=True))
        ).aggregate(
            files_in_dataset=Sum('files_in_request')
        )

        # smoosh all the info together into one big, beautiful data object ...
        queue = {
            'name': net.name,
            'order_by': net.sort_order,
            'file_count': file_count,
            'count': ds_requests.count(),
            'activeNet': False,
            'pending': ds_requests.aggregate(count=Count('request_id', filter=Q(pull__date_pulled__isnull=True))),
            'q': ds_requests,
            'centcom': ds_requests.aggregate(count=Count('request_id', filter=Q(pull__date_pulled__isnull=True, is_centcom=True))),
            'last_pull': last_pull,
            'orgs': ds_requests.values_list('org',flat=True)
        }

        if activeSelected == False and queue['count'] > 0:
            queue['activeNet'] = True
            activeSelected = True
        
        # ... and add it to the list
        xfer_queues.append(queue)

    # sort the list of network queues into network order
    xfer_queues = sorted(
        xfer_queues, key=lambda k: k['order_by'], reverse=False)

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

    # create the request context
    rc = {'queues': xfer_queues, 'empty': empty, 'rejections': rejections, 'easterEgg': activeSelected}

    # roll that beautiful bean footage
    return render(request, 'pages/queue.html', {'rc': rc})


@login_required
def transferRequest( request, id ):
    rqst = Request.objects.get( request_id = id )
    user = User.objects.get( user_id = rqst.user.user_id )

    rc = { 
        'User Name': user,
        'User Email': user.email,
        'Phone': user.phone,
        'network': Network.objects.get( network_id = rqst.network.network_id ),
        'Marked as Centcom': rqst.is_centcom,
        'Part of pull': rqst.pull,
        'request_id': rqst.request_id,
        'date_created': rqst.date_created,
        'files': rqst.files.all(),
        'target_email': rqst.target_email.all(),
        'is_submitted': rqst.is_submitted,
        'is_centcom': rqst.is_centcom,
        'org': rqst.org,

    }
    return render(request, 'pages/transfer-request.html', {'rc': rc, 'centcom': rqst.is_centcom, 'notes': rqst.notes})

@login_required
def requestNotes( request, requestid ):
  postData = dict(request.POST.lists())
  notes = postData['notes'][0]
  Request.objects.filter(request_id=requestid).update(notes=notes)
  return JsonResponse({'response': "Notes saved"})

@login_required
def removeCentcom( request, id ):
    Request.objects.filter(request_id = id).update(is_centcom=False)
    return redirect('queue')

@login_required
def createZip(request, network_name, isCentcom, rejectPull):
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

        if isCentcom == "True":
            new_pull = Pull(
                pull_number=pull_number,
                network=Network.objects.get(name=network_name),
                #date_pulled=datetime.datetime.now(),
                date_pulled=timezone.now(),
                user_pulled=request.user,
                centcom_pull=True
            )
        else:
            new_pull = Pull(
                pull_number=pull_number,
                network=Network.objects.get(name=network_name),
                #date_pulled=datetime.datetime.now(),
                date_pulled=timezone.now(),
                user_pulled=request.user,
            )

         # select Requests based on network and status
        if(isCentcom == "True"):
            qs = Request.objects.filter(
                network__name=network_name, pull=None, is_centcom=True, is_submitted=True)
            for rqst in qs:
                rqst.centcom_pull = True

        elif(isCentcom == "False"):
            qs = Request.objects.filter(
                network__name=network_name, pull=None, is_submitted=True)
            
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
                    emailString = emailString + this_email.address + ';\n'
                
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

    zip.close()

    # see if we can't provide something more useful to the analysts - maybe the new pull number?
    if rejectPull == "false":
        return JsonResponse({'pullNumber': new_pull.pull_number, 'datePulled': new_pull.date_pulled.strftime("%d%b %H%M").upper(), 'userPulled': str(new_pull.user_pulled)})
    else:
        return JsonResponse({'pullNumber': pull.pull_number, 'datePulled': pull.date_pulled.strftime("%d%b %H%M").upper(), 'userPulled': str(pull.user_pulled)})



@login_required
def getFile(request, fileID, fileName):
  response = FileResponse(
      open(os.path.join("uploads", fileID, fileName), 'rb'))
  return response
