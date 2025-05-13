# decorators
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import permission_required

from pages.views.auth import superUserCheck, staffCheck
from django.shortcuts import render, redirect, get_object_or_404
from pages.forms import complianceBannerForm
from pages.models import ComplianceBannerSettings

# ====================================================================
# function to serve the compliance banner management page

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def delayed_compliance(request):
    # Get the first (or only) compliance banner
    banner = ComplianceBannerSettings.objects.first()

    if request.method == 'POST':
        form = complianceBannerForm(request.POST, instance=banner)
        if form.is_valid():
            form.save()
            return redirect('delayed_compliance')  # Redirect to the same page after saving
    else:
        form = complianceBannerForm(instance=banner)

    return render(request, 'pages/compliance-banner-settings.html', {'form': form})