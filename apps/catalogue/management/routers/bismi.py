import json
import os
from django.conf import settings

import requests

cookies = {
    'BismiCart': 'CartId=b3728b57-4e45-4134-8c46-ff0b48b22bf6',
    'f': 'a1Zb980sAW2XIhCy_T3wzeVYT7EMoR2bUpz8ikUB035KKT3mz2fDN2W7xYJl3dfZI962SUPjV5OI7q3ct9vT6reWhIOqea4DRc3M7ZFAJ_Y1',
    'G_ENABLED_IDPS': 'google',
    '_ga': 'GA1.2.1982166732.1621330343',
    '_gid': 'GA1.2.1488612429.1621330343',
    'isPopupOpen': 'No',
    '_ga_XH4766K85K': 'GS1.1.1621330342.1.0.1621330344.0',
}

headers = {
    'Connection': 'keep-alive',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
    'Accept': 'application/json, text/plain, */*',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 '
                  'Safari/537.36',
    'Content-Type': 'application/json',
    'Origin': 'https://www.bismideal.com',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://www.bismideal.com/Grocery/product-list?catId=VkZaRk9WQlJQVDA9&subCatId=VkZkak9WQlJQVDA9&pMin'
               '=VkRGRk9WQlJQVDA9&pMax=VkZkd2JrNVJQVDA9&oMin=VkZWRk9WQlJQVDA9&oMax=VkZWRk9WQlJQVDA9&type'
               '=VkZaRk9WQlJQVDA9&page=1',
    'Accept-Language': 'en-US,en;q=0.9,ml-IN;q=0.8,ml;q=0.7',
}


class BismiStore(object):

    def cached_fetch(self, slug, callback_function):
        directory = os.path.join(settings.BASE_DIR, 'public', 'dataset', 'bismi-data')
        if not os.path.exists(directory):
            os.makedirs(directory)

        filename_slug = slug.replace(os.path.sep, '_')
        file_name = f'_{filename_slug}._.json'
        filepath = os.path.join(directory, file_name)

        if not os.path.exists(filepath):
            print(f"Fetching {slug} from https://www.bismideal.com .....")
            response_json = callback_function().json()
            with open(filepath, 'w') as fp:
                json.dump(response_json, fp)
        else:
            with open(filepath, 'r') as fp:
                response_json = json.load(fp)

        return response_json

    def fetch_categories(self, ):
        data = {
            "BusinessId": 1
        }

        return self.cached_fetch('categories', lambda: requests.post(
            'https://www.bismideal.com/Manage/fetch-featured-category-with-subcategory?catId=VkZaRk9WQlJQVDA9'
            '&subCatId=VkZkak9WQlJQVDA9&pMin=VkRGRk9WQlJQVDA9&pMax=VkZkd2JrNVJQVDA9&oMin=VkZWRk9WQlJQVDA9&oMax'
            '=VkZWRk9WQlJQVDA9&type=VkZaRk9WQlJQVDA9&page=1',
            headers=headers, cookies=cookies, data=json.dumps(data)))

    def fetch_product(self, slug, category_id, group_id, page_number=1, page_size=24):
        _data = {
            "StoreID": 5,
            "PageNumber": str(page_number),
            "PageSize": page_size,
            "type": "1",
            "subBannerId": 0,
            "CategoryID": str(category_id),
            "GroupID": str(group_id)
        }

        lazy_response = lambda: print("Fetching Products from https://www.bismideal.com .....") or requests.post(
            'https://www.bismideal.com/Manage/product-list', headers=headers, cookies=cookies, data=json.dumps(_data))

        product_slug = f'product__{slug}__{category_id}_{group_id}_{page_number}_{page_size}'

        # NB. Original query string below. It seems impossible to parse and
        # reproduce query strings 100% accurately so the one below is given
        # in case the reproduced version is not "correct".
        # response = requests.post('https://www.bismideal.com/Grocery/product-list?catId=VkZaRk9WQlJQVDA9&subCatId=VkZkak9WQlJQVDA9&pMin=VkRGRk9WQlJQVDA9&pMax=VkZkd2JrNVJQVDA9&oMin=VkZWRk9WQlJQVDA9&oMax=VkZWRk9WQlJQVDA9&type=VkZaRk9WQlJQVDA9&page=1', headers=headers, cookies=cookies, data=data)

        return self.cached_fetch(product_slug, lazy_response)




