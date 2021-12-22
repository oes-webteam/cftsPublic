import email
import hashlib
from os import name
from re import T
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import check_password
from django.forms.widgets import MultipleHiddenInput

from django.shortcuts import render, redirect
from django.http.response import HttpResponse

from pages.forms import NewUserForm, userInfoForm, userLogInForm, userPasswordChangeForm, UsernameLookupForm
from django.contrib.auth.forms import PasswordResetForm
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes

from django.contrib.auth import login, authenticate
from django.contrib import messages

from django.contrib.auth.models import User as authUser
from pages.models import Feedback, Network, User, Email, Feedback, ResourceLink
from cfts.settings import NETWORK

def superUserCheck(user):
    return user.is_superuser

def staffCheck(user):
    return user.is_staff

def getCert(request):
    buggedPKIs = ['2ab155e3a751644ee4073972fc4534be158aa0891e8a8df6cd1631f56c61f06073d288fed905d0932fde78155c83208deb661361e64eb1a0f3d736ed04a7e4dc']#,'85582ff68bd0225a7bf8a7b150b547e3eac6c987c0c616d6411c6ac8c31bba0c09b330c220c51080fca2cd54c893a4a3fb256b81e8845490c6a0f9caf93984eb'] #[ acutally bugged hash, my hash for testing]

    try:
        cert = request.META['CERT_SUBJECT']

        # empty cert, IIS is set to ignore certs
        if cert =="":
            return {'status': "empty"}
        
        # got a cert!
        else:
            md5Hash = hashlib.md5()
            md5Hash.update(cert.encode())
            md5Hash = md5Hash.hexdigest()

            sha512Hash = hashlib.sha512()
            sha512Hash.update(md5Hash.encode())
            userHash = sha512Hash.hexdigest()
            
            
            if userHash in buggedPKIs:
                return {'status': "buggedPKI", 'cert': cert, 'userHash': userHash}

            # and their cert info isn't bugged!
            else:
                return {'status': "validPKI", 'cert': cert, 'userHash': userHash}

    # django dev server doesn't grab certs
    except KeyError:
        return {'status': "empty"}
        # below lines are for testing PKI with django
        #return {'status': "buggedPKI", 'cert': "test.tester2.12345", 'userHash': "2ab155e3a751644ee4073972fc4534be158aa0891e8a8df6cd1631f56c61f06073d288fed905d0932fde78155c83208deb661361e64eb1a0f3d736ed04a7e4dc"}
        #return {'status': "validPKI", 'cert': "", 'userHash': "2ab155e3a751644ee4073972fc4534be158aa0891e8a8df6cd1631f56c61f06073d288fed905d0932fde78155c83208deb661361e64eb1a0f3d736ed04a7e4dc"}

def getOrCreateEmail(request, address, network):
    emailNet = Network.objects.get(name=network)

    # try to get email bassed on both address and network first
    try:
        userEmail = Email.objects.get(address=address, network=emailNet)
        if userEmail.network != emailNet:
            userEmail.network = emailNet
            userEmail.save()

    # no match, try just address and update the network if found
    except Email.DoesNotExist:
        try:
            userEmail = Email.objects.get(address=address)
            if userEmail.network != emailNet:
                userEmail.network = emailNet
                userEmail.save()

        # still nothing, create the email
        except Email.DoesNotExist:
            userEmail = Email(address=address, network=emailNet)
            userEmail.save()
        
        # oops, got multiple results, grab the first
        except Email.MultipleObjectsReturned:
            userEmail = Email.objects.filter(address=address)[0]
            if userEmail.network != emailNet:
                userEmail.network = emailNet
                userEmail.save()

    # oops, got multiple results, grab the first
    except Email.MultipleObjectsReturned:
        userEmail = Email.objects.filter(address=address, network=emailNet)[0]
    
    return userEmail


def getOrCreateUser(request, certInfo):
    try:
        if certInfo['status'] == "validPKI":
            userHash = certInfo['userHash']

            user = User.objects.get(user_identifier=userHash)

            if user.auth_user == None:
                if request.user.is_authenticated:
                    user.auth_user = request.user
                    user.save()
                else:
                    return None
        else:
            if request.user.is_authenticated:
                user = User.objects.get(auth_user=request.user)
            else:
                return None
        
    except User.DoesNotExist:
        print("No user found with ID")
        if request.user.is_authenticated:
            userEmail = getOrCreateEmail(request, request.user.email, NETWORK)
            user = User(
                auth_user = request.user,
                name_first=request.user.first_name,
                name_last=request.user.last_name,
                source_email = userEmail
            )

            if certInfo['status'] == "validPKI":
                user.user_identifier=certInfo['userHash']

            user.save()
        else:
            return None

    except KeyError:
        try:
            #print("I hope you are runing through Django server, or else I screwd up big.")
            user = User.objects.get(auth_user=request.user)

        except User.DoesNotExist:
            print("No user found with ID")
            if request.user.is_authenticated:
                userEmail = getOrCreateEmail(request, request.user.email, NETWORK)
                user = User(
                    auth_user = request.user,
                    name_first=request.user.first_name,
                    name_last=request.user.last_name,
                    source_email = userEmail
                )
                user.save()

            else:
                return None

    return user

def userLogin(request):
    resources = ResourceLink.objects.all()

    if request.method == "POST":
        form = userLogInForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                #messages.success(request, "Login successful!")
                login(request, user)

                nextUrl = request.GET.get('next', None)
                if nextUrl == None:
                    return redirect("/frontend")
                else:
                    return redirect(nextUrl)
            else:
                return render(request, template_name="authForms/userLogin.html", context={'resources': resources, "login_form":form,})
            
        else:
            return render(request, template_name="authForms/userLogin.html", context={'resources': resources, "login_form":form,})

    form = userLogInForm()
    return render(request, template_name="authForms/userLogin.html", context={'resources': resources, "login_form":form})

@login_required
def changeUserPassword(request):
    resources = ResourceLink.objects.all()

    if request.method == "POST":
        form = userPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            login(request, request.user)
            from pages.views.apis import setConsentCookie
            setConsentCookie(request)

            return redirect("/frontend")
            
        else:
            return render(request, template_name="authForms/userPassChange.html", context={'resources': resources, "pass_change_form":form,})

    form = userPasswordChangeForm(request.user)
    return render(request, template_name="authForms/userPassChange.html", context={'resources': resources, "pass_change_form":form})

def register(request):
    resources = ResourceLink.objects.all()

    if request.method == "POST":
        form = NewUserForm(request.POST)
        certInfo = getCert(request)
        form.check_duplicate(request.POST, certInfo)
        if form.is_valid():
            user = form.save()
            login(request, user)
            cftsUser = getOrCreateUser(request, certInfo)
            cftsUser.auth_user = authUser.objects.get(id=request.user.id)
            cftsUser.phone = request.POST.get('phone')
            cftsUser.save()
            #messages.success(request, "Account creation successful!")
            from pages.views.apis import setConsentCookie
            setConsentCookie(request)

            return redirect("/user-info")
        else:
            return render(request, template_name="authForms/register.html", context={'resources': resources, "register_form":form,})

    form = NewUserForm()
    return render(request, template_name="authForms/register.html", context={'resources': resources, "register_form":form})

@login_required
def editUserInfo(request):
    resources = ResourceLink.objects.all()

    nets = Network.objects.filter(visible=True)
    certInfo = getCert(request)
    cftsUser = getOrCreateUser(request, certInfo)

    if request.method == "POST":
        form = userInfoForm(request.POST, instance=cftsUser, networks=nets)
        form.validate_form(request.POST)
        if form.is_valid():
            # update source email address object
            userEmail = getOrCreateEmail(request, request.POST.get('source_email'), NETWORK)

            # update auth user account info
            request.user.first_name = request.POST.get('name_first')
            request.user.last_name = request.POST.get('name_last')
            request.user.email = userEmail.address
            request.user.save()

            # update cfts user object info
            cftsUser.name_first = request.POST.get('name_first')
            cftsUser.name_last = request.POST.get('name_last')
            cftsUser.source_email = userEmail
            cftsUser.phone = request.POST.get('phone')
            cftsUser.org = request.POST.get('org')
            if request.POST.get('org') == "OTHER":
                cftsUser.other_org = request.POST.get('other_org')
            else:
                cftsUser.other_org = None
            cftsUser.update_info = False
            
            # create or update destination emails
            for net in nets:
                formEmail = request.POST.get(str(net.name)+' Email')

                if formEmail != "":
                    # try and get destination email by network
                    try:
                        destinationEmail = cftsUser.destination_emails.get(network__name=net.name)

                        # if the destination email has changed remove old email object from user and add the new email object
                        if formEmail != destinationEmail:
                            cftsUser.destination_emails.remove(destinationEmail)
                            cftsUser.destination_emails.add(getOrCreateEmail(request, formEmail, net.name))

                    # user had multiple destination emails for the same network, shouldn't happen but just in case remove them all
                    except Email.MultipleObjectsReturned:
                        print("multiple records")
                        destinationEmails = cftsUser.destination_emails.filter(network__name=net.name)
                        for email in destinationEmails:
                            cftsUser.destination_emails.remove(email)

                        cftsUser.destination_emails.add(getOrCreateEmail(request, formEmail, net.name))

                    # user has no email for this destination, cerate it, add it
                    except Email.DoesNotExist:
                        cftsUser.destination_emails.add(getOrCreateEmail(request, formEmail, net.name))

            cftsUser.save()
            
            return redirect("/frontend")
        else:
            messages.error(request, "Required fields missing")
            return render(request, 'authForms/editUserInfo.html', context={'resources': resources, "userInfoForm": form})

    form = userInfoForm(instance=cftsUser, networks=nets)
    return render(request, 'authForms/editUserInfo.html', context={'resources': resources, "userInfoForm": form})

@login_required
@user_passes_test(superUserCheck, login_url='frontend', redirect_field_name=None)
def passwordResetAdmin(request):
    resetRequests = Feedback.objects.filter(category="Password Reset").order_by('completed','-date_submitted')
    return render(request, "pages/passwordResetAdmin.html", context={'resetRequests': resetRequests})

def passwordResetRequest(request):
    resources = ResourceLink.objects.all()

    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            formEmail = form.cleaned_data['email']
            userMatchingEmail = authUser.objects.filter(email=formEmail)
            if userMatchingEmail.exists():
                for user in userMatchingEmail:
                    cftsUser = User.objects.get(auth_user=user)
                    passwordResetFeedback = Feedback(title="Password reset: " + str(user.last_name) + ", " + str(user.first_name) + "(" + str(user.username) + ")", user=cftsUser, category="Password Reset")
                    passwordResetFeedback.save()
            
            return redirect('/password-reset/done')
        else:
            return render(request, template_name="authForms/passwordResetForms/passwordReset.html", context={'resources': resources, "password_reset_form":form, "envNet":NETWORK})

    form = PasswordResetForm()
    return render(request, template_name="authForms/passwordResetForms/passwordReset.html", context={'resources': resources, "password_reset_form":form, "envNet":NETWORK})

@login_required
@user_passes_test(superUserCheck, login_url='frontend', redirect_field_name=None)
def passwordResetEmail(request, id, feedback):
    auth_user = authUser.objects.get(id=id)
    passwordResetFeedback = Feedback.objects.get(feedback_id=feedback)
    rc ={
        'user': auth_user,
        'email': auth_user.email,
        'uid': urlsafe_base64_encode(force_bytes(auth_user.pk)),
        'token': default_token_generator.make_token(auth_user),
        'urlPrefix': "https://"+str(request.get_host())
    }

    msgBody = "mailto:" + str(auth_user.email) + "?subject=CFTS Password Reset&body="
    
    msgBody += render_to_string('authForms/passwordResetForms/passwordResetEmail.html', rc, request)

    print(msgBody)

    passwordResetFeedback.completed = True
    passwordResetFeedback.save()

    return HttpResponse(str(msgBody))

def usernameLookup(request):
    resources = ResourceLink.objects.all()

    if request.method == "POST":
        form = UsernameLookupForm(request.POST)

        if form.is_valid():
            formEmail = form.cleaned_data['email']
            userMatchingEmail = authUser.objects.filter(email=formEmail)

            if userMatchingEmail.exists:
                for user in userMatchingEmail:
                    if check_password(form.cleaned_data['password'], user.password):
                        messages.success(request, "Username: " + user.username)
                        return render(request, template_name="authForms/usernameLookup.html", context={'resources': resources, "UsernameLookupForm": UsernameLookupForm})        

                # password failed for all filtered users
                messages.error(request, "No user found for that email address or incorrect password")
                return render(request, "authForms/usernameLookup.html", context={'resources': resources, "UsernameLookupForm": UsernameLookupForm})

            # no user with that email
            else:
                messages.error(request, "No user found for that email address or incorrect password")
                return render(request, "authForms/usernameLookup.html", context={'resources': resources, "UsernameLookupForm": UsernameLookupForm})
    # GET request
    else:
        return render(request, "authForms/usernameLookup.html", context={'resources': resources, "UsernameLookupForm": UsernameLookupForm})
