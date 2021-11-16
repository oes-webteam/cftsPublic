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
# ====================================================================

buggedPKIs = ['f7d359ebb99a6a8aac39b297745b741b'] #[ acutally bugged hash, my hash for testing]

@ensure_csrf_cookie
@never_cache
def frontend(request):
    browser = request.user_agent.browser.family
    nets = Network.objects.filter(visible=True)
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
                    rc = {'networks': nets, 'resources': resources, 'user': cftsUser, 'browser': browser}
                else:
                    return render(request, 'login')
            
            # got a cert!
            else:
                if certInfo['status'] == "buggedPKI":
                    if request.user.is_authenticated:
                        cftsUser = getOrCreateUser(request, certInfo)
                        rc = {'networks': nets, 'resources': resources,
                            'cert': certInfo['cert'], 'userHash': certInfo['userHash'], 'user': cftsUser, 'browser': browser, 'buggedPKI': "true"}
                    else:
                        return render(request, 'login')

                # and their cert info isn't bugged!
                else:
                    cftsUser = getOrCreateUser(request, certInfo)
                    if cftsUser.banned == True:
                        if date.today() >= cftsUser.banned_until:
                            User.objects.filter(user_identifier=certInfo['userHash']).update(banned=False)

                    rc = {'networks': nets, 'resources': resources,
                        'cert': certInfo['cert'], 'userHash': certInfo['userHash'], 'user': cftsUser, 'browser': browser}

        # django dev server doesn't grab certs
        except KeyError:
            if request.user.is_authenticated:
                rc = {'networks': nets, 'resources': resources,'browser': browser,}
            else:
                return render(request, 'login')

        return render(request, 'pages/frontend.html', {'rc': rc})
    
    except KeyError:
        return render(request, 'pages/consent.html')

def getClassifications(request):
    classifications = serializers.serialize('json',Classification.objects.only('abbrev'))
    return HttpResponse(classifications, content_type='application/json')

def userRequests(request):
    resources = ResourceLink.objects.all()

    try:
            cert = request.META['CERT_SUBJECT']
            if cert =="":
                # requests = Request.objects.all()
                # requestPage = paginator.Paginator(requests, 8)
                # pageNum = request.GET.get('page')
                # pageObj = requestPage.get_page(pageNum)

                # rc = {'requests': pageObj,'resources': resources}
                rc = {'resources': resources, 'buggedPKI': "true"}

            else:
                userHash = hashlib.md5()
                userHash.update(cert.encode())
                userHash = userHash.hexdigest()
                
                if userHash in buggedPKIs:
                    rc = {'resources': resources, 'cert': cert, 'userHash': userHash, 'buggedPKI': "true"}
                else:
                    requests = Request.objects.filter( user__user_identifier=userHash )
                    user = User.objects.get(user_identifier=userHash)
                    requestPage = paginator.Paginator(requests, 8)
                    pageNum = request.GET.get('page')
                    pageObj = requestPage.get_page(pageNum)

                    rc = {'requests': pageObj,'resources': resources, 'cert': cert, 'userHash': userHash, 'firstName': user.name_first, 'lastName': user.name_last}
    except KeyError:
        # requests = Request.objects.all()
        # requestPage = paginator.Paginator(requests, 8)
        # pageNum = request.GET.get('page')
        # pageObj = requestPage.get_page(pageNum)

        # rc = {'requests': pageObj,'resources': resources}
        rc = {'resources': resources, 'buggedPKI': "true"}
    return render(request, 'pages/userRequests.html', {'rc': rc})


def requestDetails(request, id):
    resources = ResourceLink.objects.all()
    userRequest = Request.objects.get(request_id=id)

    try:
            cert = request.META['CERT_SUBJECT']
            if cert =="":
                rc = {'resources': resources}

            else:
                userHash = hashlib.md5()
                userHash.update(cert.encode())
                userHash = userHash.hexdigest()

                if userHash in buggedPKIs:
                    rc = {'request': userRequest,'resources': resources, 'firstName': userRequest.user.name_first.split("_buggedPKI")[0], 'lastName': userRequest.user.name_last, 'buggedPKI': "true"}
                else:
                    rc = {'request': userRequest,'resources': resources, 'firstName': userRequest.user.name_first.split("_buggedPKI")[0], 'lastName': userRequest.user.name_last}
    except:
        rc = {'request': userRequest,'resources': resources, 'firstName': userRequest.user.name_first.split("_buggedPKI")[0], 'lastName': userRequest.user.name_last, 'buggedPKI': "true"}


    return render(request, 'pages/requestDetails.html', {'rc': rc})