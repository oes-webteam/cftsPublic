from pages.models import ComplianceBannerSettings, ComplianceBannerAcceptance, User  
from django.utils.timezone import now

class ComplianceBannerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                custom_user = User.objects.get(auth_user=request.user)
            except User.DoesNotExist:
                custom_user = None

            banner = ComplianceBannerSettings.objects.filter(
                visible=True,
                start_date__lte=now(),
                end_date__gte=now()
            ).first()

            if banner and custom_user:
                has_accepted = ComplianceBannerAcceptance.objects.filter(user=custom_user, banner=banner).exists()
                request.show_compliance_banner = True
                request.compliance_banner = {
                    'text': banner.compliance_text,
                    'button_text': "Close" if has_accepted else banner.accept_button_text,
                    'has_accepted': has_accepted
                }
            else:
                request.show_compliance_banner = False
        else:
            request.show_compliance_banner = False

        return self.get_response(request)