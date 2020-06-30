#====================================================================
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from pages.models import Classification, Rejection, Network#, File
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
def setupDB( request ):
  if Network.objects.count() == 0:
    # Classifications
    unclass = Classification( classification_id = '8cefbfbe3e5a4d46aea10c22c879569d', fullname = 'UNCLASSIFIED', abbrev = 'U', sort_order = 1 )
    unclass.save()
    fouo = Classification( classification_id = 'fbeeca2f48bc4ebebdc428a8a94a2a90', fullname = 'UNCLASSIFIED//FOR OFFICIAL USE ONLY', abbrev = 'U//FOUO', sort_order = 2 )
    fouo.save()
    c = Classification( classification_id = '49c821fc4bd9487e86ded88610c59f54', fullname = 'CONFIDENTIAL', abbrev = 'C', sort_order = 3 )
    c.save()
    c_rel = Classification( classification_id = 'a605c8d9b6fe404d98812d944c3cf3ca', fullname = 'CONFIDENTIAL//RELEASABLE', abbrev = 'C//REL', sort_order = 4 )
    c_rel.save()
    s = Classification( classification_id = '3fd32c420cc74af0b7a5afd1e481b92e', fullname = 'SECRET', abbrev = 'S', sort_order = 5 )
    s.save()
    s_rel = Classification( classification_id = 'b8f6928f278d4891a77f32cb7c411094', fullname = 'SECRET//RELEASABLE', abbrev = 'S//REL', sort_order = 6 )
    s_rel.save()

    # Networks
    nipr = Network( network_id = 'dabcf4d26dcf475286351de3ac7f0c49', name = 'NIPR', sort_order = 1 )
    nipr.save()
    nipr.classifications.add( unclass )
    nipr.classifications.add( fouo )

    swa = Network( network_id = '568b6f9002d34530ada0cdae631807c3', name = 'CX-SWA', sort_order = 2 )
    swa.save()
    swa.classifications.add( unclass )
    swa.classifications.add( fouo )
    swa.classifications.add( c_rel )
    swa.classifications.add( s_rel )

    bices = Network( network_id = '7cc549aba3064d5b9cb8fa8ec846f252', name = 'BICES', sort_order = 3 )
    bices.save()
    bices.classifications.add( unclass )
    bices.classifications.add( fouo )
    bices.classifications.add( c_rel )
    bices.classifications.add( s_rel )

    sau = Network( network_id = 'be27f19fd42147ebabc098da6d8bb35c', name = 'CPN-SAU', sort_order = 99 )
    sau.save()
    sau.classifications.add( unclass )
    sau.classifications.add( fouo )
    sau.classifications.add( c_rel )
    sau.classifications.add( s_rel )

    cpnx = Network( network_id = '20c87ade9349487ba9f67b358f470add', name = 'CPN-X', sort_order = 99 )
    cpnx.save()
    cpnx.classifications.add( unclass )
    cpnx.classifications.add( fouo )
    cpnx.classifications.add( c_rel )
    cpnx.classifications.add( s_rel )

    # Rejection Reasons
    other = Rejection( name = 'Other', subject = 'CFTS Request Rejected', text = '' )
    other.save()
    no_class = Rejection( name = 'Missing Classification', subject = 'CFTS Transfer Request Rejected -- Missing Classification Markings', text = '' )
    no_class.save()
    jopes = Rejection( name = 'JOPES', subject = 'CFTS Request Rejected -- JOPES Data', text = '' )
    jopes.save()
    bad_class = Rejection( name = 'Contains Classification Markings', subject = 'CFTS Request Rejected -- Contains Classification Markings', text = '' )

  return render( request, 'pages/setupdb.html' )
