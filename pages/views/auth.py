import hashlib
from os import name

from django.shortcuts import render, redirect
import cfts
from cfts import network
from pages.forms import NewUserForm, userInfoForm
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
            #print("I hope you are runing through Django server, or else I screwd up big.")
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
            return redirect("/user-info")
        else:
            return render(request, template_name="authForms/register.html", context={"register_form":form,})

        #messages.error(request, "Error registering account, please check form for errors.")
    form = NewUserForm()
    return render(request, template_name="authForms/register.html", context={"register_form":form})

def editUserInfo(request):
    nets = Network.objects.filter(visible=True)
    certInfo = getCert(request)
    cftsUser = getOrCreateUser(request, certInfo)

    if request.method == "POST":
        form = userInfoForm(request.POST, instance=cftsUser, networks=nets)
        if form.is_valid():
            # update source email address object
            userEmail = Email.objects.get(email_id=cftsUser.source_email.email_id)
            userEmail.address=request.POST.get('source_email')
            userEmail.save()

            # update auth user account info
            userAcc = authUser.objects.get(id=request.user.id)
            userAcc.first_name = request.POST.get('name_first')
            userAcc.last_name = request.POST.get('name_last')
            userAcc.email = request.POST.get('source_email')
            userAcc.save()

            # update cfts user object info
            cftsUser.name_first = request.POST.get('name_first')
            cftsUser.name_last = request.POST.get('name_last')
            cftsUser.source_email = userEmail
            cftsUser.phone = request.POST.get('phone')
            
            # create or update destination emails
            for net in nets:
                formEmail = request.POST.get(str(net.name)+' Email')

                if formEmail != "":
                    try:
                        destinationEmail = cftsUser.destination_emails.get(network__name=net.name)
                        if formEmail != destinationEmail:
                            destinationEmail.address = formEmail
                            destinationEmail.save()

                    except Email.DoesNotExist:
                        destinationEmail = Email(address=formEmail, network=Network.objects.get(name=net.name))
                        destinationEmail.save()
                        cftsUser.destination_emails.add(destinationEmail)

            cftsUser.save()
            return redirect("/frontend")
        else:
            return render(request, 'partials/authForms/editUserInfo.html', context={"userInfoForm": form})

    form = userInfoForm(instance=cftsUser, networks=nets)
    return render(request, 'partials/authForms/editUserInfo.html', context={"userInfoForm": form})