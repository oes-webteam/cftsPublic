# ====================================================================
# core
from django.core import paginator
# decorators
from django.contrib.auth.decorators import login_required, user_passes_test

# responses
from django.shortcuts import render

# model/database stuff
from pages.models import *
from pages.views.auth import superUserCheck, staffCheck

import logging

logger = logging.getLogger('django')
# ====================================================================

# function to return a pagenated list of all pulled Requests
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def archive(request):
    networks = Network.objects.all()

    if request.GET.get('page'):
        rc = {'requests': pageObj, 'networks': networks}
        return render(request, 'pages/archive.html', {'rc': rc})

    # get all Request objects that have been pulled
    requests = Request.objects.filter(pull__isnull=False)

    # render 50 results per page
    requestPage = paginator.Paginator(requests, 50)
    pageNum = request.GET.get('page')
    pageObj = requestPage.get_page(pageNum)

    rc = {'requests': pageObj, 'networks': networks}
    return render(request, 'pages/archive.html', {'rc': rc})

# function to filter archive results based on various parameters
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def filterArchive(request):
    networks = Network.objects.all()

    # create a dictionary with a list of filter values from the POST request
    filters = dict(request.POST.lists())

    # try your best to parse out the "pull" filter field, split on an underscore
    # should idealy leave you with a list for the network name and the pull number
    pullInfo = filters['pull'][0].split("_")

    try:
        # can we convert the first list entry to an int?, if so use it as pullNum, assume empty networkName
        if isinstance(int(pullInfo[0]), int):
            pullNum = pullInfo[0]
            networkName = ""

    # couldn't cast first list entry to int, that means it's probably the network name
    except ValueError:
        # set networkName to first list entry, leave blank if no first entry exists
        try:
            networkName = pullInfo[0]
        except IndexError:
            networkName = ""

        # set pullNum to the second list entry, leave blank if no second entry exists
        try:
            pullNum = pullInfo[1]
        except IndexError:
            pullNum = ""

    # get all pulled Request objects
    requests = Request.objects.filter(pull__isnull=False)

    # do a lot of conditional filtering, this is really hacky and awful, not to mention very inefficient...
    if filters['userFirst'][0] != "":
        requests = requests.filter(user__name_first__icontains=filters['userFirst'][0])

    if filters['userLast'][0] != "":
        requests = requests.filter(user__name_last__icontains=filters['userLast'][0])

    if filters['network'][0] != "":
        requests = requests.filter(network__name__icontains=filters['network'][0])

    # filter on networkName and pullNum we parsed above
    if networkName != "":
        requests = requests.filter(pull__network__name__icontains=networkName)

    if pullNum != "":
        requests = requests.filter(pull__pull_number__icontains=pullNum)

    if filters['email'][0] != "":
        requests = requests.filter(target_email__address__icontains=filters['email'][0])

    # org filtering uses iexact becasue using icontains with a submitted value of ARCENT would also return results for MARCENT
    if filters['org'][0] != "":
        requests = requests.filter(org__iexact=filters['org'][0])

    if filters['files'][0] != "":
        requests = requests.filter(files__file_name__icontains=filters['files'][0])

    if filters['date'][0] != "":
        requests = requests.filter(date_created__date=filters['date'][0])

    requestPage = paginator.Paginator(requests.distinct(), 50)
    pageObj = requestPage.get_page(filters['page'][0])

    rc = {'requests': pageObj, 'networks': networks}

    return render(request, 'partials/Archive_partials/archiveResults.html', {'rc': rc})
