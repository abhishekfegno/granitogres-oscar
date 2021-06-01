from oscarapi.utils.loading import get_api_classes

# (
#     CoreAddProductView,
# ) = get_api_classes(
#     "views.basket",
#     [
#         "AddProductView",
#     ]
# )
from oscarapi.views.basket import AddProductView as CoreAddProductView


class AddProductView(CoreAddProductView):
    pass
