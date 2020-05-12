#====================================================================
# responses
from django.shortcuts import render
from django.http import HttpResponse

# db/model stuff
from pages.models import *
#====================================================================

def testCards(request):
  nets = Network.objects.all()
  rc = { 'networks': nets }

  return render(request, 'pages/testCards.html', { 'rc': rc } )