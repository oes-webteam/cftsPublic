from django.shortcuts import render
from django.http import HttpResponse

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
