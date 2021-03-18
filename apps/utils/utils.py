from osc import settings


def get_statuses(code: int):
    """
    This function will return a list of items
    """
    _status_set = {
        1: settings.ORDER_STATUS_PLACED,                # Placed
        2: settings.ORDER_STATUS_CONFIRMED,             # Order Confirmed
        4: settings.ORDER_STATUS_OUT_FOR_DELIVERY,      # Out For Delivery
        8: settings.ORDER_STATUS_DELIVERED,             # Delivered
        16: settings.ORDER_STATUS_RETURN_REQUESTED,     # Return Requested
        32: settings.ORDER_STATUS_RETURN_APPROVED,      # Return Approved
        64: settings.ORDER_STATUS_RETURNED,             # Returned
        128: settings.ORDER_STATUS_CANCELED,            # Canceled

        # oscar api checkout
        256: settings.ORDER_STATUS_PENDING,             # Placed
        512: settings.ORDER_STATUS_PAYMENT_DECLINED,    # Payment Declined
    }
    statuses = []
    next_greatest_factor = max(list(_status_set.keys()))

    """
    ''' *** VALIDATION IF Input expects to be string*** '''
    # if not code.isdigit() or int(code) >= next_greatest_factor * 2:
    #     return code  # raise NotACode("This is not a valid key!")
    # code = int(code)
    """

    while next_greatest_factor:
        if code & next_greatest_factor:  # finding if number is a factor using  "Bitwise AND Operator"
            statuses.append(
                _status_set[next_greatest_factor]
            )  # if so; add corresponding value to the list to be returned!
        next_greatest_factor //= 2  # get next factor
    # statuses.reverse()
    return statuses

