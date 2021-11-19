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
from pages.views.auth import getCert, getOrCreateUser


import hashlib

def feedback( request, requestid=False ):
    resources = ResourceLink.objects.all()

    certInfo = getCert(request)
    cftsUser = getOrCreateUser(request, certInfo)

    if requestid != False:
        rc = {'resources': resources, 'user': cftsUser,'rqst': Request.objects.get(request_id=requestid)}
    else:
        rc = {'resources': resources, 'user': cftsUser}

    return render(request, 'pages/feedback.html', {'rc': rc})

def submitFeedback( request ):
    if request.method == 'POST':
        form_data = request.POST

        certInfo = getCert(request)
        cftsUser = getOrCreateUser(request, certInfo)

        feedback = Feedback(
            title = form_data.get('title'),
            body = form_data.get('feedback'),
            user = cftsUser,
            category = form_data.get('category'),
            admin_feedback = form_data.get('adminUser'),
            date_submitted = timezone.now()
        )
        feedback.save()

        return JsonResponse({'status': "Success"})
    else:
        return JsonResponse({'resp': "This method only accepts POST requests"})
