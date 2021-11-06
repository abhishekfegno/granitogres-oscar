from django.forms import inlineformset_factory
from oscar.core.loading import get_class, get_model
from apps.catalogue.models import ProductAttribute
from apps.dashboard.catalogue.forms import ProductAttributesForm

ProductClass = get_model('catalogue', 'ProductClass')

ProductAttributesFormSet = inlineformset_factory(
    ProductClass,
    ProductAttribute,
    form=ProductAttributesForm,
    extra=3
)




