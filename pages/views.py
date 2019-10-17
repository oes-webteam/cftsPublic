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

# Remove after testing
def testCards(request):
    return render(request, 'pages/testCards.html')

# Remove after testing
def testCards2(request):
    return render(request, 'pages/testCards2.html')

# Remove after testing
def testCards3(request):
    return render(request, 'pages/testCards3.html')

# Remove after testing
def adminTabs(request):
    return render(request, 'pages/adminTabs.html')
