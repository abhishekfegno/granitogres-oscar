import math
from collections import defaultdict
from pprint import pprint

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apps.catalogue.models import ProductClass
from apps.dashboard.custom.models import SiteConfig
from apps.partner.models import Partner, StockRecord

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('keys/fegnodevelopments-31659696681a.json', scope)

client = gspread.authorize(creds)
"https://www.youtube.com/watch?v=RPMEoNfZW5k&t=445s"


class Handler(object):
    analytics = defaultdict(lambda: defaultdict(lambda: 0))
    reporting = defaultdict(list)
    skippable_sheets = []
    pc_mapper = {
        "Copy of Kitchen Sink": "Kitchen Sink",
    }

    def __init__(self, sheet_id=None):
        self.write_mode: bool = False
        self.allow_all: bool = False
        self.sheet_id = sheet_id or SiteConfig.get_solo().sync_google_sheet_id

        self.shared_memory = {
            'partner_stocks': {},
            'partner': {},
            'updater': {},
        }

    def read_from_sheet(self):
        self.handle(update_sheet=False)

    def sync_db_to_sheet(self):
        # caller_function can be: sync_db_to_sheet, sync_stock_from_sheet_to_db, sync_price_from_db_to_sheet
        self.handle(update_sheet=True)

    # Commented because of action is vulnurable to business ideas.
    # def sync_sheet_to_db(self):
    #     # caller_function can be: sync_db_to_sheet, sync_stock_from_sheet_to_db, sync_price_from_db_to_sheet
    #     self.handle(update_sheet=False)

    def sync_stock_from_sheet_to_db(self):
        # caller_function can be: sync_db_to_sheet, sync_stock_from_sheet_to_db,
        self.handle(update_sheet=False, fields=("stock", ))

    def sync_stock_from_db_to_sheet(self):
        # caller_function can be: sync_db_to_sheet, sync_stock_from_sheet_to_db,
        self.handle(update_sheet=False, fields=("stock", ))

    def sync_price_from_db_to_sheet(self):
        # caller_function can be: sync_db_to_sheet, sync_stock_from_sheet_to_db,
        self.handle(update_sheet=True, fields=("price", ))

    def sync_price_from_sheet_to_db(self):
        # caller_function can be: sync_db_to_sheet, sync_stock_from_sheet_to_db,
        self.handle(update_sheet=False, fields=("price", ))

    def handle(self, update_sheet=False, fields=tuple(), allow_all=True):
        self.write_mode = update_sheet
        self.allow_all = allow_all
        workbook = client.open_by_key(self.sheet_id)
        sheets = workbook.worksheets()
        for sheet in sheets:
            if sheet.title in self.skippable_sheets:
                continue
            self.extract_sheet(sheet, fields=fields)
        pprint(dict(self.analytics))
        pprint(dict(self.reporting))

    def extract_sheet(self, sheet, fields):
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
                self.read_stock_and_price(row, fields=fields)

    def update_row(self, worksheet, pc):
        out = [
            ["partner",	"stock_id",	'partner_sku',	"product_id", "product",	"stock",	"online_price",	"retail_price"]
        ]
        qs = StockRecord.objects.filter(product__product_class=pc).order_by('id')
        count = qs.count()
        sr: StockRecord
        for sr in qs:
            out.append(
                [sr.partner.name, sr.id, sr.partner_sku, sr.product_id, sr.product.get_title(), sr.num_in_stock, sr.cost_price, sr.price_retail]
            )
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

    def read_stock_and_price(self, row, fields) -> None:
        partner: Partner = self.get_partner(name=row['partner'].upper())
        partner_name = row['partner'].upper()
        stock_id = row['stock_id']
        stock: StockRecord = self.shared_memory['partner_stocks'][partner_name][stock_id]
        if 'stock' in fields and row['stock']:
            stock.num_in_stock = row['stock']
        if 'price' in fields and row['online_price'] and row['retail_price']:
            stock.cost_tax = row['online_price']                                            # assuming incl tax is entered
            stock.price_excl_tax = float(math.floor(stock.cost_price * 100 / (100 + stock.product.tax)))
            stock.price_retail = row['retail_price']
        stock.save()



