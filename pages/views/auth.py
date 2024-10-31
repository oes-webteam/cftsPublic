import hashlib
from django.shortcuts import render, redirect

from pages.forms import userInfoForm, userLogInForm

from django.contrib.auth import login, authenticate
from django.contrib import messages

from pages.models import Network, User, Email, ResourceLink
from cfts.settings import NETWORK, DEBUG, IM_ORGBOX_EMAIL, ALLOWED_DOMAIN
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

    # get the HTTP CERT_SUBJECT header, for CENTCOM external users
    try:
        cert = request.META['HTTP_SUBJECT']

        # empty cert, IIS is set to ignore certs, IIS NEEDS TO REQURE CERTS IN PRODUCTION!!!
        if cert == "":
            return {'status': "empty"}
        else:
            userHash = hashCert(cert)
            if userHash in buggedPKIs:
                return {'status': "buggedPKI"}
            else:
                return {'status': "externalPKI", 'cert': cert, 'userHash': userHash}

    # get the HTTP CERT_SUBJECT header, for CENTCOM internal users
    except KeyError:
        try:
            cert = request.META['CERT_SUBJECT']
            # empty cert, try getting windows login
            if cert == "":
                try:
                    cert = request.META['AUTH_USER']
                    # empty cert, IIS is set to ignore certs, IIS NEEDS TO REQURE CERTS IN PRODUCTION!!!
                    if cert == "":
                        return {'status': "empty"}
                    # got a cert!
                    else:
                        userHash = hashCert(cert)
                        if userHash in buggedPKIs:
                            return {'status': "buggedPKI"}
                        else:
                            return {'status': "validPKI", 'cert': cert, 'userHash': userHash}

                except KeyError:
                    return {'status': "empty"}

            # got a cert!
            else:
                userHash = hashCert(cert)
                if userHash in buggedPKIs:
                    return {'status': "buggedPKI"}
                else:
                    return {'status': "validPKI", 'cert': cert, 'userHash': userHash}

        except KeyError:
            return {'status': "empty"}

# function to retrive or create a single Email record
def getOrCreateEmail(request, address, network):
    # retieve Network object based on passed in args
    emailNet = Network.objects.get(name=network)
    allowed_domain = ALLOWED_DOMAIN  # Replace with the required domain
    
    # try to get email based on both address and network first
    try:
        userEmail = Email.objects.get(address=address, network=emailNet)
        
        # just in case, if the Email object's network field does not match the Network object we retrieved then rewrite it
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
    
    # Ensure the user's email is from the allowed domain
    user_email_domain = userEmail.address.split('@')[-1]
    print("This is the user email domain", user_email_domain)
    if user_email_domain != allowed_domain and network == NETWORK:
        print(network)
        raise ValueError(f"User email must be from the {allowed_domain} domain.")
    
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
            except User.MultipleObjectsReturned:
                messages.error(request, "An error occured while trying to identify user, please click the 'Contact Us' link to request help.")
                users = User.objects.filter(user_identifier=userHash).values_list('user_id', flat=True)
                logger.error("------------ User Identifier Collision ------------")
                logger.error(userHash)
                logger.error(users)
                return False

        # the user is external, so we can't user a certificate hash to retrieve a User object, external users MUST BE LOGGED IN
        else:
            # if they are logged in then get the User object that has a one-to-one relationship with the currently logged in Django user account
            if DEBUG == True and certInfo['status'] == "empty":
                if request.user.is_authenticated:
                    user = User.objects.get(auth_user=request.user)
                    if user.user_identifier == None or user.user_identifier == "":
                        try:
                            user.user_identifier = certInfo['userHash']
                            user.save()
                        except:
                            pass
                else:
                    return None
            else:
                messages.error(request, "Unable to identify user, please click the 'Contact Us' link to request help.")
                return None
            # # otherwise boot them to the log in page
            # else:

    # could not retireve any User object, one will need to be created, the user MUST BE LOGGED IN
    except User.DoesNotExist:
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
            clean_data = form.clean()
            # attempt to authenticate a user with matching username and password, password is automaticlly hashed by the authenticate() function
            user = authenticate(request, username=clean_data['username'], password=clean_data['password'])

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


# function for user to update certain information about their account
# @login_required
def editUserInfo(request):
    resources = ResourceLink.objects.all()

    # retrieve all Network objects where visible == True, visible == False is for decomissioned networks and the network defined in network.py
    # these networks are used for dynamically creating the destination email fields
    nets = Network.objects.filter(visible=True)

    # get user cert info and retrieve a user record
    certInfo = getCert(request)
    cftsUser = getOrCreateUser(request, certInfo)

    if cftsUser == None:
        cftsUser = User(
            user_identifier=certInfo['userHash']
        )

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
            cftsUser.save()

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
            return render(request, 'authForms/editUserInfo.html', context={'resources': resources, "userInfoForm": form, "rc": {'orgBox': IM_ORGBOX_EMAIL}})

    # all GET requests should be served a blank form
    form = userInfoForm(instance=cftsUser, networks=nets)
    return render(request, 'authForms/editUserInfo.html', context={'resources': resources, "userInfoForm": form, "rc": {'user': cftsUser, 'orgBox': IM_ORGBOX_EMAIL}})
