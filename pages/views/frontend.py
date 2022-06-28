# ====================================================================
# core
from datetime import date
from django.conf import Settings
from django.core import paginator
from django.contrib import messages

# crypto
import hashlib
from django import http
from django.db.models import fields
from django.http import request, JsonResponse, HttpResponse
# responses
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.core import serializers

from cfts import settings as Settings
# db/model stuff
from pages.models import *

from pages.views.auth import getCert, getOrCreateUser
from pages.views.apis import setConsentCookie

# ====================================================================

# function to return a dictionary of Network and Email objects from a User objects destination_emails field
# this will only allow a user to select a destination network to transfer to if they have an email saved for that network
def getDestinationNetworks(request, cftsUser):
    networkEmails = {}

    # get all Network objects that appear in a User objects destination_emails field
    nets = Network.objects.filter(visible=True, network_id__in=cftsUser.destination_emails.values('network_id'))
    for net in nets:
        try:
            # add the email address to the dictionary with the network name as the dictionary key
            networkEmails[net.name] = cftsUser.destination_emails.get(network__name=net.name).address

        # get retruned multiple Email objects
        except Email.MultipleObjectsReturned:
            # get all Email objects from destination_emails for the offending network
            duplicateEmails = cftsUser.destination_emails.filter(network__name=net.name)

            for email in duplicateEmails:
                # remove the Email object from destination_emails and set the network field on the Email object to None
                cftsUser.destination_emails.remove(email)
                email.network = None
                email.save()

            cftsUser.save()
            messages.info(request, "An error has occured, please check and re-enter any missing information.")

            # returning None will cause the user to be redirected to update their user information
            return None

    return networkEmails


# function to serve the user consent page
def consent(request):
    setConsentCookie(request)
    return render(request, 'pages/consent.html')


# function to check if a users ban period has passed, will unban the user if needed
def checkBan(cftsUser):
    if cftsUser.banned == True and date.today() >= cftsUser.banned_until:
        cftsUser.banned = False
        cftsUser.save()


# function to serve the main transfer request page
# decorators to validate that the template contains a csrf token, because it was being stripped out of some requests
@ensure_csrf_cookie
@never_cache
def frontend(request):
    # detect what browser a user is visiting from
    browser = request.user_agent.browser.family

    # collect resources to display in resources dropdown in the site nav bar
    resources = ResourceLink.objects.all()
    announcements = Message.objects.filter(visible=True)

    try:
        # if a user is using Internet Explorer server them the template with minimal request context
        # these users will be served a page with the main request form removed and a message shaming them for using IE in {{currentYear}}
        if browser == "IE":
            rc = {'resources': resources, 'browser': browser}
            return render(request, 'pages/frontend.html', {'rc': rc})

        # get consent cookie, redirect to consent page if missing
        request.session.__getitem__('consent')
        request.session.set_expiry(0)

        # get user cert info, get User object
        certInfo = getCert(request)
        cftsUser = getOrCreateUser(request, certInfo)

        # redirect user to login page or info edit page
        if cftsUser == None:
            return redirect("/login")
        elif cftsUser.update_info == True:
            return redirect("/user-info")

        # check if the user is currntly banned
        checkBan(cftsUser)

        # get all networks that a user is able to send to
        nets = getDestinationNetworks(request, cftsUser)

        if nets == None:
            return redirect('user-info')

        rc = {'networks': nets, 'submission_disabled': Settings.DISABLE_SUBMISSIONS, 'debug': str(Settings.DEBUG), 'resources': resources, 'user': cftsUser, 'browser': browser, 'announcements': announcements}

        return render(request, 'pages/frontend.html', {'rc': rc})

    except KeyError:
        return redirect('consent')


# function to serve a page that displays request history for the current user
def userRequests(request):
    resources = ResourceLink.objects.all()

    # get user cert info, get User object
    certInfo = getCert(request)
    cftsUser = getOrCreateUser(request, certInfo)

    # redirect user to login page if needed
    if cftsUser == None:
        return redirect("/login")

    # return all Request objects with a one-to-one relationship to the returned user that have been sucessfully submitted
    # page paginated after 8 Request objects
    else:
        requests = Request.objects.filter(user=cftsUser, is_submitted=True)
        requestPage = paginator.Paginator(requests, 8)
        pageNum = request.GET.get('page')
        pageObj = requestPage.get_page(pageNum)

    rc = {'requests': pageObj, 'resources': resources, 'firstName': cftsUser.name_first, 'lastName': cftsUser.name_last}

    return render(request, 'pages/userRequests.html', {'rc': rc})


# function to give user details about a certain request they submitted
def requestDetails(request, id):
    resources = ResourceLink.objects.all()

    # get the Request object the user clicked on from the request history page
    userRequest = Request.objects.get(request_id=id)

    rc = {'request': userRequest, 'resources': resources, 'firstName': userRequest.user.name_first.split("_buggedPKI")[0], 'lastName': userRequest.user.name_last}

    return render(request, 'pages/requestDetails.html', {'rc': rc})
