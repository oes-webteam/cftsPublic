# decorators
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import permission_required

from pages.views.auth import superUserCheck, staffCheck
from django.shortcuts import render, redirect, get_object_or_404
from pages.forms import complianceBannerForm
from pages.models import ComplianceBannerSettings, ComplianceBannerAcceptance
from django.utils.timezone import now

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

# ====================================================================
# function to serve the compliance banner management page

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def delayed_compliance(request):
    banner = ComplianceBannerSettings.objects.first()

    if request.method == 'POST':
        form = complianceBannerForm(request.POST, instance=banner)
        if form.is_valid():
            form.save()
            return redirect('compliance-banner-settings')
    else:
        form = complianceBannerForm(instance=banner)

    return render(request, 'pages/compliance-banner-settings.html', {
        'form': form,
    })

@login_required
def accept_compliance_banner(request):
    if request.method == "POST":
        banner = ComplianceBannerSettings.objects.filter(visible=True, start_date__lte=now(), end_date__gte=now()).first()
        if banner:
            ComplianceBannerAcceptance.objects.get_or_create(user=request.user, banner=banner)
            return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)