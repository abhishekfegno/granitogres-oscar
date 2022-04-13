from django import forms
from django.forms import modelformset_factory

from apps.dashboard.custom.models import Brochure, Gallery, Album
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
        fields = ('name', 'image', 'file', 'type')


class GalleryForm(forms.ModelForm):
    # album_images = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['album_images'].queryset = Album.objects.all()
        # self.fields['album_images'].required = False

    class Meta:
        model = Gallery
        fields = ('title', 'description', 'image')


# AlbumFormset = modelformset_factory(Album, fields=('image',), extra=2)

class AlbumForm(forms.ModelForm):

    class Meta:
        model = Album
        fields = ('image',)
