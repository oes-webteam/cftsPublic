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

# function to serve feedback submission page with optional Request object
def feedback(request, requestid=False):
    resources = ResourceLink.objects.all()

    # get user cert info, get User object
    certInfo = getCert(request)
    cftsUser = getOrCreateUser(request, certInfo)

    # if optional requestid passed in from args include it in the request context
    # requestid is only passed in from a ban request and is used to link to the Request object that warrented a user ban
    if requestid != False:
        rc = {'resources': resources, 'user': cftsUser, 'rqst': Request.objects.get(request_id=requestid)}
    else:
        rc = {'resources': resources, 'user': cftsUser}

    return render(request, 'pages/feedback.html', {'rc': rc})


# function to create Feedback object
def submitFeedback(request):

    # only process data from a POST request
    if request.method == 'POST':
        form_data = request.POST

        # get user cert info, get User object
        certInfo = getCert(request)
        cftsUser = getOrCreateUser(request, certInfo)

        # create Feedback object from POST data
        feedback = Feedback(
            title=form_data.get('title'),
            body=form_data.get('feedback'),
            category=form_data.get('category'),
            admin_feedback=form_data.get('adminUser'),
            date_submitted=timezone.now()
        )

        # if a User object was returned then create a one-to-one realationship between User and Feedback objects
        # submitting feedback does not require a user to be logged in so external users will always return None
        if cftsUser != None:
            feedback.user = cftsUser
        # no User object retruned, format and add user submitted information to the beginning of the body of the Feedback object
        else:
            buggedUserInfo = '''
            First Name: {fname}
            Last Name: {lname}
            Email: {email}
            Phone: {phone}
            Message: {msg}
            '''.format(msg=form_data.get('feedback'), fname=form_data.get('firstName'), lname=form_data.get('lastName'), email=form_data.get('userEmail'), phone=form_data.get('userPhone'))

            feedback.title = form_data.get('lastName') + ", " + form_data.get('firstName')
            feedback.body = buggedUserInfo

            # bugged PKI user, try and return a User object based on Django account username
            try:
                userFromUserName = User.objects.get(auth_user=authUser.objects.get(username=form_data.get('userName')))
                feedback.user = userFromUserName
            # no luck with username
            except (User.DoesNotExist, authUser.DoesNotExist):
                # try their email
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
