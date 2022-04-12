from django import forms

from apps.dashboard.custom.models import Brochure
from apps.users.models import User


class DeliveryBoyRegistrationForm(forms.Form):

    first_name = forms.CharField()
    mobile = forms.CharField(max_length=10, min_length=10, required=True)

    def clean_mobile(self, mobile):
        qs = User.objects.filter(username=mobile)
        if qs.exists():
            raise forms.ValidationError("Mobile number already exists in our records. "
                                        "If delivery boy is an existing User, ")
        return mobile


class BrochureForm(forms.ModelForm):
    class Meta:
        model = Brochure
        fields = ('name', 'image')



