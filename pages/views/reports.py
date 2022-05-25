# ====================================================================
# decorators
from django.contrib.auth.decorators import login_required, user_passes_test
from pages.views.auth import superUserCheck, staffCheck

# responses
from django.shortcuts import render

# model/database stuff
from pages.models import *
from django.contrib.auth.models import User as authUser

# ====================================================================


@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def reports(request):
    if request.user.is_superuser:
        rc = {'staff': authUser.objects.filter(is_staff=True)}
    else:  
        rc = {}
    return render(request, 'pages/reports.html', {'rc': rc})
