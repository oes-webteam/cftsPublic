#====================================================================
from django.http import HttpResponse, JsonResponse
from pages.models import Classification #, File
from django.contrib.auth.decorators import login_required
# from django.core.files.base import ContentFile
#====================================================================

def stubGet( request ):
  return JsonResponse( {} )

def stubPost( request ):
  data = {}
  if request.method == 'POST':
    data = request.POST.dict()

  return JsonResponse( data )

@login_required
def makeFiles( request ):
  unclass = Classification.objects.get( abbrev='U' )
  return HttpResponse( 'Made the files' )
  '''
  for i in range( 16, 20 ):
    # filename
    new_f = 'textfile_' + str(i) + '.txt'
    # new CFTS File object
    new_file = File( classification = unclass )
    # save the new CFTS file
    new_file.save()
    # save the Django File into the CFTS File
    new_file.file_object.save( new_f, ContentFile( new_f ) )
  '''