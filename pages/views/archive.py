#====================================================================
# core

# decorators
from django.contrib.auth.decorators import login_required

# responses
from django.shortcuts import render

# model/database stuff
from pages.models import *
#====================================================================


@login_required
def archive( request ):
  networks = Network.objects.all()
  requests = Request.objects.filter( pull__isnull = False )
  rc = { 'requests': requests, 'networks': networks }
  return render( request, 'pages/archive.html', { 'rc': rc } )
