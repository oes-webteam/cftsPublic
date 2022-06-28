from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User as authUser
from django.forms.widgets import PasswordInput
from django.utils.translation import gettext_lazy as _
from pages.models import User, Network, Email
from django.forms import ModelForm
from crispy_forms.helper import FormHelper
from django.contrib.auth import authenticate
from crispy_forms.layout import Div, Submit, HTML
from cfts.settings import NETWORK, DEBUG


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
class userPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(userPasswordChangeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout.append(Submit('save', 'Save'))
        self.helper.layout.append(HTML('<a class="btn btn-danger" href="/frontend">Cancel</a>'))


class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    phone = forms.CharField(max_length=25, required=True)

    class Meta:
        model = authUser
        fields = ("username", 'first_name', 'last_name', "email", "phone", "password1", "password2")

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

    def check_duplicate(self, form, certInfo):
        if DEBUG == False:
            if certInfo['status'] == "validPKI":
                matchingUsers = User.objects.filter(user_identifier=certInfo['userHash'])
                if matchingUsers.count() != 0:
                    dupe = False
                    for user in matchingUsers:
                        if user.auth_user != None:
                            dupe = True

                    if dupe == True:
                        self.add_error(None, "Your " + NETWORK + " token is already tied to an account. If you forgot your password you can request a reset from the login page. If you believe this to be an error please contact us at the link below.")
            else:
                matchingUsers = authUser.objects.filter(email=form.get('email'))
                if matchingUsers.count() != 0:
                    self.add_error(None, "Your email is already tied to an account. If you forgot your password you can request a reset from the login page. If you believe this to be an error please contact us at the link below.")


class userInfoForm(ModelForm):
    source_email = forms.EmailField(max_length=75, required=True)
    phone = forms.CharField(max_length=50, required=True)
    org = forms.ChoiceField(choices=[
        ('None', '---------------------'),
        ('CENTCOM HQ', 'CENTCOM HQ'),
        ('AFCENT', 'AFCENT'),
        ('ARCENT', 'ARCENT'),
        ('MARCENT', 'MARCENT'),
        ('NAVCENT', 'NAVCENT'),
        ('SOCCENT', 'SOCCENT'),
        ('OTHER', 'OTHER - Describe')], required=True)
    other_org = forms.CharField(max_length=50, required=False)
    read_policy = forms.BooleanField()

    class Meta:
        model = User
        fields = ('name_first', 'name_last')

    def __init__(self, *args, **kwargs):
        networks = kwargs.pop('networks')
        user = kwargs.get('instance')
        email = Email.objects.get(email_id=user.source_email.email_id)

        super(userInfoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        self.fields['name_first'].label = 'First Name'
        self.fields['name_last'].label = 'Last Name'
        self.fields['source_email'].initial = email.address
        self.fields['source_email'].label = NETWORK + ' Email'
        self.fields['phone'].initial = user.phone
        self.fields['org'].initial = user.org
        self.fields['org'].label = "Organization"
        self.fields['other_org'].initial = user.other_org
        self.fields['other_org'].label = "Other Organization"
        self.fields['read_policy'].initial = user.read_policy
        self.fields['read_policy'].label = "I have read and agree to follow the Combined File Transfer Service policies"
        self.helper.layout.append(HTML(
            '<div style="width: 100%"><hr class="mt-2 mb-3" style="border-top-width: 3px; border-top-color: rgba(0, 0, 0, 0.2);"/><h3 class="mt-3">Destination Emails</h3><p class="mb-4">You can only submit transfer requests to networks you have a valid email for.</p></div>'))

        for network in networks:
            net = Network.objects.get(name=network)
            fieldName = net.name+' Email'
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

    def validate_form(self, form):
        for network in Network.objects.filter(visible=True):
            if form.get(network.name+' Email') == form.get('source_email'):
                self.add_error(network.name+' Email', "Destination email cannot be the same as " + NETWORK + " email")

        if form.get('org') == "None":
            self.add_error('org', "Select an organization")

        if form.get('org') == "OTHER" and form.get('other_org') == "":
            self.add_error('other_org', "List your organization")


class UsernameLookupForm(ModelForm):
    email = forms.EmailField(max_length=75, required=True)
    password = forms.CharField(widget=PasswordInput(), required=True)

    class Meta:
        model = authUser
        fields = ('email', 'password')

    def __init__(self, *args, **kwargs):
        super(UsernameLookupForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['email'].label = NETWORK + ' Email'
        self.fields['password'].label = 'Account Password'
        self.helper.layout.append(Submit('save', 'Search'))
        self.helper.layout.append(HTML('<a class="btn btn-danger" href="/frontend">Cancel</a>'))
