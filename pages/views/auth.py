import hashlib

from django.shortcuts import render, redirect
from pages.forms import NewUserForm
from django.contrib.auth import login
from django.contrib import messages

from django.contrib.auth.models import User as authUser
from pages.models import Network, User, Email

from cfts.settings import NETWORK

def getCert(request):
    buggedPKIs = ['f7d359ebb99a6a8aac39b297745b741b'] #[ acutally bugged hash, my hash for testing]

    try:
        cert = request.META['CERT_SUBJECT']

        # empty cert, IIS is set to ignore certs
        if cert =="":
            return {'status': "empty"}
        
        # got a cert!
        else:
            userHash = hashlib.md5()
            userHash.update(cert.encode())
            userHash = userHash.hexdigest()
            
            if userHash in buggedPKIs:
                return {'status': "buggedPKI", 'cert': cert, 'userHash': userHash}

            # and their cert info isn't bugged!
            else:
                return {'status': "validPKI", 'cert': cert, 'userHash': userHash}

    # django dev server doesn't grab certs
    except KeyError:
        return {'status': "empty"}

def getOrCreateUser(request, certInfo):
    userAcc = authUser.objects.get(id=request.user.id)
    emailNet = Network.objects.get(name=NETWORK)

    try:
        userEmail = Email.objects.get(address=userAcc.email)
        userEmail.network = emailNet

    except Email.DoesNotExist:
        userEmail = Email(address=userAcc.email, network=emailNet)
        userEmail.save()
        

    try:
        userHash = certInfo['userHash']

        user = User.objects.get(user_identifier=userHash)
        return user
        
    except User.DoesNotExist:
        print("No user found with ID")
        user = User(
            auth_user = userAcc,
            name_first=userAcc.first_name,
            name_last=userAcc.last_name,
            user_identifier=certInfo['userHash'],
            source_email = userEmail
        )
        user.save()

        return user

    except KeyError:
        try:
            print("I hope you are runing through Django server, or else I screwd up big.")
            user = User.objects.get(auth_user=userAcc)

            return user

        except User.DoesNotExist:
            print("No user found with ID")
            user = User(
                auth_user = userAcc,
                name_first=userAcc.first_name,
                name_last=userAcc.last_name,
                source_email = userEmail
            )
            user.save()

            return user

def register(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            login(request, user)
            certInfo = getCert(request)
            cftsUser = getOrCreateUser(request, certInfo)
            cftsUser.auth_user = authUser.objects.get(id=request.user.id)
            cftsUser.phone = request.POST.get('phone')
            cftsUser.save()
            #messages.success(request, "Account creation successful!")
            return redirect("/frontend")
        else:
            return render(request, template_name="authForms/register.html", context={"register_form":form,})

        #messages.error(request, "Error registering account, please check form for errors.")
    form = NewUserForm()
    return render(request, template_name="authForms/register.html", context={"register_form":form})