#====================================================================
# responses
from django.shortcuts import render
from django.http import HttpResponse

# db/model stuff
from pages.models import *
#====================================================================

def frontend(request):
  nets = Network.objects.all()
  resources = ResourceLink.objects.all()
#  for rl in resources:
#    print( rl.file_name )
  rc = { 'networks': nets, 'resources': resources }

  return render(request, 'pages/frontend.html', { 'rc': rc } )