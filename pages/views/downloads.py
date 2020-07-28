#====================================================================
# responses
from django.http import  FileResponse


def downloads(request, file):
    filename = 'templates/partials/files/{}'.format(file)
    response = FileResponse(open(filename, 'rb'))
    return response

