import os

from oscar.defaults import *

PINCODE = 'pincode'
GEOLOCATION = 'geolocation'

LOCATION_FETCHING_MODE_SET = [PINCODE, GEOLOCATION]

LOCATION_FETCHING_MODE = PINCODE

DEFAULT_LOCATION_NAME = "Deliverable"

OSCARAPI_OVERRIDE_MODULES = ["apps.mod_oscarapi"]

OSCARAPI_BLOCK_ADMIN_API_ACCESS = True
OSCAR_MAX_PER_LINE_QUANTITY = 10

OSCAR_DEFAULT_CURRENCY = 'INR'
OSCAR_SHOP_NAME = 'ABCHAUZ'
OSCAR_SHOP_TAGLINE = "House of Homes"
OSCAR_HOMEPAGE = reverse_lazy('catalogue:index')
OSCAR_ACCOUNTS_REDIRECT_URL = 'customer:profile-view'
OSCAR_RECENTLY_VIEWED_PRODUCTS = 20
OSCAR_RECENTLY_VIEWED_COOKIE_LIFETIME = 604800  # 1 week
OSCAR_RECENTLY_VIEWED_COOKIE_NAME = 'oscar_history'
OSCAR_HIDDEN_FEATURES = ['reviews', ]

# PAGINATION
OSCAR_PRODUCTS_PER_PAGE = 20
OSCAR_OFFERS_PER_PAGE = 20
OSCAR_REVIEWS_PER_PAGE = 20
OSCAR_NOTIFICATIONS_PER_PAGE = 20
OSCAR_EMAILS_PER_PAGE = 20
OSCAR_ORDERS_PER_PAGE = 20
OSCAR_ADDRESSES_PER_PAGE = 20
OSCAR_STOCK_ALERTS_PER_PAGE = 20
OSCAR_DASHBOARD_ITEMS_PER_PAGE = 30

_ = lambda x: x

OSCAR_DASHBOARD_DEFAULT_ACCESS_FUNCTION = 'oscar.apps.dashboard.nav.default_access_fn'

OSCAR_ALLOW_ANON_REVIEWS = False
OSCAR_MODERATE_REVIEWS = False

OSCAR_EAGER_ALERTS = True
OSCAR_SEND_REGISTRATION_EMAIL = True
OSCAR_FROM_EMAIL = 'no-reply@grocery.com'
OSCAR_OFFERS_INCL_TAX = False

OSCAR_MISSING_IMAGE_URL = 'image_not_found.jpg'
MISSING_BANNER_URL = 'banner.jpg'
OSCAR_GOOGLE_ANALYTICS_ID = None

# Other statuses
ORDER_STATUS_PLACED = 'Placed'
ORDER_STATUS_CONFIRMED = 'Order Confirmed'
ORDER_STATUS_PACKED = 'Packed'
ORDER_STATUS_SHIPPED = 'Shipped'
ORDER_STATUS_OUT_FOR_DELIVERY = 'Out For Delivery'
ORDER_STATUS_DELIVERED = 'Delivered'
ORDER_STATUS_RETURN_REQUESTED = 'Return Requested'
ORDER_STATUS_RETURN_APPROVED = 'Return Approved'
ORDER_STATUS_RETURNED = 'Returned'
ORDER_STATUS_REFUND_APPROVED = 'Return Pickup Initiated'
ORDER_STATUS_REPLACEMENT_APPROVED = 'Replacement Pickup Initiated'
ORDER_STATUS_REPLACED = 'Returned and Replacement Initiated'
ORDER_STATUS_CANCELED = 'Canceled'

# Needed by oscarapicheckout
ORDER_STATUS_PENDING = 'Placed'
ORDER_STATUS_PAYMENT_DECLINED = 'Payment Declined'
ORDER_STATUS_AUTHORIZED = ORDER_STATUS_PENDING
OSCAR_INITIAL_ORDER_STATUS = ORDER_STATUS_PENDING
OSCARAPI_INITIAL_ORDER_STATUS = ORDER_STATUS_PENDING
OSCAR_INITIAL_LINE_STATUS = ORDER_STATUS_PENDING

admin_or_staff = lambda user, url_name, url_args, url_kwargs: user.is_staff or user.is_superuser

OSCAR_ORDER_STATUS_UNTIL_DELIVER = [
    (1, ORDER_STATUS_PLACED),
    (2, ORDER_STATUS_CONFIRMED),
    (3, ORDER_STATUS_PACKED),
    (4, ORDER_STATUS_SHIPPED),
    (5, ORDER_STATUS_OUT_FOR_DELIVERY),
    (6, ORDER_STATUS_DELIVERED),
]

OSCAR_ORDER_STATUS_PIPELINE = {

    # 'Pending': ('Order Confirmed', 'Canceled', 'Pending', 'Payment Declined'),
    # admin / user can cancel an order / an item

    'Placed': ('Order Confirmed', 'Payment Declined', 'Canceled'),  # admin / user can cancel an order / an item
    'Order Confirmed': ('Packed', 'Out For Delivery', 'Delivered', 'Canceled'),  # only admin can set these statuses
    'Packed': ('Shipped', 'Out For Delivery', 'Delivered', 'Canceled'),  # only admin can set these statuses
    'Shipped': ('Out For Delivery', 'Delivered', 'Canceled'),  # only admin can set these statuses
    'Out For Delivery': ('Delivered', 'Canceled'),  # only admin can set these statuses
    'Delivered': ('Return Requested', ),
    'Return Requested': ('Return Approved', ),
    'Return Approved': ('Returned', ),
    'Payment Declined': (),
    'Canceled': (),
}

OSCAR_USER_CANCELLABLE_ORDER_STATUS = (
    'Placed', 'Order Confirmed', 'Packed', 'Shipped',  'Out For Delivery',
)

EMAIL_MESSAGES = {
    'CONFIRMED': "CONFIRMED: Your Order #{order.number} for {order.num_lines} item(s) from Abchauz is confirmed. \n"
                 "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'SHIPPED'   : "SHIPPED: Your Order #{order.number} for {order.num_lines} item(s) from Abchauz is shipped. \n"
                  "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'PLACED'   : "PLACED: Your Order #{order.number} for {order.num_lines} item(s) from Abchauz is placed. \n"
                 "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'DELIVERED' : "DELIVERED: Your Order #{order.number} for {order.num_lines} item(s) from Abchauz is delivered. \n"
                  "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'CANCELED' : "CANCELED: Your Order #{order.number} for {order.num_lines} item(s) from Abchauz is confirmed. \n"
                 "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'PAYMENT_RECEIVED': "RECEIVED: Your Payment of Rs.{order.total_incl_tax}/- against Order #{order.number} is RECEIVED.",
    'PAYMENT_DECLINED': "DECLINED: Your Payment of Rs.{order.total_incl_tax}/- against Order #{order.number} is DECLINED.",

    'PAYMENT_REFUNDED': "REFUNDED: Your Payment of Rs.{refund_amount}/- against Order #{order.number} is Refunded.\n"
                        "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'RETURN_INITIATED': "RETURN: Return Request against your Order #{order.number} is Initiated.\n"
                        "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'REPLACEMENT_INITIATED': "REPLACEMENT: Replacement Request against your Order #{order.number} is Initiated.\n"
                             "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'RETURNED'         : "RETURND: Your Order #{order.number} is Returned.\n"
                         "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'RETURN_REJECTED' : "RETURN: Your Return Request Against Order #{order.number} could not be processed.\n"
                        "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'CANCELED': "ITEM CANCEL: {line.product.title} Has been Cancelled from Order #{order.number}.\n"
                "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",
}

OSCAR_SEND_EMAIL_ORDER_STATUS = (
    ORDER_STATUS_PLACED, ORDER_STATUS_CONFIRMED, ORDER_STATUS_PACKED, ORDER_STATUS_SHIPPED,
    ORDER_STATUS_OUT_FOR_DELIVERY, ORDER_STATUS_DELIVERED, ORDER_STATUS_CANCELED,
    ORDER_STATUS_PAYMENT_DECLINED,
    ORDER_STATUS_RETURN_REQUESTED, ORDER_STATUS_RETURN_APPROVED, ORDER_STATUS_RETURNED
)

OSCAR_DOMAIN_NAME = os.environ.get('OSCAR_DOMAIN_NAME', 'https://devserver.abchauz.com')  # for rendering image into email template


OSCAR_LINE_STATUS_PIPELINE = {
    'Placed': ('Canceled', ),                                 # user can cancel an item until order confirm
    'Order Confirmed': (),                                   # admin can deliver or confirm item
    'Out For Delivery': (),                                  # our for delivery
    'Delivered': ('Return Requested', ),                     # delivered item can be triggered for return
    'Return Requested': ('Return Approved', 'Delivered', ),  # user can cancel return to go to 'Delivered'
    'Return Approved': ('Returned',  'Delivered', ),         # or return accepted by by admin
    'Returned': (),                                          # nothing to do much
    'Canceled': (),                                          # nothing to do much
}

OSCAR_ORDER_REFUNDABLE_STATUS = (
    'Returned',
    'Canceled',
)

OSCAR_LINE_REFUNDABLE_STATUS = (
    'Returned',
    'Canceled',
)

OSCAR_ORDER_STATUS_CASCADE = {
    'Placed': 'Placed',
    'Payment Declined': 'Canceled',
    'Canceled': 'Canceled',
}

OSCAR_ADMIN_PRE_DELIVERY_STATUSES = (
    'Placed',
    'Order Confirmed',
    'Out For Delivery',
)

OSCAR_ADMIN_LINE_POST_DELIVERY_ORDER_STATUSES = (
    'Delivered',
    'Return Requested',
    'Return Approved',
    'Returned',
)

OSCAR_ADMIN_POSSIBLE_LINE_STATUSES_BEFORE_DELIVERY = (
    ('Canceled', 'Cancel Order Item'),
)
OSCAR_ADMIN_POSSIBLE_LINE_STATUSES_AFTER_DELIVERY = (
    ('Return Requested', 'Initiate the return request'),
    ('Return Approved', 'Approve Return!'),
    ('Delivered', 'Cancel return request!'),
    ('Returned', 'Returned'),
)

OSCAR_HOMEPAGE = '/'
# Menu structure of the dashboard navigation

OSCAR_DASHBOARD_NAVIGATION = [
    {
        'label': _('Dashboard'),
        'icon': 'icon-th-list',
        'url_name': 'dashboard:index',
    }, {
        'label': _('Catalogue'),
        'icon': 'icon-sitemap',
        'children': [
            {
                'label': _('Product Types'),
                'url_name': 'dashboard:catalogue-class-list',
            },
            {
                'label': _('360 Images'),
                'url_name': 'dashboard:catalogue-product360-list',
                'access_fn': lambda user, url_name, url_args, url_kwargs: user.is_staff,

            },
            {
                'label': _('Products'),
                'url_name': 'dashboard:catalogue-product-list',
            },
            {
                'label': _('Categories'),
                'url_name': 'dashboard:catalogue-category-list',
            },
            {
                'label': _('Brands'),
                'url_name': 'dashboard:catalogue-brand-list',
                'access_fn': lambda user, url_name, url_args, url_kwargs: user.is_staff,
            },
            {
                'label': _('Ranges'),
                'url_name': 'dashboard:range-list',
            },
            {
                'label': _('Low stock alerts'),
                'url_name': 'dashboard:stock-alert-list',
            },
            {
                'label': _('Options'),
                'url_name': 'dashboard:catalogue-option-list',
            },
        ]
    }, {
        'label': _('Fulfilment'),
        'icon': 'icon-shopping-cart',
        'children': [
            {
                'label': _('Orders'),
                'url_name': 'dashboard:order-list',
            },
            {
                'label': _('Statistics'),
                'url_name': 'dashboard:order-stats',
            },
            {
                'label': _('Partners'),
                'url_name': 'dashboard:partner-list',
            },
            # The shipping method dashboard is disabled by default as it might
            # be confusing. Weight-based shipping methods aren't hooked into
            # the shipping repository by default (as it would make
            # customising the repository slightly more difficult).
            # {
            #     'label': _('Shipping charges'),
            #     'url_name': 'dashboard:shipping-method-list',
            # },
        ]
    }, {
        'label': _('Customers'),
        'icon': 'icon-group',
        'children': [
            {
                'label': _('Customers'),
                'url_name': 'dashboard:users-index',
            },
            {
                'label': _('Reviews'),
                'url_name': 'dashboard:reviews-list',
            },
            # {
            #     'label': _('Dealer Registration'),
            #     'url_name': 'dealer_registration_list',
            #     'access_fn': lambda user, url_name, url_args, url_kwargs: user.is_superuser,
            # },
            {
                'label': _('Stock alert requests'),
                'url_name': 'dashboard:user-alert-list',
            },
        ]
    }, {
        'label': _('Offers'),
        'icon': 'icon-bullhorn',
        'children': [
            {'label': _('Home Page Mega Banners'),
             'url_name': 'dashboard-custom:dashboard-home-page-mega-banner-list',
             'access_fn': admin_or_staff
             },
            {'label': _('Top Categories'),
             'url_name': 'dashboard-custom:dashboard-top-category-list',
             'access_fn': admin_or_staff
             },
            {'label': _('Offer Boxes'),
             'url_name': 'dashboard-custom:dashboard-offer-box-list',
             'access_fn': admin_or_staff
             },
            {'label': _('Social Media Posts'),
             'url_name': 'dashboard-custom:dashboard-social-media-list',
             'access_fn': admin_or_staff
             },
            {'label': _('In app Full Screen Banners'),
             'url_name': 'dashboard-custom:dashboard-in-app-full-screen-banner-list',
             'access_fn': admin_or_staff
             },
            {'label': _('In app Slider Banners'),
             'url_name': 'dashboard-custom:dashboard-in-app-slider-banner-list',
             'access_fn': admin_or_staff
             },
            {'label': _('Offers'),
             'url_name': 'dashboard:offer-list',
             },
            # {'label': _('Vouchers'),
            #  'url_name': 'dashboard:voucher-list',
            #  },
            # {'label': _('Voucher Sets'),
            #  'url_name': 'dashboard:voucher-set-list',
            #  },
        ],
    },
    {
        'label': _('Content'),
        'icon': 'icon-folder-close',
        'children': [
            {
                'label': _('Pages'),
                'url_name': 'dashboard:page-list',
            },
            {
                'label': _('Predefined Return Reasons'),
                'url_name': 'dashboard-custom:dashboard-return-reason-list',
                'access_fn': admin_or_staff,
            },
            {
                'label': _('Email templates'),
                'url_name': 'dashboard:comms-list',
            },
            {
                'label': _('Reviews'),
                'url_name': 'dashboard:reviews-list',
            },
            {
                'label': _('Brochure'),
                'url_name': 'dashboard-custom:dashboard-brochure-create',
                'access_fn': lambda user, url_name, url_args, url_kwargs: user.is_staff,

            },
            {
                'label': _('Gallery'),
                'url_name': 'dashboard-custom:dashboard-gallery-create',
                'access_fn': lambda user, url_name, url_args, url_kwargs: user.is_staff,

            },


        ]
    },
    # {
    #     'label': _('Reports'),
    #     'icon': 'icon-bar-chart',
    #     'url_name': 'dashboard:reports-index',
    # }, {
    #     'label': 'Accounts',
    #     'icon': 'las la-wallet',
    #     'children': [
    #         {'label': 'Accounts', 'url_name': 'accounts_dashboard:accounts-list', },
    #         {'label': 'Transfers', 'url_name': 'accounts_dashboard:transfers-list', },
    #         {'label': 'Deferred income report', 'url_name': 'accounts_dashboard:report-deferred-income', },
    #         {'label': 'Profit/loss report', 'url_name': 'accounts_dashboard:report-profit-loss', },
    #         # {'label': _('COD transactions'),'url_name': 'cashondelivery-transaction-list', },
    #     ]
    # },
    {
        'label': _('Configurations'),
        'icon': 'icon-double-angle-down',
        'children': [
            {'label': _('Site Configuration'), 'url_name': 'dashboard-custom:site-config',
             'access_fn': admin_or_staff},
            {'label': _('Availability: Zones'), 'url_name': 'availability:zones-list',
             'access_fn': admin_or_staff},
            {'label': _('Choose Pincodes with services'), 'url_name': 'availability:pincode-selector',
             'access_fn': admin_or_staff},
            # {'label': _('Time Slots'), 'url_name': 'timeslotconfiguration-list',
            #  'access_fn': admin_or_staff},
            # {'label': _('Shipping charges'), 'url_name': 'dashboard:shipping-method-list', },
            {'label': _('Sync Stock Data'), 'url_name': 'dashboard-custom:sheet-synchronization',
             'access_fn': admin_or_staff},

        ]
        # }, {
        #     'label': _('Logistics'),
        #     'icon': 'icon-double-angle-down',
        #     'children': [
        #         {'label': _('Upcomming Time Slots'), 'url_name': 'logistics:scheduledtimeslot-list',
        #          'access_fn': admin_or_staff},
        #
        #         {'label': _('Delivery Agents'), 'url_name': 'logistics:dashboard-delivery-boy-list',
        #          'access_fn': admin_or_staff},
        #
        #         {'label': _('Create Trip'), 'url_name': 'logistics:new-trip',
        #          'access_fn': admin_or_staff},
        #
        #         {'label': _('Planned Trips'), 'url_name': 'logistics:planned-trips',
        #          'access_fn': admin_or_staff},
        #
        #         {'label': _('Active Trips'), 'url_name': 'logistics:active-trips',
        #          'access_fn': admin_or_staff},
        #
        #         {'label': _('Delivered Trips'), 'url_name': 'logistics:delivered-trips',
        #          'access_fn': admin_or_staff,
        #          },
        #         {'label': _('Cancelled Trips'), 'url_name': 'logistics:cancelled-trips',
        #          'access_fn': admin_or_staff,
        #          },
        #     ],
        # }, {
        #     'label': 'Accounts',
        #     'icon': 'icon-globe',
        #     'children': [
        #         {
        #             'label': 'Accounts',
        #             'url_name': 'accounts_dashboard:accounts-list',
        #         },
        #         {
        #             'label': 'Transfers',
        #             'url_name': 'accounts_dashboard:transfers-list',
        #         },
        #         {
        #             'label': 'Deferred income report',
        #             'url_name': 'accounts_dashboard:report-deferred-income',
        #         },
        #         {
        #             'label': 'Profit/loss report',
        #             'url_name': 'accounts_dashboard:report-profit-loss',
        #         },
        #     ]
    }]


API_ENABLED_PAYMENT_METHODS = [
    {
        'method': 'apps.payment.utils.cash_payment.Cash',
        'permission': 'apps.utils.oscar_api_checkout.AuthorizedUsers',
    },
    {
        'method': 'apps.payment.utils.razorpay_payment.RazorPay',
        'permission': 'apps.utils.oscar_api_checkout.AuthorizedUsers',
    },
]

MINIMUM_BASKET_AMOUNT_FOR_FREE_DELIVERY = 250     # in INR
DELIVERY_CHARGE = 40                     # in INR
EXPRESS_DELIVERY_CHARGE = 180            # in INR
MINIMUM_TIMESLOT_TO_BE_PROVIDED = 5

