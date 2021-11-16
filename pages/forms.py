from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User as authUser
from pages.models import User, Network, Email
from django.forms import ModelForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Submit
from cfts.settings import NETWORK

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

class userInfoForm(ModelForm):
    source_email = forms.EmailField(max_length=50, required=True)
    phone = forms.CharField(max_length=50 ,required=True)
    class Meta:
        model = User
        fields = ('name_first', 'name_last')

    def __init__(self, *args, **kwargs):
        networks = kwargs.pop('networks')
        user = kwargs.get('instance')
        email = Email.objects.get(email_id=user.source_email.email_id)
        
        super(userInfoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['source_email'].initial = email.address
        self.fields['source_email'].label = NETWORK + ' Email'
        self.fields['phone'].initial = user.phone

        for network in networks:
            net = Network.objects.get(name=network)
            fieldName = net.name+' Email'
            self.fields[fieldName] = forms.EmailField(max_length=50 ,required=False)
            self.fields[fieldName].label = fieldName
            try:
                networkEmail = user.destination_emails.get(network__name=network)
                self.fields[fieldName].initial = networkEmail.address
            except Email.DoesNotExist:
                pass
            self.helper.layout.append(fieldName)

        self.helper.all().wrap_together(Div, css_class="inline-fields")
        self.helper.layout.append(Submit('save','Save'))