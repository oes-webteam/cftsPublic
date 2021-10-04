# ====================================================================
# core
from django.conf import settings

# decorators
from django.contrib.auth.decorators import login_required

# responses
from django.shortcuts import render, redirect
# , HttpResponse, FileResponse
from django.http import JsonResponse, HttpResponseRedirect

# timeszone
from django.utils import timezone

# cfts settings
from cfts import settings as Settings
# model/database stuff
from pages.models import *

import hashlib

buggedPKIs = ['f7d359ebb99a6a8aac39b297745b741b']

def feedback( request ):
    resources = ResourceLink.objects.all()

    try:
        cert = request.META['CERT_SUBJECT']
        if cert =="":
            rc = {'resources': resources, }
        else:
            userHash = hashlib.md5()
            userHash.update(cert.encode())
            userHash = userHash.hexdigest()
            
            if userHash in buggedPKIs:
                rc = {'resources': resources,
                    'cert': cert, 'userHash': userHash, 'buggedPKI': "true"}
            else:
                rc = {'resources': resources,
                    'cert': cert, 'userHash': userHash, }
    except KeyError:
        rc = {'resources': resources, }

        return render(request, 'pages/feedback.html', {'rc': rc})

def submitFeedback( request ):
    if request.method == 'POST':
        form_data = request.POST

        # check if email exists in database
        try:
            source_email = Email.objects.get(
                address=form_data.get('userEmail'))
        except Email.DoesNotExist:
            source_email = Email(address=form_data.get('userEmail'))
            source_email.save()

        # PKI user handleing/fall back
        # really needs to be moved to its own api
        # this is a copy paste form the process api
        if form_data.get('userID') == "":
            print("Not able to get user ID, may create duplicate user.")

            user = User(
                name_first=form_data.get('firstName'),
                name_last=form_data.get('lastName'),
                email=source_email,
            )
            user.save()
            
        # Make the check for the bugged PKI hash here
        elif form_data.get('userID') in buggedPKIs:
            print("Bugged user ID hash found")

            user = User(
                name_first=form_data.get('firstName')+ "_buggedPKI",
                name_last=form_data.get('lastName'),
                email=source_email,
            )
            user.save()
            
        else:
            try:
                User.objects.filter(
                    user_identifier=form_data.get('userID')).update(email=source_email)
                    
                user = User.objects.get(
                    user_identifier=form_data.get('userID'))

                print("User already exists")
                print("Updating user email")
                

            except User.DoesNotExist:
                print("No user found with ID")
                user = User(
                    name_first=form_data.get('firstName'),
                    name_last=form_data.get('lastName'),
                    email=source_email,
                    user_identifier=form_data.get('userID')
                )
                
                user.save() 

        feedback = Feedback(
            title = form_data.get('title'),
            body = form_data.get('feedback'),
            user = user,
            category = form_data.get('category'),
            admin_feedback = form_data.get('adminUser'),
            date_submitted = timezone.now()
        )
        feedback.save()

        return JsonResponse({'status': "Success"})
    else:
        return JsonResponse({'resp': "This method only accepts POST requests"})