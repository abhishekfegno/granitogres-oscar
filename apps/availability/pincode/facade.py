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
