from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User as authUser
from django.utils.translation import gettext_lazy as _
from pages.models import User, Network, Email
from django.forms import ModelForm
from crispy_forms.helper import FormHelper
from django.contrib.auth import authenticate
from crispy_forms.layout import Div, Submit, HTML
from cfts.settings import NETWORK, ALLOWED_DOMAIN



class userLogInForm(AuthenticationForm):
    error_messages = {
        "invalid_login": _(
            "Please enter a correct %(username)s and password. Note that both "
            "fields are case-sensitive."
        ),
        "inactive": _("Your account is inactive."),
    }

    def __init__(self, *args, **kwargs):
        super(userLogInForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout.append(Submit('login', 'Login'))

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )
            if self.user_cache is None:
                try:
                    if self.confirm_login_allowed(authUser.objects.get(username=username)) == None:
                        raise self.get_invalid_login_error()
                except authUser.DoesNotExist:
                    raise self.get_invalid_login_error()

        return self.cleaned_data


class userInfoForm(ModelForm):
    source_email = forms.EmailField(max_length=75, required=True)
    phone = forms.CharField(max_length=50, required=True)
    org = forms.ChoiceField(choices=[
        ('None', '---------------------'),
        ('CENTCOM HQ', 'CENTCOM HQ'),
        ('AFCENT', 'AFCENT'),
        ('AFRICOM', 'AFRICOM'),
        ('ARCENT', 'ARCENT'),
        ('CYBERCOM', 'CYBERCOM'),
        ('EUCOM', 'EUCOM'),
        ('INDOPACOM', 'INDOPACOM'),
        ('JCS', 'JCS'),
        ('MARCENT', 'MARCENT'),
        ('NAVCENT', 'NAVCENT'),
        ('NORTHCOM', 'NORTHCOM'),
        ('SOCCENT', 'SOCCENT'),
        ('SOCOM', 'SOCOM'),
        ('SOUTHCOM', 'SOUTHCOM'),
        ('SPACECOM', 'SPACECOM'),
        ('STRATCOM', 'STRATCOM'),
        ('TRANSCOM', 'TRANSCOM'),
        ('USA', 'USA'),
        ('USAF', 'USAF'),
        ('USCG', 'USCG'),
        ('USMC', 'USMC'),
        ('USN', 'USN'),
        ('USSF', 'USSF'),
        ('OTHER', 'OTHER > DIR/UNIT - Describe -> ')], required=True)
    other_org = forms.CharField(max_length=50, required=False)
    read_policy = forms.BooleanField()

    class Meta:
        model = User
        fields = ('name_first', 'name_last')

    def __init__(self, *args, **kwargs):
        networks = kwargs.pop('networks')
        user = kwargs.get('instance')
        try:
            email = Email.objects.get(email_id=user.source_email.email_id).address
        except:
            email = ""

        super(userInfoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        self.fields['name_first'].label = 'First Name'
        self.fields['name_last'].label = 'Last Name'
        self.fields['source_email'].initial = email
        self.fields['source_email'].label = NETWORK + ' Email'
        self.fields['phone'].initial = user.phone
        self.fields['org'].initial = user.org
        self.fields['org'].label = "Organization"
        self.fields['other_org'].initial = user.other_org
        self.fields['other_org'].label = "DIR/UNIT"
        self.fields['read_policy'].initial = user.read_policy
        self.fields['read_policy'].label = "I have read and agree to follow the Combined File Transfer Service policies"
        self.helper.layout.append(HTML(
            '<div style="width: 100%"><hr class="mt-2 mb-3" style="border-top-width: 3px; border-top-color: rgba(0, 0, 0, 0.2);"/><h3 class="mt-3">Destination Emails</h3><p class="mb-4">You can only submit transfer requests to networks you have a valid email for.</p></div>'))

        for network in networks:
            net = Network.objects.get(name=network)
            fieldName = net.name + ' Email'
            self.fields[fieldName] = forms.EmailField(max_length=75, required=False)
            self.fields[fieldName].label = fieldName
            try:
                networkEmail = user.destination_emails.get(network__name=network)
                self.fields[fieldName].initial = networkEmail.address
            except Email.MultipleObjectsReturned:
                networkEmail = user.destination_emails.filter(network__name=network)
                self.fields[fieldName].initial = networkEmail[0].address
            except Email.DoesNotExist:
                pass
            self.helper.layout.append(fieldName)

        self.helper.all().wrap_together(Div, css_class="inline-fields")
        self.helper.layout.append(Submit('save', 'Save'))

    def clean_source_email(self):
        source_email = self.cleaned_data.get('source_email')

        def is_valid_email(email: str, allowed_domain: str) -> bool:
            if "@" not in email or email.split("@")[1].strip() == "":
                return False

            domain = email.split("@")[-1].strip()
            if "." not in domain:
                return False

            base_domain = ".".join(domain.split(".")[-2:]).lower()
            return base_domain == allowed_domain.lower()

        if not is_valid_email(source_email, ALLOWED_DOMAIN):
            raise forms.ValidationError(f"Email must be from the {ALLOWED_DOMAIN} domain.")

        return source_email

    def clean(self):
        cleaned_data = super().clean()
        source_email = cleaned_data.get('source_email')
        org = cleaned_data.get('org')
        other_org = cleaned_data.get('other_org')

        # Validate organization fields separately
        if org == "None":
            self.add_error('org', "Please select an organization")
        if org == "OTHER" and not other_org:
            self.add_error('other_org', "Please list your DIR/UNIT")
        
        # Loop over each visible network and validate its email field
        for network in Network.objects.filter(visible=True):
            field_name = f"{network.name} Email"
            network_email = cleaned_data.get(field_name)
            
            # If the network email is provided and it matches the source email,
            # add an error to that field.
            if network_email and network_email == source_email:
                self.add_error(
                    field_name,
                    f"Destination email for {network.name} cannot be the same as the source email."
                )
        
        return cleaned_data
