from oscar.core.loading import get_model

PinCode = get_model('availability', 'PinCode')


class PincodeFacade(object):

    @classmethod
    def set_pincode(cls, request, pincode):
        pin = PinCode.objects.filter(code=pincode).first()
        if pin:
            cls.set_session(request, pincode)
            return True
        else:
            cls.set_session(request, None)
        return False

    @staticmethod
    def set_session(request, pincode):
        request.session['pincode'] = pincode

    # @staticmethod
    # def set_cookie(response, pincode):
    #     existing_cookie = response.COOKIES.get('pincode', [])
    #     if type(existing_cookie) is list:
    #         existing_cookie.append(pincode)
    #         response.set_cookie('pincode', existing_cookie)
    #     else:
    #         response.set_cookie('pincode', [pincode, ])
    #
    #
