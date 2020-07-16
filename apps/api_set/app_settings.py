from django.conf import settings

OTP_LENGTH = getattr(settings, 'OTP_LENGTH', 4) - 1
OTP_MIN_VALUE = 10 ** OTP_LENGTH
OTP_MAX_VALUE = (10 ** (OTP_LENGTH + 1)) - 1
OTP_EXPIRY = getattr(settings, 'OTP_EXPIRY', 1500)

settings_mob_validator = getattr(settings, 'MOBILE_NUMBER_VALIDATOR', {}).get('LENGTH', 10)
DEFAULT__MOBILE_NUMBER_VALIDATOR = {
    'LENGTH': 10,
    'REGEX': r'{}'.format(f"^\d{{{settings_mob_validator}}}$"),
    'MAX_RETRIES': 3,
}
MOBILE_NUMBER_VALIDATOR = {**DEFAULT__MOBILE_NUMBER_VALIDATOR, **settings.MOBILE_NUMBER_VALIDATOR}







