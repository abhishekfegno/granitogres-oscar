

import os

STRIPE_LIVE_MODE = os.environ.get("STRIPE_LIVE_MODE", 'off').lower() in ('true', 'on')   # Change to True in production

if STRIPE_LIVE_MODE:
    STRIPE_PUBLIC_KEY = os.environ["STRIPE_LIVE_PUBLIC_KEY"]
    STRIPE_SECRET_KEY = os.environ["STRIPE_LIVE_SECRET_KEY"]
else:
    STRIPE_PUBLIC_KEY = os.environ["STRIPE_TEST_PUBLIC_KEY"]
    STRIPE_SECRET_KEY = os.environ["STRIPE_TEST_SECRET_KEY"]

STRIPE_EMAIL = os.environ.get("STRIPE_EMAIL")
STRIPE_CURRENCY = "INR"

# Get it from the section in the Stripe dashboard where you added the webhook endpoint
DJSTRIPE_WEBHOOK_SECRET = "whsec_xxx"

