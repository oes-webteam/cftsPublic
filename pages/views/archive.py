#====================================================================
# core
from django.core import paginator
# decorators
from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.template.loader import render_to_string

# responses
from django.shortcuts import render

# model/database stuff
from pages.models import *
#====================================================================


@login_required
def archive( request ):
  networks = Network.objects.all()
  requests = Request.objects.filter( pull__isnull = False )
  
  requestPage = paginator.Paginator(requests, 50)
  pageNum = request.GET.get('page')
  pageObj = requestPage.get_page(pageNum)

  rc = { 'requests': pageObj, 'networks': networks }
  return render( request, 'pages/archive.html', { 'rc': rc } )

@login_required
def filterArchive( request ):
  networks = Network.objects.all()

  filters = dict(request.POST.lists())
  #print(filters)

  pullInfo = filters['pull'][0].split("_")

  try:
    if isinstance(int(pullInfo[0]),int):
      pullNum = pullInfo[0]
      networkName = ""
  except ValueError:
    try:
      networkName = pullInfo[0]
    except IndexError:
      networkName = ""

    try:
      pullNum = pullInfo[1]
    except IndexError:
      pullNum = ""

  requests = Request.objects.filter( 
    pull__isnull = False,
    user__name_first__icontains=filters['userFirst'][0],
    user__name_last__icontains=filters['userLast'][0],
    network__name__icontains=filters['network'][0],
    pull__network__name__icontains=networkName,
    pull__pull_number__icontains=pullNum,
    files__file_name__icontains=filters['files'][0],
    target_email__address__icontains=filters['email'][0],
    org__icontains=filters['org'][0]
    )

  if filters['date'][0] != "":
    requests = requests.filter(date_created__date=filters['date'][0])
  
  # requestPage = paginator.Paginator(requests, 5)
  # pageNum = request.GET.get('page')
  # pageObj = requestPage.get_page(pageNum)

  rc = { 'requests': requests, 'networks': networks }
  return render( request, 'partials/Archive_partials/archiveResults.html', { 'rc': rc })
