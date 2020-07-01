from django import forms


class StripeTokenForm(forms.Form):
    stripeEmail = forms.EmailField(widget=forms.HiddenInput())
    stripeToken = forms.CharField(widget=forms.HiddenInput())
    stripeTokenType = forms.CharField(widget=forms.HiddenInput(), required=False)


class RazorPayTokenForm(forms.Form):
    razorpay_payment_id = forms.CharField(widget=forms.HiddenInput())




