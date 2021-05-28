#====================================================================
# core
import json
from datetime import datetime
from zipfile import ZipFile
from django.conf import settings

#utilities
from django.utils.dateparse import parse_date

# decorators
from django.contrib.auth.decorators import login_required

# responses
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect # , HttpResponse, FileResponse

# model/database stuff
from pages.models import *

# smartcard stuff
import chilkat2
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
  someRequest = Request.objects.get( request_id = request_id[0] )
  network_name = someRequest.network.name
  pull_number = someRequest.pull.pull_number

  zipPath =  os.path.join( settings.STATICFILES_DIRS[0], "files\\" ) + network_name + "_" + str( pull_number ) + ".zip"
  zip = ZipFile( zipPath, "w" )

  #select Requests based on pull
  qs = Request.objects.filter( pull__pull_id = someRequest.pull.pull_id, files__rejection_reason = None )

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

@login_required
def runNumbers( request ):
  files_reviewed = 0
  files_transfered = 0
  start_date = datetime.strptime( request.POST.get( 'start_date' ), "%m/%d/%Y" ).date()
  end_date = datetime.strptime( request.POST.get( 'end_date' ), "%m/%d/%Y" ).date()

  # only the completed requests, tyvm
  requests_in_range = Request.objects.filter( pull__date_complete__date__range = ( start_date, end_date ) )

  for rqst in requests_in_range:
    
    files_in_request = rqst.files.all()

    for f in files_in_request:
      file_count = 1
      file_name = f.__str__()
      ext = file_name.split( '.' )[1]

      # if it's a zip ...
      if ext == 'zip':
        # ... count all the files in the zip ...
        path = f.file_object.path
        with ZipFile( path, 'r' ) as zip:
          contents = zip.namelist()
          # ... minus the folders
          for c in contents:
            if c[-1] == "/" or c[-1] == "\\":
              contents.remove( c )
          file_count = len( contents )

      # sum it all up
      files_reviewed = files_reviewed + file_count
      # exclude the rejects from the transfers numbers
      if f.rejection_reason == None:
        files_transfered = files_transfered + file_count

  return JsonResponse( { 'files_reviewed': files_reviewed, 'files_transfered': files_transfered } )

def process ( request ):
  resp = {}
  
  if request.method == 'POST':
    form_data = request.POST
    print(form_data)
    form_files = request.FILES

    # use the form data to create the necessary records for the request
    source_email = Email( address = form_data.get( 'userEmail' ) )
    source_email.save()
    
    destination_list = form_data.get( 'targetEmail' ).split( "," )
    target_list = []
    for destination in destination_list:
      target_email = Email( address = destination )
      target_email.save()
      target_list.append( target_email )

    user = User( 
      name_first = form_data.get( 'firstName' ), 
      name_last = form_data.get( 'lastName' ), 
      email = source_email,
      is_centcom=form_data.get('isCentcom'),
      user_identifier=form_data.get('userID')
      )
    user.save()

    request = Request( 
      user = user, 
      network = Network.objects.get( name = form_data.get( 'network' ) ),  
      comments = form_data.get( 'comments' )
      )
    request.save()
    request.target_email.add( *target_list )

    # add files to the request
    file_info =  json.loads( form_data.get( 'fileInfo' ) )
    print( form_files.getlist( "files" ) )
    for i, f in enumerate( form_files.getlist( "files" ) ):
      this_file = File(
        file_object = f,
        classification = Classification.objects.get( abbrev = file_info[ i ][ 'classification' ] ),
        is_pii = file_info[ i ][ 'encrypt' ] == 'true'
        )
      this_file.save()
      request.files.add( this_file )
    
    request.is_submitted = True
    request.save()

    resp = { 'status': 'success', 'request_id': request.pk }

  else:
    resp = { 'status': 'fail', 'reason': 'bad-request-type', 'msg': "The 'api-processrequest' view only accepts POST requests." }

  return JsonResponse( resp )


def cardAuth(request):
  user = {}
  authAttempts = request.GET.get('authAttempts')
  cardPIN = request.GET.get('cardPIN')
  userInfo = authGetCerts(cardPIN, authAttempts)

  if userInfo == False:
    correctPIN = False
  else:
    user = verifyUserInfo(userInfo)
    correctPIN = True

  resp = {'status': 'success',
          'authAttempts': authAttempts,
          'correctPIN': correctPIN,
          'user': user
          }
  return JsonResponse(resp)


##################################################################
store = chilkat2.CertStore()


cspName = ""
store.OpenSmartcard(cspName)


def authGetCerts(cardPIN, authAttempts):
    #print("-------------------------------------------------")
    userInfo = []
    i = 0
    while(i < store.NumCertificates):
        try:
            cert = store.GetCertificate(i)
            cert.SmartCardPin = cardPIN

            authStatus = cert.CheckSmartCardPin()
            if authStatus == 1:
                print("Correct PIN")
                if cert.SubjectCN != "":
                    #print("Cert #%d loaded from smartcard: " % i)
                    #print("CN: " + cert.SubjectCN)
                    dodID = cert.SubjectCN.split(".")
                    user = {
                        "firstName": dodID[1],
                        "lastName": dodID[0],
                        "ID": cert.SubjectCN,
                        "Email": ""
                    }

                    #print("DoD ID: " + dodID[-1])
                    #print("Alt Name: " + cert.SubjectAlternativeName.split(">")
                    #       [3].split("<")[0])
                    user["Email"] = cert.SubjectAlternativeName.split(">")[
                        3].split("<")[0]
                    userInfo.append(user)

            elif authStatus == 0:
                print("Incorrect PIN")
                #print("-------------------------------------------------")
                # if authAttempts > 0:
                #     print("You have %s PIN attemtps left" % authAttempts)
                # else:
                return False

            elif authStatus < 0:
                print("Smartcard does not support a PIN")

        except UnicodeDecodeError:
            pass

        #print("-------------------------------------------------")
        i = i + 1
    return userInfo


def verifyUserInfo(userInfo):
  differentID = False
  i = 0
  while(i < len(userInfo)):
      try:
          if(userInfo[i] != userInfo[i+1]):
              differentID = True
          i = i + 1
      except(IndexError):
          break

  if userInfo != []:
      if differentID == True:
          print("User info not uniform.")
      else:
          # print("All user info is the same")
          # print("First Name:", userInfo[0]["firstName"])
          # print("Last Name:", userInfo[0]["lastName"])
          # print("DoD ID:", userInfo[0]["ID"])
          # print("Email: ", userInfo[0]["Email"])
          user = {
              "firstName": userInfo[0]["firstName"],
              "lastName": userInfo[0]["lastName"],
              "ID": userInfo[0]["ID"],
              "Email": userInfo[0]["Email"]
          }
          return user
