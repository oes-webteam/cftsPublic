#====================================================================
# decorators
from django.contrib.auth.decorators import login_required

# responses
from django.shortcuts import render

# model/database stuff
from pages.models import *
#====================================================================

@login_required
def reports( request ):
  rc = {}
  return render( request, 'pages/reports.html', { 'rc': rc } )
