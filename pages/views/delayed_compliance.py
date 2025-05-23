# decorators
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import permission_required

from pages.views.auth import superUserCheck, staffCheck
from django.shortcuts import render, redirect, get_object_or_404
from pages.forms import complianceBannerForm
from pages.models import ComplianceBannerSettings, ComplianceBannerAcceptance, User
from django.utils.timezone import now

from django.http import JsonResponse
from django.views.decorators.http import require_POST
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
@require_POST
def accept_compliance_banner(request):
    try:
        # Get the custom user object
        user = User.objects.get(auth_user=request.user)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=400)

    try:
        # Get the active compliance banner
        banner = ComplianceBannerSettings.objects.get(visible=True)
    except ComplianceBannerSettings.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'No active compliance banner found.'}, status=400)

    # Record acceptance
    ComplianceBannerAcceptance.objects.get_or_create(user=user, banner=banner)
    return JsonResponse({'status': 'success'})


def compliance_banner_settings(request):
    # Get the current settings instance, or create one if it doesn't exist
    banner, created = ComplianceBannerSettings.objects.get_or_create(pk=1)  # or your logic

    if request.method == "POST":
        form = ComplianceBannerSettingsForm(request.POST, instance=banner)
        if form.is_valid():
            form.save()
    else:
        form = ComplianceBannerSettingsForm(instance=banner)

    return render(request, "pages/compliance-banner-settings.html", {"form": form})