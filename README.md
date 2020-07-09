# Shopprix
###### Grossery Based E-Commerce Project By Fegno Technologies.

### Features 


### DEVELOEPRS
1. github::jerinisready


### API Docs 
Api Docs is available on `/api/v1/`     
{updated from `apps.mod_oscarapi.views.root`}


#### Environment Variables Docs

    DB_HOST=<DB_HOST>
    DB_NAME=<DB_NAME>
    DB_USER=<DB_USER>
    DB_PASSWORD=<DB_PASSWORD>
    IN_PRODUCTION=False
    DEBUG=True    
    
    HAYSTACK_ENGINE=haystack.backends.simple_backend.SimpleEngine #(currentlu not using)
    HAYSTACK_URL=
    HAYSTACK_INCLUDE_SPELLING=True
    
    STRIPE_LIVE_PUBLIC_KEY=
    STRIPE_LIVE_SECRET_KEY=
    STRIPE_TEST_PUBLIC_KEY=pk_test_pwwR9T.....................QytrBk9
    STRIPE_TEST_SECRET_KEY=sk_test_5LiCrh.....................kbs47HE
    STRIPE_EMAIL=jer......dy@g....com
    
    STRIPE_LIVE_MODE=off                 # Change to 'on' in production
    DJSTRIPE_WEBHOOK_SECRET="whsec_xxx"  # Get it from the section in the Stripe dashboard where you added the webhook endpoint
    
    RAZOR_PAY_MERCHANT_ID=Ewb2..........M1
    RAZOR_PAY_LIVE_PUBLIC_KEY=
    RAZOR_PAY_LIVE_SECRET_KEY=
    RAZOR_PAY_TEST_PUBLIC_KEY=rzp_test_inQ.........70Z
    RAZOR_PAY_TEST_SECRET_KEY=M9eHM0YwWZYr.........xPi
    RAZOR_PAY_EMAIL=jerinisready@gmail.com
    RAZOR_PAY_LIVE_MODE=off                 # Change to 'on' in production
    FAST_2_SMS_SENDER_ID='SMSIND'
    FAST_2_SMS_API_KEY="eTVuoO.................I12YUB..........................615eNu"
    FAST_2_SMS_TEMPLATE_ID=14782
    FCM_API_KEY=AAAAIdKjsl4:APA9.................msJ7-2FaM....8kf_D8c2.......3jj-gKG...........PCf



Additionally add in  requirements.txt

```
pip install -e git+https://github.com/michaelkuty/django-oscar-cash-on-delivery#egg=cashondelivery
```


#### How to deploy?
Create a database and a user in postgres database.

    create database grocery;
    create user  grocery_user with password 'password';
    grant all privileges on database grocery to grocery_user;
    \c grocery;
    Create Extension postgis;
    CREATE EXTENSION pg_trgm;
    \q
    
update values properly in  `.env`

    DB_HOST=localhost
    DB_NAME=grocery
    DB_USER=grocery_user
    DB_PASSWORD=password


migrate the project. Run the server.
    
    python manage.py migrate
    python manage.py runserver
    







