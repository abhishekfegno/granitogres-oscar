import os

from django.core.management import BaseCommand
from oscar.apps.offer.models import Range

from apps.catalogue.models import Category
from apps.dashboard.custom.models import OfferBanner, TopCategory, HomePageMegaBanner, OfferBox, InAppBanner, \
    InAppFullScreenBanner, InAppSliderBanner, SocialMediaPost
import shutil

from apps.partner.models import StockRecord


def copy_media_files():
    src = 'public/dataset/home/*'
    dst = 'public/media/.'
    os.system(f"cp -rf {src} {dst}")


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        copy_media_files()
        self.set_banners()
        self.set_top_categories()
        self.set_listing_range_products()

        self.offer_boxes()
        self.set_short_banners_3x()
        self.set_one_ling_banner()
        self.set_instagram_page()

    def set_banners(self):
        #  BANNER 1 - Bathroom Accessories
        Range.objects.filter(
            slug__in=[
                'bathroom_accessories',
                'kitchen_sink',
                'furniture',
                'decor_artestic',
                'decor_latest',
                'furniture_top_categories',
                'surface_top_categories',
                'faucets_top_categories',
                'kitchen_sink_top_categories',
                'bathroom_top_categories',
            ]
        ).delete()
        rng, created = Range.objects.get_or_create(name="HOMEPAGE - Bathroom Accessories", slug="bathroom_accessories", is_public=True)
        ct: Category = Category.objects.get(name="Accessories")
        for cat in ct.get_descendants_and_self():
            rng.included_categories.add(cat)
        rng.save()
        HomePageMegaBanner.objects.create(
            position=5,
            title="Modern Bathroom Collections",
            banner="banner/bathroom.jpg",
            product_range=rng
        )

        #  BANNER 2 - Kitchen Accessories
        rng, created = Range.objects.get_or_create(name="HOMEPAGE - Hot deals on Kitchenware", slug="kitchen_sink", is_public=True)
        ct: Category = Category.objects.get(name="Kitchen Sink")
        rng.included_categories.add(ct)
        rng.save()
        HomePageMegaBanner.objects.create(
            position=10,
            title="Hot deals on Kitchenware",
            banner="banner/kitchen.jpg",
            product_range=rng
        )

        #  BANNER 3 - Exclusive Furniture Collection
        rng, created = Range.objects.get_or_create(name="HOMEPAGE - Exclusive Furniture Collection", slug="furniture", is_public=True)
        # ct: Category = Category.objects.get(name="Kitchen Sink")
        # rng.included_categories.add(ct)
        # rng.save()
        HomePageMegaBanner.objects.create(
            position=5,
            title="Exclusive Furniture Collection",
            banner="banner/Furniture-banner.jpg",
            product_range=rng
        )

        #  BANNER 4 - Artestic Decor Collections
        rng, created = Range.objects.get_or_create(name="HOMEPAGE - Artestic Decor Collections", slug="decor_artestic", is_public=True)
        ct: Category = Category.objects.get(name="Art Basins")
        rng.included_categories.add(ct)
        rng.save()
        HomePageMegaBanner.objects.create(
            position=20,
            title="Artestic Decor Collections",
            banner="banner/decor.jpg",
            product_range=rng
        )

    def set_top_categories(self):
        rng, created = Range.objects.get_or_create(name="TopCategories - Explore the latest decor items", slug="decor_latest", is_public=True)
        ct: Category = Category.objects.get(name="Art Basins")
        rng.included_categories.add(ct)
        TopCategory.objects.create(
            position=5,
            title="Explore the latest decor items",
            image="collections/decor-new.jpg",
            product_range=rng
        )
        # Top categories :: 2
        rng, created = Range.objects.get_or_create(name="TopCategories - Let your furniture evolve", slug="furniture_top_categories", is_public=True)
        # ct: Category = Category.objects.get(name="Art Basins")
        rng.included_categories.add(ct)
        TopCategory.objects.create(
            position=10,
            title="Let your furniture evolve",
            image="collections/Furniture-new-1.jpg",
            product_range=rng
        )

        # Top categories :: 3
        rng, created = Range.objects.get_or_create(name="TopCategories - Rich and Conventional Surface", slug="surface_top_categories", is_public=True)
        # ct: Category = Category.objects.get(name="Art Basins")
        rng.included_categories.add(ct)
        TopCategory.objects.create(
            position=15,
            title="Rich and Conventional Surface",
            image="collections/Tiles-Category.jpg",
            product_range=rng
        )

        # Top categories :: 4
        rng, created = Range.objects.get_or_create(name="TopCategories - Exciting Deals on Branded Faucets", slug="faucets_top_categories", is_public=True)
        # ct: Category = Category.objects.get(name="Art Basins")
        rng.included_categories.add(ct)
        TopCategory.objects.create(
            position=20,
            title="Exciting Deals on Branded Faucets",
            image="collections/faucet-Category.jpg",
            product_range=rng
        )

        # Top categories :: 5
        rng, created = Range.objects.get_or_create(name="TopCategories - Amazing offers in Kitchen Sink", slug="kitchen_sink_top_categories", is_public=True)
        # ct: Category = Category.objects.get(name="Art Basins")
        rng.included_categories.add(ct)
        TopCategory.objects.create(
            position=25,
            title="Amazing offers in Kitchen Sink",
            image="collections/kitchen-new.jpg",
            product_range=rng
        )

        # Top categories :: 6
        rng, created = Range.objects.get_or_create(name="TopCategories - Elegant Bathroom Accessories", slug="bathroom_top_categories", is_public=True)
        # ct: Category = Category.objects.get(name="Art Basins")
        rng.included_categories.add(ct)
        TopCategory.objects.create(
            position=3,
            title="Elegant Bathroom Accessories",
            image="collections/Bathroom-new.jpg",
            product_range=rng
        )

    def set_listing_range_products(self):

        exclusive_products_slug = 'exclusive-products'
        exclusive_products, _created = Range.objects.get_or_create(
            slug=exclusive_products_slug,
            defaults={
                'name': '??? Exclusive Products',
                'is_public': True,
            }
        )
        furniture_for_your_home_slug = 'furnitures-for-your-home'
        furniture_for_your_home, _created = Range.objects.get_or_create(
            slug=furniture_for_your_home_slug,
            defaults={
                'name': '??? Furnitures for your home',
                'is_public': True,
            }
        )
        jambo_offer_slug = 'jumbo-offer'
        jambo_offer, _created = Range.objects.get_or_create(
            slug=jambo_offer_slug,
            defaults={
                'name': 'Jumbo Offers',
                'is_public': True,
            }
        )
        offer_banner_3_slug = 'offer-banner-x3'
        offer_banner_3, _created = Range.objects.get_or_create(
            slug=offer_banner_3_slug,
            defaults={
                'name': '??? ',
                'is_public': True,
            }
        )
        picked_for_you_slug = 'picked-for-you'
        picked_for_you, _created = Range.objects.get_or_create(
            slug=picked_for_you_slug,
            defaults={
                'name': '??? Picked for you',
                'is_public': True,
            }
        )
        customer_favorites_slug = 'customer-favorites'
        customer_favorites, _created = Range.objects.get_or_create(
            slug=customer_favorites_slug,
            defaults={
                'name': '??? Customer Favorites',
                'is_public': True,
            }
        )

    def set_short_banners_3x(self):
        # 1
        _range, _created = Range.objects.get_or_create(
            slug='elegant-design-with-a-touch-of-sophistication',
            defaults={
                'name': '??? Elegant Design With A Touch Of Sophistication',
                'is_public': True,
            }
        )
        iab = InAppSliderBanner.objects.create(
            position=10,
            title='Elegant Design With A Touch Of Sophistication',
            product_range=_range,
            banner='3x/chair-1-1.jpg',
            type=InAppBanner.SLIDER_BANNER,
        )

        # 2
        _range, _created = Range.objects.get_or_create(
            slug='home-decor-collection',
            defaults={
                'name': '??? Interior Decor Collections',
                'is_public': True,
            }
        )
        iab = InAppSliderBanner.objects.create(
            position=20,
            title='Interior Decor Collections',
            product_range=_range,
            banner='3x/decor-2.jpg',
            type=InAppBanner.SLIDER_BANNER,
        )

        # 3
        _range, _created = Range.objects.get_or_create(
            slug='best-bathroom-accessories',
            defaults={
                'name': '??? Best Bathroom Accessories',
                'is_public': True,
            }
        )
        iab = InAppSliderBanner.objects.create(
            position=30,
            title='Best Bathroom Accessories',
            product_range=_range,
            banner='3x/bathroom-accessories-new.jpg',
            type=InAppBanner.SLIDER_BANNER,
        )

    def set_one_ling_banner(self):
        # 4
        _range, _created = Range.objects.get_or_create(
            slug='full-length-banner',
            defaults={
                'name': '??? Best Bathroom Access0ories',
                'is_public': True,
            }
        )
        iab = InAppFullScreenBanner.objects.create(
            position=1,
            title='Best Bathroom Accessories',
            product_range=_range,
            banner='fullwidth/banner-2.png',
            type=InAppBanner.SLIDER_BANNER,
        )

    def offer_boxes(self):
        Range.objects.filter(
            slug__in=[
                'under-500',
                '500-2000',
                '2000-7000',
                '7000-15000',
                '15000-',
            ]
        ).delete()
        r = Range(slug="under-500", name="Under 500", is_public=True)
        r.save()
        ind = 0
        for sr in StockRecord.objects.filter(price_excl_tax__lte=500).select_related('product'):
            r.add_product(sr.product, ind)
        OfferBox.objects.create(
            image='price/under-500-200x200.png',
            product_range=r,
            position=1,
            title='Under 500',
        )

        r = Range(slug="500-2000", name="500 to 2000", is_public=True)
        r.save()
        ind = 0
        for sr in StockRecord.objects.filter(price_excl_tax__range=(500, 2_000)).select_related('product'):
            r.add_product(sr.product, ind)
        OfferBox.objects.create(
            image='price/500-to-2000-200x200.png',
            product_range=r,
            position=1,
            title='500 to 2000',
        )

        r = Range(slug="2000-7000", name="2000 to 7000", is_public=True)
        r.save()
        ind = 0
        for sr in StockRecord.objects.filter(price_excl_tax__range=(2_000, 7_000)).select_related('product'):
            r.add_product(sr.product, ind)
        OfferBox.objects.create(
            image='price/2000-to-7000-200x200.png',
            product_range=r,
            position=1,
            title='2000 to 7000',
        )
        r = Range(slug="7000-15000", name="7000 to 15000", is_public=True)
        r.save()
        ind = 0
        for sr in StockRecord.objects.filter(price_excl_tax__range=(7_000, 15_000)).select_related('product'):
            r.add_product(sr.product, ind)
        OfferBox.objects.create(
            image='price/7000-to-15000-200x200.png',
            product_range=r,
            position=1,
            title='7000 to 15000',
        )

        r = Range(slug="15000-", name="15000 and Above", is_public=True)
        r.save()
        ind = 0
        for sr in StockRecord.objects.filter(price_excl_tax__gte=15_000).select_related('product'):
            r.add_product(sr.product, ind)
        OfferBox.objects.create(
            image='price/15000-200x200.png',
            product_range=r,
            position=1,
            title='15000 and Above',
        )

    def set_instagram_page(self):
        SocialMediaPost.objects.create(
            position=1,
            title='ins01',
            banner="insta/ins01.jpg",
            social_media_url="https://www.instagram.com/p/Cac4zFzvVis/",
        )

        SocialMediaPost.objects.create(
            position=2,
            title='ins02',
            banner="insta/ins02.jpg",
            social_media_url="https://www.instagram.com/p/Cayvrj7P_FB/",
        )

        SocialMediaPost.objects.create(
            position=3,
            title='ins03',
            banner="insta/ins03.jpg",
            social_media_url="https://www.instagram.com/p/CaR4pCkqjyE/",
        )

        SocialMediaPost.objects.create(
            position=4,
            title='ins04',
            banner="insta/ins04.jpg",
            social_media_url="https://www.instagram.com/p/CaR4pCkqjyE/",
        )

