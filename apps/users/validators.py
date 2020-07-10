from django.core import validators
from django.utils.deconstruct import deconstructible


@deconstructible
class UnicodeMobileNumberValidator(validators.RegexValidator):
    regex = r'^\d{10}$'
    message = 'Enter a valid mobile number. '
    flags = 0
    code = 'invalid_mobile_number'
