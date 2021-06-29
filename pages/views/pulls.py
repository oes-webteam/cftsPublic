#====================================================================
# core
import datetime

# decorators
from django.contrib.auth.decorators import login_required
from django.http.response import FileResponse

# responses
from django.shortcuts import render
from django.http import JsonResponse, FileResponse #, HttpResponse, FileResponse

# model/database stuff
from pages.models import *

# cfts settings
from cfts import settings
#====================================================================


@login_required
def pulls( request ):
  # request context
  rc = {
    'bodyText': 'This is the Pulls dashboard',
    'pull_history': []
  }

  networks = Network.objects.all()

  # get last 10 pull data for each network
  for net in networks:
    # get information about the last pull that was done on each network
    pulls = Pull.objects.filter( network__name=net.name ).order_by( '-date_pulled' )[:5]
    these_pulls = []
    for pull in pulls:
      this_pull = {
        'pull_id': pull.pull_id,
        'pull_number': pull.pull_number,
        'pull_date': pull.date_pulled,
        'pull_user': pull.user_pulled,
        'date_oneeye': pull.date_oneeye,
        'user_oneeye': pull.user_oneeye,
        'date_twoeye': pull.date_twoeye,
        'user_twoeye': pull.user_twoeye,
        'date_complete': pull.date_complete,
        'user_complete': pull.user_complete,
        'disk_number': pull.disc_number,
        'pull_network': net.name,
        'centcom_pull': pull.centcom_pull
      }
      these_pulls.append( this_pull )
    rc['pull_history'].append( these_pulls )

  return render( request, 'pages/pulls.html', { 'rc': rc } )

@login_required
def pullsOneEye( request, id ):
  thisPull = Pull.objects.get( pull_id = id )
  thisPull.date_oneeye = datetime.datetime.now()
  thisPull.user_oneeye = request.user
  thisPull.save()
  return JsonResponse( { 'id': id } )

@login_required
def pullsTwoEye( request, id ):
  thisPull = Pull.objects.get( pull_id = id )
  thisPull.date_twoeye = datetime.datetime.now()
  thisPull.user_twoeye = request.user
  thisPull.save()
  return JsonResponse( { 'id': id } )

@login_required
def pullsDone( request, id, cd ):
  thisPull = Pull.objects.get( pull_id = id )
  thisPull.date_complete = datetime.datetime.now()
  thisPull.user_complete = request.user
  thisPull.disc_number = cd
  thisPull.save()
  return JsonResponse( { 'id': id } )

@login_required
def getPull(request, fileName):
  response = FileResponse(
      open(os.path.join(settings.PULLS_DIR, fileName), 'rb'))
  return response

