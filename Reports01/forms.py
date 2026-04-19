from django import forms
# from .models import OPEX_Data, Expense_Heads, Course
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group

class UploadOPEXForm(forms.Form):
    opexfile = forms.FileField(label='Select OPEX Excel File')

class UploadExpenseHeads(forms.Form):
    glfile = forms.FileField(label='Select Expense Heads Excel File')

class UploadIncidents(forms.Form):
    incidentfile = forms.FileField(label='Select Incident Excel File')

class UploadVendor(forms.Form):
    vendorfile = forms.FileField(label='Select Vendor Details Excel File')

class UploadRoutine(forms.Form):
    routinefile = forms.FileField(label='Select Routine Waste Disposal Excel File')

class UploadNonRoutine(forms.Form):
    nonroutinefile = forms.FileField(label='Select Non-Routine Waste Disposal Excel File')

class UploadEWaste(forms.Form):
    ewastefile = forms.FileField(label='Select Authorised Users Excel File')

class UploadLocation(forms.Form):
    locationfile = forms.FileField(label='Select Location Details Excel File')

class UploadAuthUser(forms.Form):
    userfile = forms.FileField(label='Select Authorised Users Excel File')

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    email = forms.EmailField(max_length=254, required=False, help_text='Optional.')
    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

class UserUpdateForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.exclude(name__in=['Site-Admin']),
        widget = forms.CheckboxSelectMultiple, required=False,
    )
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'is_active', 'groups'
        ]

