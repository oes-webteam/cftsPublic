from django.shortcuts import render

# Views here ONLY output/render a template. No DB, no business logic, no nuthin'
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
