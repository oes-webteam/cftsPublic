#====================================================================
# core
from django.core import paginator
# decorators
from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse

# responses
from django.shortcuts import render

# model/database stuff
from pages.models import *
#====================================================================


@login_required
def archive( request ):
  networks = Network.objects.all()
  requests = Request.objects.filter( pull__isnull = False )
  
  requestPage = paginator.Paginator(requests, 25)
  pageNum = request.GET.get('page')
  pageObj = requestPage.get_page(pageNum)

  rc = { 'requests': pageObj, 'networks': networks }
  return render( request, 'pages/archive.html', { 'rc': rc } )
