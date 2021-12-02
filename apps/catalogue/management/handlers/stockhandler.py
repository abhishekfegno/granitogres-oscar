from collections import defaultdict
from pprint import pprint

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apps.catalogue.models import ProductClass
from apps.partner.models import Partner, StockRecord

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('keys/fegnodevelopments-31659696681a.json', scope)

client = gspread.authorize(creds)


class Handler(object):
    analytics = defaultdict(lambda: defaultdict(lambda: 0))
    reporting = defaultdict(list)
    skippable_sheets = []
    pc_mapper = {
        "Copy of Kitchen Sink": "Kitchen Sink",
    }

    def __init__(self):
        self.write_mode: bool = False
        self.shared_memory = {
            'partner_stocks': {},
            'partner': {},
            'updater': {},
        }

    def read_from_sheet(self):
        self.handle(update_sheet=False)

    def sync_db_to_sheet(self):
        self.handle(update_sheet=True)

    def handle(self, *args, **options):
        self.write_mode = options['update_sheet']
        workbook = client.open_by_key('1WIeWBr4rka0SDO32VOcDw_N8tttySqC4YjC0Gh9Zr3Q')
        sheets = workbook.worksheets()
        for sheet in sheets:
            print(" =============================================== ")
            if sheet.title in self.skippable_sheets:
                print("Skipping in ", sheet.title)
                continue
            print("Operating in ", sheet.title)
            # self.extract_sheet(sheet)
            if input("Do you want to proceed? ").lower() == "y":
                self.extract_sheet(sheet)
            else:
                print("Skipping.... ")
        print(" =============================================== ")
        pprint(dict(self.analytics))
        pprint(dict(self.reporting))

    def extract_sheet(self, sheet):
        parent_products = {}

        pc_title = self.pc_mapper.get(sheet.title, sheet.title)
        pc, _ = ProductClass.objects.get_or_create(name=pc_title)
        if self.write_mode:
            self.update_row(sheet, pc)
        else:

            dataset = sheet.get_all_records()
            self.shared_memory['updater'] = dict()
            self.shared_memory['partner'] = dict()
            self.shared_memory['read_stock_and_price'] = {}
            for row in dataset:
                self.read_stock_and_price(row)

    def update_row(self, worksheet, pc):
        out = [
            ["partner",	"stock_id",	"product_id",	"product",	"stock",	"online_price",	"retail_price"]
        ]
        qs = StockRecord.objects.filter(product__product_class=pc).order_by('id')
        count = qs.count()
        for sr in qs:
            out.append([sr.partner.name, sr.id, sr.product_id, sr.product.get_title(), sr.num_in_stock, sr.price_excl_tax, sr.price_retail])
        worksheet.clear()
        worksheet.update(f'A1:G{count+1}', out)

    def get_partner(self, name) -> Partner:
        if name.upper() not in self.shared_memory['partner']:
            partner = Partner.objects.filter(name__iexact=name.upper()).prefetch_related('stockrecords').first()
            self.shared_memory['partner'][name.upper()] = partner
            if name.upper() not in self.shared_memory['partner_stocks']:
                self.shared_memory['partner_stocks'][name.upper()] = {}
            self.shared_memory['partner_stocks'][name.upper()] = {s.id: s for s in partner.stockrecords.all()}
        return self.shared_memory['partner'][name.upper()]

    def read_stock_and_price(self, row) -> None:
        partner: Partner = self.get_partner(name=row['partner'].upper())
        partner_name = row['partner'].upper()
        stock_id = row['stock_id']
        stock: StockRecord = self.shared_memory['partner_stocks'][partner_name][stock_id]
        stock.num_in_stock = row['stock']
        stock.price_excl_tax = row['online_price']
        stock.price_retail = row['retail_price']
        stock.save()



