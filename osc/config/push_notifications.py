
import os

from osc.config.base_dir import BASE_DIR

PUSH_NOTIFICATIONS_SETTINGS = {
        'FCM_API_KEY': os.environ.get('FCM_API_KEY', ),
        'GCM_API_KEY': None,

        'APNS_CERTIFICATE': '/path/to/your/certificate.pem',
        'APNS_TOPIC': 'com.example.push_test',

        'WNS_PACKAGE_SECURITY_ID': '[your package security id, e.g: \'ms-app://e-3-4-6234...\']',
        'WNS_SECRET_KEY': '[your app secret key, e.g.: \'KDiejnLKDUWodsjmewuSZkk\']',
        'WP_PRIVATE_KEY': os.path.join(BASE_DIR, 'keys/wns/private.pem'),
        'WP_CLAIMS': {'sub': 'mailto: woodncart@gmail.com'}
}

