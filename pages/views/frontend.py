from django.shortcuts import render
from django.http import HttpResponse # JsonResponse, FileResponse

def testCards(request):
    return render(request, 'pages/testCards.html')

