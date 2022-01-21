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


def getDestinationNetworks(request, cftsUser):
    networkEmails = {}
    nets = Network.objects.filter(visible=True, network_id__in=cftsUser.destination_emails.values('network_id'))
    for net in nets:
        try:
            networkEmails[net.name] = cftsUser.destination_emails.get(network__name=net.name).address
        except Email.MultipleObjectsReturned:
            duplicateEmails = cftsUser.destination_emails.filter(network__name=net.name)

            for email in duplicateEmails:
                cftsUser.destination_emails.remove(email)
                email.network = None
                email.save()

            cftsUser.save()
            messages.info(request, "An error has occured, please check and re-enter any missing information.")
            return None

    return networkEmails


def consent(request):
    setConsentCookie(request)
    return render(request, 'pages/consent.html')


def checkBan(cftsUser):
    if cftsUser.banned == True and date.today() >= cftsUser.banned_until:
        cftsUser.banned = False
        cftsUser.save()


@ensure_csrf_cookie
@never_cache
def frontend(request):
    browser = request.user_agent.browser.family
    resources = ResourceLink.objects.all()

    # get the consent header, redirect to consent page if not found
    try:
        if browser == "IE":
            rc = {'resources': resources, 'browser': browser}
            return render(request, 'pages/frontend.html', {'rc': rc})

        request.session.__getitem__('consent')
        request.session.set_expiry(0)

        # grab client cert form the request create user hash, ignore if no cert info is found in request
        certInfo = getCert(request)
        cftsUser = getOrCreateUser(request, certInfo)

        if cftsUser == None:
            return redirect("/login")
        elif cftsUser.update_info == True:
            return redirect("/user-info")

        checkBan(cftsUser)

        nets = getDestinationNetworks(request, cftsUser)
        if nets == None:
            return redirect('user-info')
        rc = {'networks': nets, 'submission_disabled': Settings.DISABLE_SUBMISSIONS, 'debug': str(Settings.DEBUG), 'resources': resources, 'user': cftsUser, 'browser': browser}

        return render(request, 'pages/frontend.html', {'rc': rc})

    except KeyError:
        return redirect('consent')


def userRequests(request):
    resources = ResourceLink.objects.all()

    certInfo = getCert(request)
    cftsUser = getOrCreateUser(request, certInfo)
    if cftsUser == None:
        return redirect("/login")
    else:
        requests = Request.objects.filter(user=cftsUser, is_submitted=True)
        requestPage = paginator.Paginator(requests, 8)
        pageNum = request.GET.get('page')
        pageObj = requestPage.get_page(pageNum)

    rc = {'requests': pageObj, 'resources': resources, 'firstName': cftsUser.name_first, 'lastName': cftsUser.name_last}

    return render(request, 'pages/userRequests.html', {'rc': rc})


def requestDetails(request, id):
    resources = ResourceLink.objects.all()
    userRequest = Request.objects.get(request_id=id)

    rc = {'request': userRequest, 'resources': resources, 'firstName': userRequest.user.name_first.split("_buggedPKI")[0], 'lastName': userRequest.user.name_last}

    return render(request, 'pages/requestDetails.html', {'rc': rc})
