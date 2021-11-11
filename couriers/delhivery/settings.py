
"""
Settings Available from Delhivery Accounts
"""
from osc.config.base_dir import _is_env_set_as

"""
Delhivery consider each account as CLIENT seperate for both testing and production,  
"""
CLIENT = "ABC 0051799"
STAGING_CLIENT = 'CHIKAARA0053767-B2C'


"""
Delhivery provides Seperate URL's for Staging / Production!  
"""
STAGING_URL = 'https://staging-express.delhivery.com'
PRODUCTION_URL = 'https://track.delhivery.com'


"""
Authentication Token
"""
STAGING_TOKEN = '0782a6b6204df6f052bd178214b545d7e0541a16'
PRODUCTION_TOKEN = '8b77707d9dc27386ec4d07fe68e5e2d55e412ca6'


"""
We are setting Application Mode!  
IN_PRODUCTION = True / False
"""
IN_PRODUCTION = _is_env_set_as("DEBUG", False)


"""
Just a name for reference
"""
CLIENT_NAME = CLIENT


"""
Pickup Client Warehouse and Pickup Location Address!  
"""
PICKUP = "ABC Buildwares india Pvt. Ltd"
#PICKUP_ADDRESS = "Chikaara Cosmetics, KRISHNA BUILDING8/376/C, " \
#         "FIRST FLOOR, PERUMBILISSERY JUNCTION, " \
#         "KODUNGALLUR ROAD, CHERPU. P.O. , Thrissur, 680561" \
#       "Kerala, India"
PICKUP_ADDRESS = "Kallupurakkal Building, Pookattupady Road Thrikkakara,,, Thrikkakara, Near SBI Unnichira"

"""
Pickup Warehouse
"""
STAGING_PICKUP_WAREHOUSE = 'CHIKAARA0053767-B2C'
PRODUCTION_PICKUP_WAREHOUSE = 'CHIKAARA0053767-B2C'

"""
Account Holding Email and Mobile Phone
"""
EMAIL = "Abchauzofficial@gmail.com"
MOBILE = "+919633600524"


"""
Account Holding Email and Mobile Phone
"""
SELLER_GSTIN = '32AJYPD8778K2ZB'


"""
We need unique names for Shipping Addresses! We are planning to generate it with unique id of shipping address!
"""
SHIPPING_ADDRESS_UNIQUE_SLUG = "shipping-address-{id}"

""" city """
CITY = "Ernakulam"
"""

PINCODE of Warehouse, Completely dedicated to script! Used for creating return address!
"""
# PIN_CODE = '680561'
PIN_CODE = '682021'

PICKUP_LOCATION = {
    "business_name": CLIENT_NAME,
    "name": PICKUP,
    "address": PICKUP_ADDRESS,
    "city": CITY,
    "pin": PIN_CODE,
    "state": "Kerala",
    "country": "India",
    "phone": MOBILE,
    "add": PICKUP_ADDRESS
}


