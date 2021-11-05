
"""
Settings Available from Delhivery Accounts
"""

"""
Delhivery consider each account as CLIENT seperate for both testing and production,  
"""
CLIENT = "CHIKAARA0053767"
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
IN_PRODUCTION = False


"""
Just a name for reference
"""
CLIENT_NAME = "Chikaara Cosmetics"


"""
Pickup Client Warehouse and Pickup Location Address!  
"""
PICKUP = 'CHIKAARA 0053767'
PICKUP_ADDRESS = "Chikaara Cosmetics, KRISHNA BUILDING8/376/C, " \
         "FIRST FLOOR, PERUMBILISSERY JUNCTION, " \
         "KODUNGALLUR ROAD, CHERPU. P.O. , Thrissur, 680561" \
         "Kerala, India"


"""
Pickup Warehouse
"""
STAGING_PICKUP_WAREHOUSE = 'CHIKAARA0053767-B2C'
PRODUCTION_PICKUP_WAREHOUSE = 'CHIKAARA0053767-B2C'

"""
Account Holding Email and Mobile Phone
"""
EMAIL = "chikaaracosmetics@gmail.com"
MOBILE = "+919497396083"


"""
Account Holding Email and Mobile Phone
"""
SELLER_GSTIN = '32AJYPD8778K2ZB'


"""
We need unique names for Shipping Addresses! We are planning to generate it with unique id of shipping address!
"""
SHIPPING_ADDRESS_UNIQUE_SLUG = "shipping-address-{id}"


"""
PINCODE of Warehouse, Completely dedicated to script! Used for creating return address!
"""
PIN_CODE = '680561'

PICKUP_LOCATION = {
    "business_name": CLIENT_NAME,
    "name": STAGING_CLIENT,
    "address": ' KRISHNA BUILDING8/376/C, FIRST FLOOR, PERUMBILISSERY JUNCTION, KODUNGALLUR ROAD, CHERPU. P.O. , ',
    "city": "Trissur",
    "pin": PIN_CODE,
    "state": "Kerala",
    "country": "India",
    "phone": MOBILE,
    "add": PICKUP_ADDRESS
}


