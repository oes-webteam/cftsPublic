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
        # Get the current user and compliance banner
        try:
            user = User.objects.get(auth_user=request.user)  # Retrieve the custom User instance
        except User.DoesNotExist:
            return JsonResponse({"status": "error", "message": "User not found."}, status=400)

        banner = ComplianceBannerSettings.objects.filter(visible=True).first()

        if banner:
            # Record the user's acceptance
            ComplianceBannerAcceptance.objects.update_or_create(
                user=user,
                banner=banner,
                defaults={'last_accepted': now()}
            )
            return JsonResponse({"status": "success"})
        else:
            return JsonResponse({"status": "error", "message": "No active compliance banner found."}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)