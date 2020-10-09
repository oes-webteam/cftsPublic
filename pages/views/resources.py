#====================================================================
# responses
from django.http import  FileResponse


def resources(request, file):
    filename = 'resources/' + file
    response = FileResponse(open(filename, 'rb'))
    return response

