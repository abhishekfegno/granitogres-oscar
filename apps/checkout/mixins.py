from oscar.apps.checkout.mixins import OrderPlacementMixin as CoreOrderPlacementMixin


class OrderPlacementMixin(CoreOrderPlacementMixin):

    def get_message_context(self, order, code=None):
        super().get_message_context(order, code)
        ctx = {
                    'orderID': order.id,
                    'shipping_address': order.shipping_address,
                    'date_of_order': order.date_placed,
                    'products': {i.id: {'image': i.product.primary_image(),
                                        'name': i.product.name,
                                        'quantity': i.quantity,
                                        'price': i.product.effective_price,
                                        'total': i.line_price_incl_tax,
                                        } for i in order.lines.all()},
                    'total': order.total_incl_tax,
                }
        return ctx