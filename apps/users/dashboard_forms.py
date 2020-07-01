from django import forms
from django.utils.translation import pgettext_lazy

from apps.availability.models import PinCode
from apps.users.models import UserProfile


class DealerRegistrationSearchForm(forms.Form):
    email = forms.CharField(required=False, label="Email")
    mobile = forms.CharField(required=False, label="Mobile")
    name = forms.CharField(required=False, label=pgettext_lazy("User's name", "Name"))
    gst_number = forms.CharField(required=False, label="GST Number")
    pincode = forms.CharField(required=False, label="Pin Code")


class DealerRegistrationForm(forms.ModelForm):
    pincode = forms.ModelChoiceField(queryset=PinCode.objects.filter(depth=PinCode.POSTAL_CODE_DEPTH),)

    class Meta:
        model = UserProfile
        exclude = []
        # exclude = ['user']



