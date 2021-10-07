import random
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from faker import Factory

from apps.catalogue.models import ProductImage
from osc.config.static import MEDIA_URL

from django.core.files import File
from django.core.management import BaseCommand
from oscar.core.utils import slugify

from apps.catalogue.reviews.models import ProductReview, ProductReviewImage
from apps.order.models import Line


f = Factory.create()


def __(path):
    return "https://abchauz.dev.fegno.com" + path


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
        for line in Line.objects.all():
            if line.stockrecord is None:
                continue
            for i in range(15):
                review = ProductReview(order_line=line, product=line.stockrecord.product, score=random.randint(0, 6),
                                       title=f.text()[:60], body=f.text(), user=line.order.user, status=ProductReview.APPROVED)

                image_url_list = [__(image.original.url) for image in line.stockrecord.product.images.all()]
                for j in image_url_list:
                    self.get_remote_image(review, j)
                ol.append(review)

        ProductReview.objects.bulk_create(ol)


