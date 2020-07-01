from django.conf import settings
import requests

FAST_2_SMS_BASE_URL = "https://www.fast2sms.com/dev/bulk"

def format_otp_message(otp):
    return f"Your Verification Code is : {otp}; this will be active for {settings.OTP_EXPIRY / 15} minute(s) - WoodN\'Cart"


def send_otp(phone_no: str, otp):

    querystring = {
        "authorization": settings.FAST_2_SMS_API_KEY,
        "sender_id": settings.FAST_2_SMS_SENDER_ID,
        "language": "english",
        "route": "qt",
        "numbers": phone_no,
        "message": settings.FAST_2_SMS_TEMPLATE_ID,
        "variables": "{AA}",
        "variables_values": otp
    }
    headers = {'cache-control': "no-cache"}
    response = requests.request("GET", FAST_2_SMS_BASE_URL, headers=headers, params=querystring)
    print(response.text)
    return True


def send_welcome_message(phone_no):
    # querystring = {
    #     "authorization": settings.FAST_2_SMS_API_KEY,
    #     "sender_id": settings.FAST_2_SMS_SENDER_ID,
    #     "language": "english",
    #     "route": "qt",
    #     "numbers": phone_no,
    #     "message": settings.FAST_2_SMS_TEMPLATE_ID,
    #     "variables": "{AA}",
    #     "variables_values": otp
    # }
    # headers = {'cache-control': "no-cache"}
    # response = requests.request("GET", FAST_2_SMS_BASE_URL, headers=headers, params=querystring)
    # print(response.text)
    # return True
    return


