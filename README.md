# GRANITOGRES OSCAR
###### GRANITOGRES - An OSCAR Based E-Commerce Project By Fegno Technologies.

### Features 


### DEVELOEPRS
1. github::jerin-fegno
2. github::abhishek-fegno

### API Docs 
Api Docs is available on `/api/v2/`     
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



You need to setup GDAL before adding requirements.txt

```
#!/usr/bin/env bash

sudo add-apt-repository ppa:ubuntugis/ppa && sudo apt-get update
sudo apt-get update
sudo apt-get install gdal-bin
sudo apt-get install libgdal-dev
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
pip install GDAL
```

install `requirements.txt`


```
pip install -r requirements.txt
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
    
    
##### How to fill up with dummy data:
We have script to generate dummy data from package
https://github.com/marcusklasson/GroceryStoreDataset .

Download the package to home directory.

then run the management command `generate_products` as :

    python manage.py generate_products --copy ~/GroceryStoreDataset/dataset/iconic-images-and-descriptions ~/GroceryStoreDataset/dataset/classes.csv

(Code is editabel at `apps.catalogue.management.commands.generate_products`)
takes optional  --copy to names with folder of images. instead you can manually copy the contents of 
`iconic-images-and-descriptions` to your media folder 
`public/media/products/scripted/` pass required parameter `classes.csv` file to script to start execution.


The script is optimized so as not to read all the file, reprocess them to django media file and  then save tp db. 
Instead, it stores the path directly to db as string.





