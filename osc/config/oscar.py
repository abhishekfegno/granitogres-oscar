from oscar.defaults import *

OSCARAPI_OVERRIDE_MODULES = ["apps.mod_oscarapi"]

OSCARAPI_BLOCK_ADMIN_API_ACCESS = True

OSCAR_DEFAULT_CURRENCY = 'INR'
OSCAR_SHOP_NAME = 'Shopprix'
OSCAR_SHOP_TAGLINE = "Super Center"
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
OSCAR_DASHBOARD_ITEMS_PER_PAGE = 20

_ = lambda x: x

OSCAR_DASHBOARD_DEFAULT_ACCESS_FUNCTION = 'oscar.apps.dashboard.nav.default_access_fn'

OSCAR_ALLOW_ANON_REVIEWS = False
OSCAR_MODERATE_REVIEWS = False

OSCAR_EAGER_ALERTS = True
OSCAR_SEND_REGISTRATION_EMAIL = True
OSCAR_FROM_EMAIL = 'no-reply@grocery.com'
OSCAR_OFFERS_INCL_TAX = False

OSCAR_MISSING_IMAGE_URL = 'image_not_found.jpg'
OSCAR_GOOGLE_ANALYTICS_ID = None

# Other statuses
ORDER_STATUS_PLACED = 'Placed'
ORDER_STATUS_CONFIRMED = 'Order Confirmed'
# ORDER_STATUS_SHIPPED = 'Shipped'
ORDER_STATUS_OUT_FOR_DELIVERY = 'Out For Delivery'
ORDER_STATUS_DELIVERED = 'Delivered'
ORDER_STATUS_RETURN_REQUESTED = 'Return Requested'
ORDER_STATUS_RETURN_APPROVED = 'Return Approved'
ORDER_STATUS_RETURNED = 'Returned'
ORDER_STATUS_CANCELED = 'Canceled'

# Needed by oscarapicheckout
ORDER_STATUS_PENDING = 'Placed'
ORDER_STATUS_PAYMENT_DECLINED = 'Payment Declined'
ORDER_STATUS_AUTHORIZED = ORDER_STATUS_PENDING
OSCAR_INITIAL_ORDER_STATUS = ORDER_STATUS_PENDING
OSCARAPI_INITIAL_ORDER_STATUS = ORDER_STATUS_PENDING
OSCAR_INITIAL_LINE_STATUS = ORDER_STATUS_PENDING

admin_or_staff = lambda user, url_name, url_args, url_kwargs: user.is_staff or user.is_superuser

OSCAR_ORDER_STATUS_PIPELINE = {

    # 'Pending': ('Order Confirmed', 'Canceled', 'Pending', 'Payment Declined'),
    # admin / user can cancel an order / an item

    'Placed': ('Order Confirmed', 'Payment Declined', 'Canceled'),  # admin / user can cancel an order / an item
    'Order Confirmed': ('Out For Delivery', 'Delivered', 'Canceled'),  # only admin can set these statuses
    'Out For Delivery': ('Delivered', 'Canceled'),  # only admin can set these statuses
    'Delivered': ('Return Requested', ),
    'Return Requested': ('Return Approved', ),
    'Return Approved': ('Returned', ),
    'Payment Declined': (),
    'Canceled': (),

}

OSCAR_LINE_STATUS_PIPELINE = {
    'Placed': ('Canceled',),                                 # user can cancel an item until order confirm
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
                'label': _('Products'),
                'url_name': 'dashboard:catalogue-product-list',
            },
            {
                'label': _('Product Types'),
                'url_name': 'dashboard:catalogue-class-list',
            },
            {
                'label': _('Categories'),
                'url_name': 'dashboard:catalogue-category-list',
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
            {
                'label': _('Offers'),
                'url_name': 'dashboard:offer-list',
            },
            {
                'label': _('Vouchers'),
                'url_name': 'dashboard:voucher-list',
            },
            {
                'label': _('Voucher Sets'),
                'url_name': 'dashboard:voucher-set-list',
            },

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
            # {
            #     'label': _('Email templates'),
            #     'url_name': 'dashboard:comms-list',
            # },
            {
                'label': _('Reviews'),
                'url_name': 'dashboard:reviews-list',
            },
        ]
    },
    {
        'label': _('Reports'),
        'icon': 'icon-bar-chart',
        'url_name': 'dashboard:reports-index',
    }, {
        'label': 'Accounts',
        'icon': 'las la-wallet',
        'children': [
            {'label': 'Accounts', 'url_name': 'accounts_dashboard:accounts-list', },
            {'label': 'Transfers', 'url_name': 'accounts_dashboard:transfers-list', },
            {'label': 'Deferred income report', 'url_name': 'accounts_dashboard:report-deferred-income', },
            {'label': 'Profit/loss report', 'url_name': 'accounts_dashboard:report-profit-loss', },
            # {'label': _('COD transactions'),'url_name': 'cashondelivery-transaction-list', },
        ]
    }, {
        'label': _('Configurations'),
        'icon': 'icon-double-angle-down',
        'children': [
            {'label': _('Availability: Zones'), 'url_name': 'availability:zones-list',
             'access_fn': admin_or_staff},

            {'label': _('Offer Banners'),
             'url_name': 'dashboard-custom:dashboard-offer-banner-list',
             'access_fn': admin_or_staff
             },

            {'label': _('Shipping charges'), 'url_name': 'dashboard:shipping-method-list', },

        ]
    }, {
        'label': _('Logistics'),
        'icon': 'icon-double-angle-down',
        'children': [
            {'label': _('Delivery Agents'), 'url_name': 'logistics:dashboard-delivery-boy-list',
             'access_fn': admin_or_staff},

            {'label': _('Create Trip'), 'url_name': 'logistics:new-trip',
             'access_fn': admin_or_staff},

            {'label': _('Planned Trips'), 'url_name': 'logistics:planned-trips',
             'access_fn': admin_or_staff},

            {'label': _('Active Trips'), 'url_name': 'logistics:active-trips',
             'access_fn': admin_or_staff},

            {'label': _('Delivered Trips'), 'url_name': 'logistics:delivered-trips',
             'access_fn': admin_or_staff,
             },

            {'label': _('Cancelled Trips'), 'url_name': 'logistics:cancelled-trips',
             'access_fn': admin_or_staff,
             },
        ],
    }, {
        'label': 'Accounts',
        'icon': 'icon-globe',
        'children': [
            {
                'label': 'Accounts',
                'url_name': 'accounts_dashboard:accounts-list',
            },
            {
                'label': 'Transfers',
                'url_name': 'accounts_dashboard:transfers-list',
            },
            {
                'label': 'Deferred income report',
                'url_name': 'accounts_dashboard:report-deferred-income',
            },
            {
                'label': 'Profit/loss report',
                'url_name': 'accounts_dashboard:report-profit-loss',
            },
        ]
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
DELIVERY_CHARGE = 40            # in INR

