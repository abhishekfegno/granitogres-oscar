from django.core.management import BaseCommand
import csv


class Command(BaseCommand):
    """
    ./manage.py load_from_wordpress public/dataset/abchauz_wp/wc-product-export-16-8-2021-1629114021490.csv
    HEADER:
     post_title,
     post_name,
     post_parent,
     ID,
     post_content,
     post_excerpt,
     post_status,
     post_password,
     menu_order,
     post_date,
     post_author,
     comment_status,
     sku,
     parent_sku,
     children,
     downloadable,
     virtual,
     stock,
     regular_price,
     sale_price,
     weight,
     length,
     width,
     height,
     tax_class,
     visibility,
     stock_status,
     backorders,
     sold_individually,
     low_stock_amount,
     manage_stock,
     tax_status,
     upsell_ids,
     crosssell_ids,
     purchase_note,
     sale_price_dates_from,
     sale_price_dates_to,
     download_limit,
     download_expiry,
     product_url,
     button_text,
     images,
     downloadable_files,
     product_page_url

    """

    def add_arguments(self, parser):
        parser.add_argument('data_source_csv', type=str, help='please choose a path of images')

    def handle(self, *args, **kwargs):
        filename = kwargs['data_source_csv']
        with open(filename, 'r') as _fp:
            contents = csv.DictReader(_fp)
            for line in contents:
                print(line['post_title'], line['children'])
                # if line['children']:
                #     import pdb; pdb.set_trace()
                #     break
        return



