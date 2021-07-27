# ====================================================================
# crypto
import hashlib
from django import http
# responses
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

# db/model stuff
from pages.models import *
# ====================================================================


@ensure_csrf_cookie
def frontend(request):
    try:
        request.session.__getitem__('consent')
        request.session.set_expiry(0)
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
    
    except KeyError:
        request.session.__setitem__('consent','consent given')
        request.session.set_expiry(0)
        return render(request, 'pages/consent.html')
