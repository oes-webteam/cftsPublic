# ====================================================================
# core
from datetime import date
from django.core import paginator

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
from django.utils import cache

from pages.models import User

# db/model stuff
from pages.models import *

from pages.views.auth import getCert, getOrCreateUser
from pages.views.apis import setConsentCookie

# ====================================================================

def getDestinationNetworks(request, cftsUser):
    networkEmails = {}
    nets = Network.objects.filter(visible=True, network_id__in=cftsUser.destination_emails.values('network_id'))
    for net in nets:
        networkEmails[net.name] = cftsUser.destination_emails.get(network__name=net.name).address
    
    return networkEmails

def consent(request):
    setConsentCookie(request)
    return render(request, 'pages/consent.html')

@ensure_csrf_cookie
@never_cache
def frontend(request):
    browser = request.user_agent.browser.family
    resources = ResourceLink.objects.all()

    # get the consent header, redirect to consent page if not found
    try:
        request.session.__getitem__('consent')
        request.session.set_expiry(0)
        
        # grab client cert form the request create user hash, ignore if no cert info is found in request
        
        try:
            certInfo = getCert(request)
            print(certInfo)

            # empty cert, IIS is set to ignore certs
            if certInfo['status'] == "empty":
                if request.user.is_authenticated:
                    cftsUser = getOrCreateUser(request, certInfo)

                    if cftsUser == None:
                        return redirect("/login")
                    elif cftsUser.update_info == True:
                        return redirect("/user-info")

                    nets = getDestinationNetworks(request, cftsUser)
                    if cftsUser.banned == True:
                        if date.today() >= cftsUser.banned_until:
                            cftsUser.banned=False
                            cftsUser.save()
                    rc = {'networks': nets, 'resources': resources, 'user': cftsUser, 'browser': browser}
                else:
                    return redirect('login')
            
            # got a cert!
            else:
                if certInfo['status'] == "buggedPKI":
                    if request.user.is_authenticated:
                        cftsUser = getOrCreateUser(request, certInfo)

                        if cftsUser == None:
                            return redirect("/login")
                        elif cftsUser.update_info == True:
                            return redirect("/user-info")

                        nets = getDestinationNetworks(request, cftsUser)
                        if cftsUser.banned == True:
                            if date.today() >= cftsUser.banned_until:
                                cftsUser.banned=False
                                cftsUser.save()

                        rc = {'networks': nets, 'resources': resources,
                            'cert': certInfo['cert'], 'userHash': certInfo['userHash'], 'user': cftsUser, 'browser': browser, 'buggedPKI': "true"}
                    else:
                        return redirect('login')

                # and their cert info isn't bugged!
                else:
                    cftsUser = getOrCreateUser(request, certInfo)

                    if cftsUser == None:
                        return redirect("/login")
                    elif cftsUser.update_info == True:
                        return redirect("/user-info")

                    nets = getDestinationNetworks(request, cftsUser)
                    if cftsUser.banned == True:
                        if date.today() >= cftsUser.banned_until:
                            cftsUser.banned=False
                            cftsUser.save()

                    rc = {'networks': nets, 'resources': resources,
                        'cert': certInfo['cert'], 'userHash': certInfo['userHash'], 'user': cftsUser, 'browser': browser}

        # django dev server doesn't grab certs
        except KeyError:
            if request.user.is_authenticated:
                rc = {'networks': nets, 'resources': resources,'browser': browser,}
            else:
                return redirect('login')

        return render(request, 'pages/frontend.html', {'rc': rc})
    
    except KeyError:
        return redirect('consent')

def getClassifications(request):
    classifications = serializers.serialize('json',Classification.objects.only('abbrev'))
    return HttpResponse(classifications, content_type='application/json')

def userRequests(request):
    resources = ResourceLink.objects.all()

    certInfo = getCert(request)
    cftsUser = getOrCreateUser(request, certInfo)
    if cftsUser == None:
        return redirect("/login")
    else:
        requests = Request.objects.filter( user=cftsUser, is_submitted=True )
        requestPage = paginator.Paginator(requests, 8)
        pageNum = request.GET.get('page')
        pageObj = requestPage.get_page(pageNum)

    rc = {'requests': pageObj,'resources': resources, 'firstName': cftsUser.name_first, 'lastName': cftsUser.name_last}
    
    return render(request, 'pages/userRequests.html', {'rc': rc})


def requestDetails(request, id):
    resources = ResourceLink.objects.all()
    userRequest = Request.objects.get(request_id=id)

    rc = {'request': userRequest,'resources': resources, 'firstName': userRequest.user.name_first.split("_buggedPKI")[0], 'lastName': userRequest.user.name_last}

    return render(request, 'pages/requestDetails.html', {'rc': rc})
