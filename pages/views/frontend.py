# ====================================================================
# crypto
import hashlib
# responses
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

# db/model stuff
from pages.models import *
# ====================================================================


@ensure_csrf_cookie
def frontend(request):
    nets = Network.objects.all()
    resources = ResourceLink.objects.all()
    try:
        cert = request.META['CERT_SUBJECT']
        userHash = hashlib.md5()
        userHash.update(cert.encode())
        userHash = userHash.hexdigest()
        rc = {'networks': nets, 'resources': resources,
              'cert': cert, 'userHash': userHash}
    except KeyError:
        rc = {'networks': nets, 'resources': resources, }
    #  for rl in resources:
#    print( rl.file_name )

    return render(request, 'pages/frontend.html', {'rc': rc})
