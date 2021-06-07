from oscarapi.basket import operations
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
from rest_framework import status
from rest_framework.response import Response
from oscar.apps.basket import signals


class AddProductView(CoreAddProductView):
    def validate(
            self, basket, product, quantity, options
    ):  # pylint: disable=unused-argument
        availability = basket.strategy.fetch_for_product(product).availability
        if quantity > 0:
            # check if product is available at all
            if not availability.is_available_to_buy:
                return False, availability.message

            current_qty = basket.product_quantity(product)
            desired_qty = current_qty + quantity

            # check if we can buy this quantity
            allowed, message = availability.is_purchase_permitted(desired_qty)
            if not allowed:
                return False, message

            # check if there is a limit on amount
            allowed, message = basket.is_quantity_allowed(desired_qty)
            if not allowed:
                return False, message
        else:
            current_qty = basket.product_quantity(product)
            if current_qty - quantity < 0:
                return False, "Item not in cart"
        return True, None

    def post(self, request, format=None):  # pylint: disable=redefined-builtin
        p_ser = self.add_product_serializer_class(
            data=request.data, context={"request": request}
        )
        if p_ser.is_valid():
            basket = operations.get_basket(request)
            product = p_ser.validated_data["url"]
            quantity = p_ser.validated_data["quantity"]
            options = p_ser.validated_data.get("options", [])

            basket_valid, message = self.validate(basket, product, quantity, options)
            if not basket_valid:
                return Response(
                    {"reason": message}, status=status.HTTP_406_NOT_ACCEPTABLE
                )
            current_qty = basket.product_quantity(product)
            desired_qty = current_qty + quantity
            if desired_qty < 0:
                quantity = -current_qty
            basket.add_product(product, quantity=quantity, options=options)
            signals.basket_addition.send(
                sender=self, product=product, user=request.user, request=request
            )

            operations.apply_offers(request, basket)
            ser = self.serializer_class(basket, context={"request": request})
            return Response(ser.data)

        return Response({"reason": p_ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE, )

