from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from .models import *

import random

# Views here output/render a template.
def index( request ):
    return render(request, 'pages/index.html')

def consent( request ):
    return render(request, 'pages/consent.html')

def howTo( request ):
    return render(request, 'pages/howTo.html')

def resources( request ):
    return render(request, 'pages/resources.html')

def urlShortner( request ):
    return render(request, 'pages/urlShortner.html')

@login_required
def analysts( request ):
    xfer_queues = []
    networks = Network.objects.all()
    empty = random.choice( [ 'These pipes are clean.', 'LZ is clear.', 'Nothing here. Why not work on metadata?', 'Queue is empty -- just like my wallet.', "There's nothing here? Huh. That's gotta be an error ... " ] )

    for net in networks:
      dataset = Request.objects.filter( network__name=net.name, is_submitted=True, date_complete__isnull=True ).order_by( '-date_created' )
      queue = { 'name': net.name, 'count': dataset.count(), 'q': dataset }
      xfer_queues.append( queue )
    
    xfer_queues = sorted( xfer_queues, key=lambda k: k['count'], reverse=True )
    rc = { 'queues': xfer_queues, 'empty': empty }
    return render( request, 'pages/analysts.html', { 'rc': rc } )

@login_required
def transferRequest( request, id ):
    rqst = Request.objects.get( request_id = id )
    rc = { 
      'request_id': rqst.request_id,
      'date_created': rqst.date_created,
      'user': User.objects.get( user_id = rqst.user.user_id ),
      'network': Network.objects.get( network_id = rqst.network.network_id ),
      'files': rqst.files.all(),
      'target_email': Email.objects.get( email_id = rqst.target_email.email_id ),
      'is_submitted': rqst.is_submitted,
      'date_pulled': rqst.date_pulled,
      'user_pulled': rqst.user_pulled,
      'pull_number': rqst.pull_number,
      'date_oneeye': rqst.date_oneeye,
      'user_oneeye': rqst.user_oneeye,
      'date_twoeye': rqst.date_twoeye,
      'user_twoeye': rqst.user_twoeye,
      'date_complete': rqst.date_complete,
      'user_complete': rqst.user_complete,
      'disc_number': rqst.disc_number
    }
    return render( request, 'pages/transfer-request.html', { 'rc': rc } )

@login_required
def createZip( request, network_name ):
  #select Requests based on network and status
  requestsToPull = Request.objects.filter( network = network_name, date_pulled = None )
  return HttpResponse({requestsToPull})

  #compile files from Requests


  '''
  zip_file = open(path_to_file, 'r')
  response = HttpResponse(zip_file, content_type='application/force-download')
  response['Content-Disposition'] = 'attachment; filename="%s"' % 'foo.zip'
  return response
  '''
  pass
