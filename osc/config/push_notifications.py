
import os

from osc.config.base_dir import BASE_DIR


PUSH_NOTIFICATIONS_SETTINGS = {
        # 'FCM_API_KEY': os.environ.get('FCM_API_KEY', ),
        # 'GCM_API_KEY': None,
        #
        # 'APNS_CERTIFICATE': '/path/to/your/certificate.pem',
        # 'APNS_TOPIC': 'com.example.push_test',

        "CONFIG": 'push_notifications.conf.AppConfig',
        "APPLICATIONS": {
                "GROCERY": {
                        # PLATFORM (required) determines what additional settings are required.
                        "PLATFORM": "FCM",

                        # required FCM setting
                        "API_KEY": os.environ.get('FCM_API_KEY', ),
                },
                "GROCERY_IOS": {
                        # PLATFORM (required) determines what additional settings are required.
                        "PLATFORM": "APNS",
                        # required APNS setting
                        "CERTIFICATE": os.path.join(BASE_DIR, 'keys', 'cert.pem'),
                },
                "DELIVERYBOY": {
                        # PLATFORM (required) determines what additional settings are required.
                        "PLATFORM": "FCM",

                        # required APNS setting
                        "API_KEY": os.environ.get('FCM_API_KEY', ),
                },
        }

}

