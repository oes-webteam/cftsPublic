from io import BytesIO
from zipfile import ZipFile
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, FileResponse
from django.db.models import Max, Count, Q, Sum
from .models import *

import random
import datetime

# Views here output/render a template.
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

@login_required
def analysts( request ):
    xfer_queues = []
    networks = Network.objects.all()
    empty = random.choice( [ 
      'These pipes are clean.', 
      'LZ is clear.', 
      'Nothing here. Why not work on metadata?', 
      'Queue is empty -- just like my wallet.', 
      "There's nothing here? Huh. That's gotta be an error ... " 
    ] )

    for net in networks:
      # get information about the last pull that was done on each network
      last_pull =Request.objects.values( 
        'pull_number', 
        'date_pulled', 
        'user_pulled__username' 
        ).filter( network__name=net.name ).order_by( '-date_pulled' )[:1]
      
      # get all the xfer requests (pending and pulled) submitted for this network
      dataset = Request.objects.filter( 
        network__name=net.name, 
        is_submitted=True, 
        date_complete__isnull=True ).order_by( '-date_created' )
      
      # count how many total files are in all the pending requests (excluding ones that have already been pulled)
      file_count = dataset.annotate( 
        files_in_request = Count( 'files__file_id', filter=Q( date_pulled__isnull=True ) ) 
      ).aggregate( 
        files_in_dataset = Sum( 'files_in_request' ) 
      )

      # smoosh all the info together into one big, beautiful data object ...
      queue = { 
        'name': net.name, 
        'order_by': net.sort_order, 
        'file_count': file_count, 
        'count': dataset.count(), 
        'pending': dataset.aggregate( count = Count( 'request_id', filter=Q( date_pulled__isnull=True ) ) ), 
        'q': dataset, 
        'last_pull': last_pull 
      }
      # ... and add it to the list
      xfer_queues.append( queue )
    
    # sort the list of network queues into network order
    xfer_queues = sorted( xfer_queues, key=lambda k: k['order_by'], reverse=False )
    
    # create the request context
    rc = { 'queues': xfer_queues, 'empty': empty }
    
    # roll that beautiful bean footage
    return render( request, 'pages/analysts.html', { 'rc': rc } )

@login_required
def transferRequest( request, id ):
    rqst = Request.objects.get( request_id = id )
    rc = { 
      'request_id': rqst.request_id,
      'date_created': rqst.date_created,
      'user': User.objects.get( user_id = rqst.user.user_id ),
      'network': Network.objects.get( network_id = rqst.network.network_id ),
      'files': rqst.files.all(),
      'target_email': Email.objects.get( email_id = rqst.target_email.email_id ),
      'is_submitted': rqst.is_submitted,
      'date_pulled': rqst.date_pulled,
      'user_pulled': rqst.user_pulled,
      'pull_number': rqst.pull_number,
      'date_oneeye': rqst.date_oneeye,
      'user_oneeye': rqst.user_oneeye,
      'date_twoeye': rqst.date_twoeye,
      'user_twoeye': rqst.user_twoeye,
      'date_complete': rqst.date_complete,
      'user_complete': rqst.user_complete,
      'disc_number': rqst.disc_number
    }
    return render( request, 'pages/transfer-request.html', { 'rc': rc } )

@login_required
def createZip( request, network_name ):
  # create pull number
  maxPull = Request.objects.aggregate( Max( 'pull_number' ) )
  pull_number = maxPull['pull_number__max'] + 1
  
  # create/overwrite zip file
  zipPath =  os.path.join( settings.STATICFILES_DIRS[0], "files\\" ) + network_name + "_" + str( pull_number ) + ".zip"
  zip = ZipFile( zipPath, "w" )

  #select Requests based on network and status
  qs = Request.objects.filter( network__name = network_name, date_pulled = None )

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

    # update the records
    rqst.date_pulled = datetime.datetime.now()
    rqst.user_pulled = request.user
    rqst.pull_number = pull_number
    rqst.save()

  zip.close()

  # see if we can't provide something more useful to the analysts - maybe the new pull number?
  return JsonResponse( { 'pullNumber': rqst.pull_number, 'datePulled': rqst.date_pulled.strftime( "%d%b %H%M" ).upper(), 'userPulled': str( rqst.user_pulled ) } )