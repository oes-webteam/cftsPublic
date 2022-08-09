# ====================================================================
# core
import datetime
from django.contrib import messages

# decorators
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache

# responses
from django.shortcuts import redirect, render
from django.http import JsonResponse, FileResponse

# model/database stuff
from pages.models import *

# cfts settings
from cfts import settings

from pages.views.auth import superUserCheck, staffCheck
from pages.views.dev_tools import fileCleanup
# ====================================================================


# function to get list of all staff users that reviewed any file in a pull
def getReviewers(pull):
    # get a combined list of unique usernames for oneeye and twoeye reviewers on all files in a pull
    oneEyers = Request.objects.filter(pull=pull).values_list('files__user_oneeye__username', flat=True)
    twoEyers = Request.objects.filter(pull=pull).values_list('files__user_twoeye__username', flat=True)
    reviewers = list(oneEyers) + list(twoEyers)
    return set(reviewers)


# function to serve the pulls history page, only available to staff users
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def pulls(request):
    # request context
    rc = {
        'bodyText': 'This is the Pulls dashboard',
        'pull_history': []
    }

    networks = Network.objects.all()

    # get last 5 pulls for each network for current day and all past incomplete pulls
    for net in networks:
        # get information about the last 5 pulls that was done on each network
        pulls = Pull.objects.filter(network__name=net.name).filter(date_pulled__date=datetime.datetime.now().date()).order_by('-date_pulled')[:5]

        # and all pulls on that network that were never completed
        incompletePulls = Pull.objects.filter(network__name=net.name).filter(date_pulled__date__lt=datetime.datetime.now().date(), date_complete__isnull=True).order_by('-date_pulled')

        these_pulls = []

        # formatting information from Pull objects into dictionarys
        # this was written before my time so I'm not sure why this wasn't just done in the pulls.html template, but it works so whatev
        for pull in pulls:
            reviewers = getReviewers(pull)

            this_pull = {
                'pull_id': pull.pull_id,
                'pull_number': pull.pull_number,
                'pull_date': pull.date_pulled,
                'pull_user': pull.user_pulled,
                'date_complete': pull.date_complete,
                'user_complete': pull.user_complete,
                'disk_number': pull.disc_number,
                'pull_network': net.name,
                'reviewers': reviewers,
            }
            these_pulls.append(this_pull)

        for pull in incompletePulls:
            reviewers = getReviewers(pull)

            this_pull = {
                'pull_id': pull.pull_id,
                'pull_number': pull.pull_number,
                'pull_date': pull.date_pulled,
                'pull_user': pull.user_pulled,
                'date_complete': pull.date_complete,
                'user_complete': pull.user_complete,
                'disk_number': pull.disc_number,
                'pull_network': net.name,
                'reviewers': reviewers,
            }
            these_pulls.append(this_pull)

        if len(these_pulls) > 0:
            rc['pull_history'].append(these_pulls)

    return render(request, 'pages/pulls.html', {'rc': rc})


# function to 'complete' a Pull object
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def pullsDone(request, id, cd):
    # get the Pull object to complete
    thisPull = Pull.objects.get(pull_id=id)

    # update Pull info
    thisPull.date_complete = datetime.datetime.now()
    thisPull.user_complete = request.user
    thisPull.disc_number = cd
    thisPull.queue_for_delete = True
    thisPull.save()

    fileCleanup(request)

    messages.success(request, "Pull completed")
    return JsonResponse({'id': id})


# function to get and return/download the pull zip file
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def getPull(request, fileName):
    response = FileResponse(
        open(os.path.join(settings.PULLS_DIR, fileName), 'rb'))
    return response

# function to cancel a pull
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def cancelPull(request, id):
    # get the Pull object to cancel and all objects that have a relationship to the Pull object
    thisPull = Pull.objects.get(pull_id=id)
    network = thisPull.network.name
    files = File.objects.filter(pull=id)
    requests = Request.objects.filter(pull=id)

    # remove the relationship between the Pull object and all returned File and Request objects
    # we do this before we delete the Pull object to avoid database integrity errors
    files.update(pull=None)
    requests.update(pull=None)

    # once the pull is deleted all request will move back to the "Pullable" section of the queue
    zipPath = os.path.join(settings.PULLS_DIR+"\\") + thisPull.network.name + "_" + str(thisPull.pull_number) + " " + str(thisPull.date_pulled.astimezone().strftime("%d%b %H%M")) + ".zip"
    os.remove(zipPath)
    thisPull.delete()
    messages.success(request, "Pull canceled, requests returned to pending queue")
    return redirect('/queue?network=' + network)
