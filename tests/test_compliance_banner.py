import pytest
from django.test import TestCase
from django.utils.timezone import now, timedelta
from pages.models import ComplianceBannerSettings, ComplianceBannerAcceptance
from django.contrib.auth.models import User

@pytest.fixture
def compliance_banner(db):
    return ComplianceBannerSettings.objects.create(
        compliance_text="Test compliance message",
        visible=True,
        start_date=now() - timedelta(days=1),
        end_date=now() + timedelta(days=1),
    )

def test_banner_visibility_within_timeframe(compliance_banner):
    assert compliance_banner.visible is True
    assert compliance_banner.start_date <= now() <= compliance_banner.end_date

def test_banner_not_visible_outside_timeframe(db):
    banner = ComplianceBannerSettings.objects.create(
        compliance_text="Test compliance message",
        visible=True,
        start_date=now() + timedelta(days=1),  # Future start date
        end_date=now() + timedelta(days=2),
    )
    assert banner.start_date > now()

def test_user_acceptance(user, compliance_banner):
    # Simulate user accepting the banner
    acceptance = ComplianceBannerAcceptance.objects.create(user=user, banner=compliance_banner)
    assert acceptance.user == user
    assert acceptance.banner == compliance_banner
    assert acceptance.accepted_at is not None

    from pages.middleware import ComplianceBannerMiddleware
from django.test import RequestFactory

@pytest.fixture
def request_factory():
    return RequestFactory()

def test_middleware_shows_banner(request_factory, user, compliance_banner):
    request = request_factory.get("/")
    request.user = user

    middleware = ComplianceBannerMiddleware(lambda req: None)
    middleware(request)

    assert request.show_compliance_banner is True
    assert request.compliance_banner["text"] == compliance_banner.compliance_text
    assert request.compliance_banner["button_text"] == "Accept"

def test_middleware_hides_banner_if_not_visible(request_factory, user):
    request = request_factory.get("/")
    request.user = user

    ComplianceBannerSettings.objects.create(
        compliance_text="Test compliance message",
        visible=False,  # Banner is not visible
        start_date=now() - timedelta(days=1),
        end_date=now() + timedelta(days=1),
    )

    middleware = ComplianceBannerMiddleware(lambda req: None)
    middleware(request)

    assert request.show_compliance_banner is False

def test_reset_acceptance(user, compliance_banner):
    # User accepts the banner
    ComplianceBannerAcceptance.objects.create(user=user, banner=compliance_banner)

    # Reset the banner
    compliance_banner.visible = False
    compliance_banner.save()

    # Ensure acceptances are cleared
    assert ComplianceBannerAcceptance.objects.filter(banner=compliance_banner).count() == 0