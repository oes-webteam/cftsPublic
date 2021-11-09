from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from pages.models import User as cftsUser, Network, Email
from django.forms import fields

class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    phone = forms.CharField(max_length=25, required=True)

    class Meta:
        model = User
        fields = ("username", 'first_name', 'last_name', "email", "phone", "password1", "password2")

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

    # def check_unique(self):
    #     print("checking for unique username")
    #     print("form username: " + str(self.cleaned_data['username']))
    #     try:
    #         user = User.objects.get(username__iexact=self.cleaned_data['username'])
    #         print("saved user username: " + str(user.username))
    #         raise self.ValidationError("Username already exists.")
    #     except:
    #         pass