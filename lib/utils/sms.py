from django.conf import settings
import requests

FAST_2_SMS_BASE_URL = "https://www.fast2sms.com/dev/bulkV2"


def send_sms_for_order_status_change(order):
    message = settings.SMS_MESSAGES.get(({
        settings.ORDER_STATUS_PLACED: None,
        settings.ORDER_STATUS_CONFIRMED: 'ORDER_CONFIRMED',
        settings.ORDER_STATUS_PACKED: None,
        settings.ORDER_STATUS_SHIPPED: 'ORDER_SHIPPED',
        settings.ORDER_STATUS_OUT_FOR_DELIVERY: None,
        settings.ORDER_STATUS_DELIVERED: 'ORDER_DELIVERED',
        settings.ORDER_STATUS_RETURN_REQUESTED: None,
        settings.ORDER_STATUS_REFUND_APPROVED: 'RETURN_INITIATED',
        settings.ORDER_STATUS_REPLACEMENT_APPROVED: 'REPLACEMENT_INITIATED',
        settings.ORDER_STATUS_RETURNED: 'RETURNED',
        settings.ORDER_STATUS_REPLACED: None,
        settings.ORDER_STATUS_CANCELED: 'ORDER_CANCELED',
        settings.ORDER_STATUS_PAYMENT_DECLINED: 'PAYMENT_DECLINED',
    }).get(order.status))
    try:
        mob_no = ",".join([num[-10:] for num in order.user.mobile if num])
        mob_no = mob_no.replace(",", "")
        if message and mob_no:
            print("calling send_p_sms", message, mob_no)
            return send_p_sms(mob_no, message=message.format(order=order))
    except Exception as e:
        try:
            order.notes.create(user=None, message='Could not send SMS', note_type='Info')
        except:
            pass


class Fast2SMS:
    def __init__(self):
        self.url = FAST_2_SMS_BASE_URL

    def send_p_sms(self, phone_no, message):
        url = self.url

        querystring = {
            "authorization": settings.FAST_2_SMS_API_KEY,
            # "sender_id": getattr(settings, 'FAST_2_SMS_SENDER_ID', "SMSINI"),
            "sender_id": "TXTIND",
            # "language": "english",
            "route": "v3",
            "numbers": phone_no,
            "message": message,
        }
        headers = {'cache-control': "no-cache"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        print(response.text, "$$$ sent $$$$")
        return True

    def send_qt_sms(self, phone_no, message):
        url = self.url

        querystring = {
            "authorization": settings.FAST_2_SMS_API_KEY,
            # "sender_id": "TXTIND",
            "sender_id": settings.FAST_2_SMS_SENDER_ID,
            "language": "english",
            "route": "dlt",
            "numbers": phone_no,
            "message": settings.FAST_2_SMS_TEMPLATE_ID,
            "variables_values": "%s" % message
        }
        headers = {'cache-control': "no-cache"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        print(response.text)
        return True


def send_p_sms(phone_no, message):
    print("calling fast 2 class")
    return Fast2SMS().send_p_sms(phone_no, message)


def send_qt_sms(phone_no, message):
    return Fast2SMS().send_qt_sms(phone_no, message)


######################################################################


# def _send_p_sms(phone_no, message):
#     url = "https://www.fast2sms.com/dev/bulk"
#
#     querystring = {
#         "authorization": settings.FAST_2_SMS_API_KEY,
#         "sender_id": getattr(settings, 'FAST_2_SMS_SENDER_ID', "SMSINI"),
#         "language": "english",
#         "route": "p",
#         "numbers": phone_no,
#         "message": message,
#     }
#     headers = {'cache-control': "no-cache"}
#     response = requests.request("GET", url, headers=headers, params=querystring)
#     print(response.text)
#     return True
#
#
# def _send_qt_sms(phone_no, message):
#     url = "https://www.fast2sms.com/dev/bulk"
#
#     querystring = {
#         "authorization": settings.FAST_2_SMS_API_KEY,
#         "sender_id": "BathxB",
#         "language": "english",
#         "route": "qt",
#         "numbers": phone_no,
#         "message": settings.FAST_2_SMS_TEMPLATE_ID,
#         "variables": "{BB}",
#         "variables_values": "%s" % message
#     }
#     headers = {'cache-control': "no-cache"}
#     response = requests.request("GET", url, headers=headers, params=querystring)
#     print(response.text)
#     return True

# ###################################################################################################3


def format_otp_message(otp):
    return f"Your Verification Code is : {otp}; this will be active for {settings.OTP_EXPIRY / 15} minute(s) - WoodN\'Cart"


def send_otp(phone_no: str, otp):

    querystring = {
        "authorization": settings.FAST_2_SMS_API_KEY,
        # "sender_id": settings.FAST_2_SMS_SENDER_ID,
        # "language": "english",
        "route": "otp",
        "numbers": phone_no,
        # "message": settings.FAST_2_SMS_TEMPLATE_ID,
        # "message": f"{otp} is your OTP to login to ABCHAUZ.COM",
        "variables_values": f"Use {otp} to login at ABCHAUZ"
    }
    headers = {'cache-control': "no-cache"}
    try:
        response = requests.request("GET", FAST_2_SMS_BASE_URL, headers=headers, params=querystring)
        return True
    except Exception as e:
        return False


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


