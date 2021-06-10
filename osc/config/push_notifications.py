
import os

from osc.config.base_dir import BASE_DIR
CUSTOMER = 'CUSTOMER'
DELIVERY_BOY = 'DELIVERY_BOY'
DELIVERY_BOY_ANDROID_APP = 'com.fegno.delivery_boy_application'
CUSTOMER_ANDROID_APP = 'com.fegno.ecom.eshop'
CUSTOMER_IOS_APP = 'com.fegno.ecom.eshop2'

PUSH_DEVICES = {
        DELIVERY_BOY_ANDROID_APP: CUSTOMER,
        CUSTOMER_ANDROID_APP: CUSTOMER,
        CUSTOMER_IOS_APP: DELIVERY_BOY,
}

PUSH_NOTIFICATIONS_SETTINGS = {
        # 'FCM_API_KEY': os.environ.get('FCM_API_KEY', ),
        # 'GCM_API_KEY': None,
        #
        # 'APNS_CERTIFICATE': '/path/to/your/certificate.pem',
        # 'APNS_TOPIC': 'com.example.push_test',

        "CONFIG": 'push_notifications.conf.AppConfig',
        "APPLICATIONS": {
                CUSTOMER_ANDROID_APP: {
                        # PLATFORM (required) determines what additional settings are required.
                        "PLATFORM": "FCM",
                        # required FCM setting
                        "API_KEY": os.environ.get('FCM_API_KEY', ),
                },
                CUSTOMER_IOS_APP: {
                        # PLATFORM (required) determines what additional settings are required.
                        "PLATFORM": "APNS",
                        # required APNS setting
                        "CERTIFICATE": os.path.join(BASE_DIR, 'keys', 'cert.pem'),
                },
                DELIVERY_BOY_ANDROID_APP: {
                        # PLATFORM (required) determines what additional settings are required.
                        "PLATFORM": "FCM",
                        # required APNS setting
                        "API_KEY": os.environ.get('FCM_API_KEY'),
                },
        }

}

