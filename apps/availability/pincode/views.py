from django.http import JsonResponse

# Create your views here.
from oscar.apps.dashboard.communications.views import ListView
from rest_framework.response import Response

from apps.api_set.serializers.mixins import ProductPriceFieldMixin
from apps.availability.pincode.facade import PincodeFacade
from apps.availability.signals import pincode_changed

from oscar.core.loading import get_model
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404

from apps.availability.models import PincodePartnerThroughModel
from apps.availability.utils import load_all_postal_code_in_district

Partner = get_model('partner', 'Partner')
PinCode = get_model('availability', 'PinCode')
Product = get_model('catalogue', 'Product')

NOT_DELIVERABLE = 'not_deliverable'
PARTNER_NOT_FOUND = 'partner_not_found'
PINCODE_REQUIRED = 'pincode_required'
DISTRICT_NOT_FOUND = 'district_not_found'
NO_COMMUNITIES_UNLOCKED = 'no_communities_unlocked'
PRODUCT_DOES_NOT_EXIST = 'product_does_not_exist'
AVAILABLE = 'available'


class PincodeSelector(ListView):
    template_name = 'availability/pincode/selector.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponse({'access': 'denied'})
        return super(PincodeSelector, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['partner_options'] = Partner.objects.values_list('id', 'name')
        kwargs['country_options'] = PinCode.get_root_nodes().values_list('id', 'name', 'code')
        return super(PincodeSelector, self).get_context_data(**kwargs)


@api_view()
def ajax_for_children(request, pk):
    if not request.user.is_superuser:
        return Response({'access': 'denied'}, status=403)
    object = get_object_or_404(PinCode, pk=pk)
    return Response(
        {'response': list(object.get_children().values('id', 'name', 'code'))}
    )


@api_view(['GET', 'POST'])
def load_page(request, partner, district):
    # pk of a district
    if not request.user.is_superuser:
        return Response({'access': 'denied'}, status=403)

    district_object = PinCode.objects.filter(pk=district).first()
    partner_object = Partner.objects.filter(pk=partner).first()
    out = {}
    if not district_object:
        out['error_code'] = DISTRICT_NOT_FOUND
        out['error'] = 'District does not exists'
        return Response(out, status=400)
    if not partner_object:
        out['error_code'] = PARTNER_NOT_FOUND
        out['error'] = 'Partner does not exists'
        return Response(out, status=400)

    communities = district_object.get_children()

    if not communities.exists():
        if request.method == 'GET':
            out['error_code'] = NO_COMMUNITIES_UNLOCKED
            out['error'] = 'You Have Not Unlocked Any Communities in this District!'
            return Response(out, status=400)
        else:
            load_all_postal_code_in_district(district_object)
        communities = district_object.get_children()
    postal = PinCode.objects.filter(path__startswith=district_object.path, depth=PinCode.POSTAL_CODE_DEPTH)

    out['communities'] = list(communities.values('id', 'name', 'path'))
    out['postal'] = list(postal.values('id', 'name', 'code', 'path'))
    out['partner_deliverable'] = list(partner_object.pincodes.all().values_list('id', flat=True))
    return Response(out,  status=200)


@api_view(['POST'])
def update_pincode(request, partner, **kwargs):
    """
    Maps The Partner to Pincodes where they deliver.

    ============================
    Usage : available only for superadmin via web. to update pincode.
    """
    if not request.user.is_superuser:
        return Response({'access': 'denied'}, status=403)

    out = {}
    partner_object = Partner.objects.filter(pk=partner).first()
    if not partner_object:
        out['error_code'] = PARTNER_NOT_FOUND
        out['error'] = 'Partner does not exists'
        return Response(out, status=400)
    PincodePartnerThroughModel.objects.filter(
        partner_id=partner,
        pincode__in=request.data['nondeliverable'] + request.data['deliverable']
    ).delete()
    # added = partner_object.pincodes.bulk_create(PinCode.objects.filter(request.data['deliverable']))

    PincodePartnerThroughModel.objects.bulk_create(
        [PincodePartnerThroughModel(partner_id=partner, pincode_id=pincode_id) for pincode_id in request.data['deliverable']]
    )
    out['status'] = True
    return Response(out, status=200)


@api_view(['GET'])
def set_pincode(request):
    """
    request : GET
    params : /../../?pincode=<pincode>
    RETURN : 'pincode' Is a deliverable location if 'status' => true

    Usage : available only for superadmin via web. to update pincode.
    """

    out = {'error': None, 'status': None}
    if not request.GET.get('pincode'):
        out['error'] = PINCODE_REQUIRED
        return Response(out, status=400)
    out['status'] = success = PincodeFacade.set_pincode(request, request.GET['pincode'])
    if not request.session.get('pincode') and request.user._profile and request.user._profile.pincode:
        request.session['pincode'] = request.user._profile.pincode.code
        pincode_changed.send(user=request.user, pincode=request.GET['pincode'])
    if not success:
        out['error'] = NOT_DELIVERABLE
    return Response(out, status=200 if success else 400)


@api_view(['GET'])
def check_availability(request):
    """
    request : GET
    params : /../../?pincode=<pincode>&product=<product>
    RETURN : 'pincode' Is a deliverable location if 'status' => true
    """
    if not request.user.is_authenticated:
        return Response({'access': 'denied'}, status=403)

    product_id = request.GET.get('product')
    pincode = request.GET.get('pincode')
    pin_object = PinCode.objects.filter(code=pincode).first()
    product = Product.objects.filter(id=product_id).first()
    out = {}

    if not pin_object or pin_object.partners.all().exists():
        out['status'] = NOT_DELIVERABLE
        out['status_text'] = f'This item is not deliverable to "{pincode}".'
        return Response(out, status=400)

    if not product:
        out['status'] = PRODUCT_DOES_NOT_EXIST
        out['status_text'] = f'Invalid Product ID'
        return Response(out, status=400)

    price_field_mixin = ProductPriceFieldMixin()
    price_field_mixin.context = {'request': request}
    out['price'] = price_field_mixin.get_price(product)
    return Response(out)





