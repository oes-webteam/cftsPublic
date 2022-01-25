# ====================================================================
# core
from django.conf import settings
from django.contrib import messages

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
from pages.views.auth import getCert, getOrCreateUser
from django.contrib.auth.models import User as authUser


import hashlib


def feedback(request, requestid=False):
    resources = ResourceLink.objects.all()

    certInfo = getCert(request)
    cftsUser = getOrCreateUser(request, certInfo)

    if requestid != False:
        rc = {'resources': resources, 'user': cftsUser, 'rqst': Request.objects.get(request_id=requestid)}
    else:
        rc = {'resources': resources, 'user': cftsUser}

    return render(request, 'pages/feedback.html', {'rc': rc})


def submitFeedback(request):

    if request.method == 'POST':
        form_data = request.POST

        certInfo = getCert(request)
        cftsUser = getOrCreateUser(request, certInfo)

        feedback = Feedback(
            title=form_data.get('title'),
            body=form_data.get('feedback'),
            category=form_data.get('category'),
            admin_feedback=form_data.get('adminUser'),
            date_submitted=timezone.now()
        )

        if cftsUser != None:
            feedback.user = cftsUser

        else:
            buggedUserInfo = '''
            User Name: {uname}
            First Name: {fname}
            Last Name: {lname}
            Email: {email}
            Phone: {phone}

            '''.format(uname=form_data.get('userName'), fname=form_data.get('firstName'), lname=form_data.get('lastName'), email=form_data.get('userEmail'), phone=form_data.get('userPhone'))
            feedback.body = buggedUserInfo + form_data.get('feedback')

            # bugged PKI user, try and return a CFTS userser account based on username
            try:
                userFromUserName = User.objects.get(auth_user=authUser.objects.get(username=form_data.get('userName')))
                feedback.user = userFromUserName
            # no luck with username
            except (User.DoesNotExist, authUser.DoesNotExist):
                # try thier emmail
                try:
                    userFromEmail = User.objects.get(source_email=Email.objects.get(address=form_data.get('userEmail')))
                    feedback.user = userFromEmail
                # still nothing, pass a Null user
                except (User.DoesNotExist, User.MultipleObjectsReturned, Email.DoesNotExist):
                    pass

        feedback.save()

        return JsonResponse({'status': "Success"})
    else:
        return JsonResponse({'resp': "This method only accepts POST requests"})
