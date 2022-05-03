import hashlib
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import paginator
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
import logging

logger = logging.getLogger('django')

# used with the @user_passes_test decorator to restict access to certain functions to only superusers
def superUserCheck(user):
    return user.is_superuser

# userd with the @user_passes_test to restrict access to certain function to only staff users
def staffCheck(user):
    return user.is_staff

def hashCert(cert):
    # create hash of cert, this was originally only an MD5 hash and has since been wrapped with SHA512
    md5Hash = hashlib.md5()
    md5Hash.update(cert.encode())
    md5Hash = md5Hash.hexdigest()

    # create a SHA512 hash of the MD5 hash
    sha512Hash = hashlib.sha512()
    sha512Hash.update(md5Hash.encode())
    userHash = sha512Hash.hexdigest()
    return userHash

# function to get certificate information from a user
def getCert(request):
    # this is the certificate hash that all external users will have until F5 can resolve the certificate rewrite issue
    # for more details on this see apis.py
    buggedPKIs = ['2ab155e3a751644ee4073972fc4534be158aa0891e8a8df6cd1631f56c61f06073d288fed905d0932fde78155c83208deb661361e64eb1a0f3d736ed04a7e4dc']

    # get the HTTP CERT_SUBJECT header
    try:
        cert = request.META['HTTP_SUBJECT']

        # empty cert, IIS is set to ignore certs, IIS NEEDS TO REQURE CERTS IN PRODUCTION!!!
        if cert == "":
            return {'status': "empty"}
        else:
            userHash = hashCert(cert)
            if userHash in buggedPKIs:
                return {'status': "buggedPKI", 'cert': cert, 'userHash': userHash}
            else:
                return {'status': "externalPKI", 'cert': cert, 'userHash': userHash}

    # django dev server doesn't grab certs
    except KeyError:
        try:
            cert = request.META['CERT_SUBJECT']
            # empty cert, IIS is set to ignore certs, IIS NEEDS TO REQURE CERTS IN PRODUCTION!!!
            if cert == "":
                return {'status': "empty"}
            # got a cert!
            else:
                userHash = hashCert(cert)
                if userHash not in buggedPKIs:
                    return {'status': "validPKI", 'cert': cert, 'userHash': userHash}
                else:
                    return {'status': "buggedPKI", 'cert': cert, 'userHash': userHash}

        except KeyError:
            return {'status': "empty"}

# function to retrive or create a single Email record
def getOrCreateEmail(request, address, network):
    # retieve Network object based on passed in args
    emailNet = Network.objects.get(name=network)

    # try to get email bassed on both address and network first
    try:
        userEmail = Email.objects.get(address=address, network=emailNet)
        # just incase, if the Email object's network field does not match the Network object we retrieved then rewrite it
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

        # oops, get returned multiple objects, use filter instead and grab the first object
        except Email.MultipleObjectsReturned:
            userEmail = Email.objects.filter(address=address)[0]
            if userEmail.network != emailNet:
                userEmail.network = emailNet
                userEmail.save()

        # still nothing, create the email
        except Email.DoesNotExist:
            userEmail = Email(address=address, network=emailNet)
            userEmail.save()

    # oops, get returned multiple objects, use filter instead and grab the first object
    except Email.MultipleObjectsReturned:
        userEmail = Email.objects.filter(address=address, network=emailNet)[0]

    return userEmail

# function to retrive or create a single User record, this function will always need the result from getCert() passed in
def getOrCreateUser(request, certInfo):
    # try and retrive a User record
    try:
        # validPKI users do not need to be logged in so long as they have a pre-existing User reccord
        if certInfo['status'] == "validPKI" or certInfo['status'] == "externalPKI":
            userHash = certInfo['userHash']

            # get the User object that matches the certificate hash
            try:
                user = User.objects.get(user_identifier=userHash)
            except User.DoesNotExist:
                if request.user.is_authenticated:
                    user = User.objects.get(auth_user=request.user)
                    if user.user_identifier == None:
                        user.user_identifier = userHash
                        user.save()
                else:
                    return None

            # User object retruned, but they do not have a Django user account linked
            if user.auth_user == None:
                # if they are logged in then create a one-to-one relationship between the returned User object and the currently logged in Django user account
                if request.user.is_authenticated:
                    user.auth_user = request.user
                    user.save()

                # if they aren't logged in return None, this will redirect the user to the log in page
                else:
                    return None
        # the user is external, so we can't user a certificate hash to retrieve a User object, external users MUST BE LOGGED IN
        else:
            # if they are logged in then get the User object that has a one-to-one relationship with the currently logged in Django user account
            if request.user.is_authenticated:
                user = User.objects.get(auth_user=request.user)

            # otherwise boot them to the log in page
            else:
                return None

    # could not retireve any User object, one will need to be created, the user MUST BE LOGGED IN
    except User.DoesNotExist:
        if request.user.is_authenticated:
            # call getOrCreateEmail() pass in the email from the currently logged in Django user account and the NETWORK value defined in network.py
            # the retured Email object will be used as the Users source_email value
            userEmail = getOrCreateEmail(request, request.user.email, NETWORK)
            user = User(
                auth_user=request.user,
                name_first=request.user.first_name,
                name_last=request.user.last_name,
                source_email=userEmail
            )

            # if they have valid cert information then add their cert hash to the User object
            if certInfo['status'] == "validPKI":
                user.user_identifier = certInfo['userHash']

            user.save()

        # user was not logged in, redirect them
        else:
            return None

    return user

# function to log a user in, all references to "user" in this function are refering to the Django user account
def userLogin(request):
    resources = ResourceLink.objects.all()

    # only process data from a POST request
    if request.method == "POST":
        # instantiate a login form with data from the POST request
        form = userLogInForm(data=request.POST)

        # proceed if form passes initial validity check
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']

            # attempt to authenticate a user with matching username and password, password is automaticlly hashed by the authenticate() function
            user = authenticate(request, username=username, password=password)

            # authenticate() will return a single User object where User.username and User.password match the data from the POST request
            if user is not None:
                # log the user in
                login(request, user)
                messages.success(request, "Login successful")

                # if they were redirected to the login page send them back to the page they came from, otherwise send them to the front page
                nextUrl = request.GET.get('next', None)
                if nextUrl == None:
                    return redirect("/frontend")
                else:
                    return redirect(nextUrl)

            # authenticate() returned no User object, serve the instantiated form back to the user, it will contain helpful error messages for them
            else:
                return render(request, template_name="authForms/userLogin.html", context={'resources': resources, "login_form": form, })

        # validity check failed, serve the instantiated form back to the user, it will contain helpful error messages for them
        else:
            return render(request, template_name="authForms/userLogin.html", context={'resources': resources, "login_form": form, })

    # all GET requests should be served a blank form
    form = userLogInForm()
    return render(request, template_name="authForms/userLogin.html", context={'resources': resources, "login_form": form})

# function for users to change their account password, users MUST BE LOGGED IN
@login_required
def changeUserPassword(request):
    resources = ResourceLink.objects.all()

    # only process data from a POST request
    if request.method == "POST":
        # instantiate a change password form with data from the POST request and the currently logged in user
        form = userPasswordChangeForm(request.user, request.POST)

        # proceed if form passes initial validity check
        if form.is_valid():
            # save is a method of the userPasswordChangeForm class that will save the password changes to the currently logged in user
            form.save()

            # changing a users password automatically logs them out and I get the reasoning beind it, but I just log them back in anyways
            login(request, request.user)
            messages.success(request, "Password changed successfully")

            # changes to the Django user account create a new session
            # need to reset the consent cookie or the user will be redirected back to the consent page even if they already consented
            from pages.views.apis import setConsentCookie
            setConsentCookie(request)

            return redirect("/frontend")

        # validity check failed, serve the instantiated form back to the user, it will contain helpful error messages for them
        else:
            return render(request, template_name="authForms/userPassChange.html", context={'resources': resources, "pass_change_form": form, })

    # all GET requests should be served a blank form
    form = userPasswordChangeForm(request.user)
    return render(request, template_name="authForms/userPassChange.html", context={'resources': resources, "pass_change_form": form})

# function to create Django user account and create one-to-one relationship with new or existing CFTS User object
def register(request):
    resources = ResourceLink.objects.all()

    # only process data from a POST request
    if request.method == "POST":
        # instantiate a register form with data from the POST request
        form = NewUserForm(request.POST)
        # get user certificate information
        certInfo = getCert(request)
        # validate that a user is not attempting to create a duplicate/second account, failed validation will serve the instantiated form back to the user, it will contain helpful error messages for them
        form.check_duplicate(request.POST, certInfo)
        # proceed if form passes duplicate check and form validity check
        if form.is_valid():
            # save is a method of the NewUserForm class that will create a Django user account based on the POST data, immediately log the user in
            user = form.save()
            login(request, user)

            # call getOrCreateUser() passing in user certificate info, this will usally create a user since this is the user registration form
            cftsUser = getOrCreateUser(request, certInfo)

            # create one-to-one relationship between the newly created Django user account and CFTS User object
            cftsUser.auth_user = authUser.objects.get(id=request.user.id)
            cftsUser.phone = request.POST.get('phone')
            cftsUser.save()
            messages.success(request, "Account creation successful, please enter required account information")

            # need to reset the consent cookie or the user will be redirected back to the consent page even if they already consented
            from pages.views.apis import setConsentCookie
            setConsentCookie(request)

            # redirect the user to the account info edit page to complete their registration
            return redirect("/user-info")

        # validity check failed, serve the instantiated form back to the user, it will contain helpful error messages for them
        else:
            return render(request, template_name="authForms/register.html", context={'resources': resources, "register_form": form, })

    # all GET requests should be served a blank form
    form = NewUserForm()
    return render(request, template_name="authForms/register.html", context={'resources': resources, "register_form": form})


# function for user to update certain information about their account
@login_required
def editUserInfo(request):
    resources = ResourceLink.objects.all()

    # retrieve all Network objects where visible == True, visible == False is for decomissioned networks and the network defined in network.py
    # these networks are used for dynamically creating the destination email fields
    nets = Network.objects.filter(visible=True)

    # get user cert info and retrieve a user record
    certInfo = getCert(request)
    cftsUser = getOrCreateUser(request, certInfo)

    # only process data from a POST request
    if request.method == "POST":

        # instantiate a user info form with data from the POST request
        form = userInfoForm(request.POST, instance=cftsUser, networks=nets)

        # validste_form() is a method of the userInfoForm class that validates none of the destination emails are the same as the users source_email
        # it also validates that if the 'org' field is set to "Other" that they have filled in the field that describes their organization
        form.validate_form(request.POST)

        # proceed if form passes validity checks
        if form.is_valid():
            # update source email address object
            userEmail = getOrCreateEmail(request, request.POST.get('source_email'), NETWORK)

            # update Django user account info
            request.user.first_name = request.POST.get('name_first')
            request.user.last_name = request.POST.get('name_last')
            request.user.email = userEmail.address
            request.user.save()

            # update cfts User object info
            cftsUser.name_first = request.POST.get('name_first')
            cftsUser.name_last = request.POST.get('name_last')
            cftsUser.source_email = userEmail
            cftsUser.phone = request.POST.get('phone')
            cftsUser.org = request.POST.get('org')
            if request.POST.get('org') == "OTHER":
                cftsUser.other_org = request.POST.get('other_org')
            else:
                cftsUser.other_org = None

            # the update_info flag is very important, the default value for this field is True
            # when update_info is true a user will be infinitely redirected to the user info edit page
            # this ensures that they have filled in all the required information for their account
            # on successful form save change set update_info to False
            cftsUser.update_info = False
            cftsUser.read_policy = True

            # create or update destination emails for all non blank destination email fields
            for net in nets:
                formEmail = request.POST.get(str(net.name)+' Email')

                # email field wasn't blank
                if formEmail != "":
                    # try and get destination email by network
                    try:
                        # get the Email object for the current network from the users many-to-many destination_emails field
                        destinationEmail = cftsUser.destination_emails.get(network__name=net.name)

                        # if the destination email has changed remove old email object from user and add the new email object
                        if formEmail != destinationEmail:
                            cftsUser.destination_emails.remove(destinationEmail)
                            cftsUser.destination_emails.add(getOrCreateEmail(request, formEmail, net.name))

                    # user had multiple destination emails for the same network, shouldn't happen but just in case remove them all
                    except Email.MultipleObjectsReturned:
                        destinationEmails = cftsUser.destination_emails.filter(network__name=net.name)
                        for email in destinationEmails:
                            cftsUser.destination_emails.remove(email)

                        cftsUser.destination_emails.add(getOrCreateEmail(request, formEmail, net.name))

                    # user has no email for this destination, cerate it, add it
                    except Email.DoesNotExist:
                        cftsUser.destination_emails.add(getOrCreateEmail(request, formEmail, net.name))

            # save all changes, redirect user to front page
            cftsUser.save()
            messages.success(request, "Account info updated")
            return redirect("/frontend")

        # validity check failed, serve the instantiated form back to the user, it will contain helpful error messages for them
        else:
            messages.error(request, "Required fields missing")
            return render(request, 'authForms/editUserInfo.html', context={'resources': resources, "userInfoForm": form})

    # all GET requests should be served a blank form
    form = userInfoForm(instance=cftsUser, networks=nets)
    return render(request, 'authForms/editUserInfo.html', context={'resources': resources, "userInfoForm": form})


# function to collect and display user password reset requests, only available to superusers
@login_required
@user_passes_test(superUserCheck, login_url='frontend', redirect_field_name=None)
def passwordResetAdmin(request):
    # get all Feedback objects with the "password reset" category, sort by most recent uncompleted objects
    resetRequests = Feedback.objects.filter(category="Password Reset").order_by('completed', '-date_submitted')

    # paginate results, 10 per page
    requestPage = paginator.Paginator(resetRequests, 10)
    pageNum = request.GET.get('page')
    pageObj = requestPage.get_page(pageNum)

    return render(request, "pages/passwordResetAdmin.html", context={'resetRequests': pageObj})

# function for users to submit password reset requests based on email
def passwordResetRequest(request):
    resources = ResourceLink.objects.all()

    # only process data from a POST request
    if request.method == "POST":
        # instantiate a password reset form with data from the POST request
        form = PasswordResetForm(request.POST)

        # proceed if form passes validity checks
        if form.is_valid():
            formEmail = form.cleaned_data['email']
            # get all Django user accounts with the entered email
            userMatchingEmail = authUser.objects.filter(email=formEmail)

            if userMatchingEmail.exists():
                # create a Feedback object for every Django user account returned
                for user in userMatchingEmail:
                    cftsUser = User.objects.get(auth_user=user)
                    pendingResets = Feedback.objects.filter(user=cftsUser, category="Password Reset", completed=False).count()

                    # only create a Feedback object if the user has no pending password reset requests
                    if pendingResets == 0:
                        passwordResetFeedback = Feedback(title="Password reset: " + str(user.last_name) + ", " + str(user.first_name) + "(" + str(user.username) + ")", user=cftsUser, category="Password Reset")
                        passwordResetFeedback.save()

            # redirect user to the password reset confirmation page, even if the email they entered in returned no Django users
            return redirect('/password-reset/done')

        # validity check failed, serve the instantiated form back to the user, it will contain helpful error messages for them
        else:
            return render(request, template_name="authForms/passwordResetForms/passwordReset.html", context={'resources': resources, "password_reset_form": form, "envNet": NETWORK})

    # all GET requests should be served a blank form
    form = PasswordResetForm()
    return render(request, template_name="authForms/passwordResetForms/passwordReset.html", context={'resources': resources, "password_reset_form": form, "envNet": NETWORK})


# function to generate email with a unique password reset link for a user, only available to superusers
@login_required
@user_passes_test(superUserCheck, login_url='frontend', redirect_field_name=None)
def passwordResetEmail(request, id, feedback):
    # get the Django user account we are generating the link for, as well as the password reset request
    auth_user = authUser.objects.get(id=id)
    passwordResetFeedback = Feedback.objects.get(feedback_id=feedback)

    rc = {
        'user': auth_user,
        'email': auth_user.email,
        # generate the uid and token to create a unique one-time password reset link for the user
        'uid': urlsafe_base64_encode(force_bytes(auth_user.pk)),
        'token': default_token_generator.make_token(auth_user),
        'urlPrefix': "https://"+str(request.get_host())
    }

    # create mailto link from password reset email template
    msgBody = "mailto:" + str(auth_user.email) + "?subject=CFTS Password Reset&body="

    msgBody += render_to_string('authForms/passwordResetForms/passwordResetEmail.html', rc, request)

    # set the password reset Feedback object to completed
    passwordResetFeedback.completed = True
    passwordResetFeedback.save()

    return HttpResponse(str(msgBody))

# function for users to lookup their own username, because users can't remember anything
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
