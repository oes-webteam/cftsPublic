#====================================================================
# core
from zipfile import ZipFile
from django.conf import settings

# decorators
from django.contrib.auth.decorators import login_required

# responses
from django.shortcuts import render
from django.http import JsonResponse # , HttpResponse, FileResponse

# model/database stuff
from pages.models import *
#====================================================================


@login_required
def setReject( request ):
  thestuff = dict( request.POST.lists() )

  reject_id = thestuff[ 'reject_id' ]
  request_id = thestuff[ 'request_id' ]
  id_list = thestuff[ 'id_list[]' ]
  
  # update the files to set the rejection
  File.objects.filter( file_id__in = id_list ).update( rejection_reason_id = reject_id[0] )

  # recreate the zip file for the pull
  someRequest = Request.objects.get( request_id = request_id )
  network_name = someRequest.network__name
  pull_number = someRequest.pull__pull_number

  zipPath =  os.path.join( settings.STATICFILES_DIRS[0], "files\\" ) + network_name + "_" + str( pull_number ) + ".zip"
  zip = ZipFile( zipPath, "w" )

  #select Requests based on pull
  qs = Request.objects.filter( pull__pull_id = someRequest.pull__pull_id, file__rejection_reason = None )

  # for each xfer request ...
  for rqst in qs:
    zip_folder = str( rqst.user )
    theseFiles = rqst.files.all()

    # add their files to the zip in the folder of their name
    for f in theseFiles:
      zip_path = os.path.join( zip_folder, str( f ) )
      zip.write( f.file_object.path, zip_path )

    # create and add the target email file
    email_file_name = str( rqst.target_email )
    fp = open( email_file_name, "w" )
    fp.close()
    zip.write( email_file_name, os.path.join( zip_folder, email_file_name ) )
    os.remove( email_file_name )

  zip.close()

  return JsonResponse( { 'mystring': 'isgreat' } )

@login_required
def getUser( request, id ):
  user = User.objects.get( user_id = id )
  data = {
    'user_id': user.user_id,
    'first_name': user.name_first,
    'last_name': user.name_last,
    'email': user.email.address
  }
  return JsonResponse( data )