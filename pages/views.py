from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from .models import *

import random

# Views here output/render a template.
def index(request):
    return render(request, 'pages/index.html')

def consent(request):
    return render(request, 'pages/consent.html')

def howTo(request):
    return render(request, 'pages/howTo.html')

def resources(request):
    return render(request, 'pages/resources.html')

def urlShortner(request):
    return render(request, 'pages/urlShortner.html')

@login_required
def analysts(request):
    xfer_queues = []
    networks = Network.objects.all()
    empty = random.choice( [ 'These pipes are clean.', 'LZ is clear.', 'Nothing here. Why not work on metadata?', 'Queue is empty -- just like my wallet.', "There's nothing here? Huh. That's gotta be an error ... " ] )

    for net in networks:
      ds = Request.objects.filter( network__name=net.name, is_submitted=True, date_complete__isnull=True ).order_by( '-date_created' )
      queue = { 'name': net.name, 'count': ds.count(), 'q': ds }
      xfer_queues.append( queue )
    
    xfer_queues = sorted( xfer_queues, key=lambda k: k['count'], reverse=True )
    rc = { 'queues': xfer_queues, 'empty': empty }
    return render(request, 'pages/analysts.html', {'rc': rc} )
