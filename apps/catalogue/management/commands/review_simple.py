import random
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from faker import Factory

from apps.catalogue.models import ProductImage, Product
from apps.users.models import User
from osc.config.static import MEDIA_URL

from django.core.files import File
from django.core.management import BaseCommand
from oscar.core.utils import slugify

from apps.catalogue.reviews.models import ProductReview, ProductReviewImage
from apps.order.models import Line


f = Factory.create()


def __(path):
    return "https://devserver.abchauz.com" + path


class Command(BaseCommand):

    def get_remote_image(self, review, image_url):
        try:
            ext = image_url.split('.')[-1]
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(image_url).read())
            img_temp.flush()
            product_img = ProductReviewImage(caption=review.title, review=review)
            product_img.original.save(f"{slugify(review.title)}.{ext}", File(img_temp))
            product_img.save()
        except Exception as e:
            print('[x]  Could not fetch the image!' + str(e))

    def handle(self, **kwargs):
        from django.db.models import Max, F, ExpressionWrapper, IntegerField, Q, Case, When, Sum, Count

        ol = []
        for product in Product.objects.all():
            # if line.stockrecord is None:
            #     continue
            print("Reviewing Product", product)
            for i in range(15):
                user = User.objects.all().order_by('?').first()
                review = ProductReview(product=product, score=random.randint(0, 6),
                                       title=f.text()[:60], body=f.text(), user=user, status=ProductReview.APPROVED)

                image_url_list = [__(image.original.url) for image in product.images.all()]
                review.save()
                for j in (image_url_list + image_url_list):
                    self.get_remote_image(review, j)
                ol.append(review)

        ProductReview.objects.bulk_create(ol)


