from typing import Optional

import urllib3
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.management import BaseCommand
from django.db import models
from oscar.apps.catalogue.models import ProductImage

from apps.catalogue.management.commands.wp import bcolors
from apps.catalogue.models import Product

data = """7706	Grab Bar - 450MM	standalone	Special Products
7701	One Piece Toilet - Wipro (S-Trap)	child	One Piece Toilet
7700	One Piece Toilet - Wipro (S-Trap)	child	One Piece Toilet
7699	One Piece Toilet - Wipro	parent	One Piece Toilet
7698	One Piece Toilet - Alex (S-Trap)	child	One Piece Toilet
7697	One Piece Toilet - Alex	parent	One Piece Toilet
7696	One Piece Toilet - Beetle (S-Trap)	child	One Piece Toilet
7695	One Piece Toilet - Beetle	parent	One Piece Toilet
7694	One Piece Toilet - Clair (S-Trap)	child	One Piece Toilet
7693	One Piece Toilet - Clair	parent	One Piece Toilet
7692	One Piece Toilet - Eva (S-Trap)	child	One Piece Toilet
7691	One Piece Toilet - Eva 	parent	One Piece Toilet
7689	Rimless One Piece Toilet - Natalia (S-Trap)	child	One Piece Toilet
7688	Rimless One Piece Toilet - Natalia (S-Trap)	parent	One Piece Toilet
7687	Rimless One Piece Toilet - Neon (S-Trap)	child	One Piece Toilet
7686	Rimless One Piece Toilet - Neon (S-Trap)	parent	One Piece Toilet
7685	Rimless One Piece Toilet - Opal (S-Trap)	child	One Piece Toilet
7683	One Piece Toilet - Palestine	parent	One Piece Toilet
7679	One Piece Toilet - Victoria (S-Trap)	child	One Piece Toilet
7678	One Piece Toilet - Victoria (S-Trap)	parent	One Piece Toilet
7677	One Piece Toilet - Viva (Syphonic) (S-trap)	child	One Piece Toilet
7676	One Piece Toilet - Viva (Syphonic) (S-trap)	parent	One Piece Toilet
7675	One Piece Toilet - Rolex (Syphonic) (S-Trap)	child	One Piece Toilet
7674	One Piece Toilet - Rolex (Syphonic) (S-Trap)	parent	One Piece Toilet
7673	One Piece Washdown Toilet - Vega	child	One Piece Toilet
7672	One Piece Washdown Toilet - Vega	child	One Piece Toilet
7671	One Piece Washdown Toilet - Vega	parent	One Piece Toilet
7670	One Piece Toilet - Force	child	One Piece Toilet
7669	One Piece Toilet - Force	child	One Piece Toilet
7668	One Piece Toilet - Force	parent	One Piece Toilet
7667	One Piece Toilet - Grand P - Trap	child	One Piece Toilet
7666	One Piece Toilet - Grand S - Trap	child	One Piece Toilet
7665	One Piece Toilet - Grand	parent	One Piece Toilet
7661	One Piece Toilet - Simona	parent	One Piece Toilet
7660	One Piece Toilet - Grace	parent	One Piece Toilet
7659	One Piece Toilet - Spice	parent	One Piece Toilet
7658	One Piece Toilet - Sesto	parent	One Piece Toilet
7657	One Piece Toilet - Wipro (S-Trap)	child	One Piece Toilet
7656	One Piece Toilet - Wipro (S-Trap)	child	One Piece Toilet
7655	One Piece Toilet - Wipro	parent	One Piece Toilet
7654	One Piece Toilet - Alex (S-Trap)	child	One Piece Toilet
7653	One Piece Toilet - Alex	parent	One Piece Toilet
7652	One Piece Toilet - Beetle (S-Trap)	child	One Piece Toilet
7651	One Piece Toilet - Beetle	parent	One Piece Toilet
7650	One Piece Toilet - Clair (S-Trap)	child	One Piece Toilet
7649	One Piece Toilet - Clair	parent	One Piece Toilet
7648	One Piece Toilet - Eva (S-Trap)	child	One Piece Toilet
7647	One Piece Toilet - Eva 	parent	One Piece Toilet
7646	One Piece Toilet - Libia	parent	One Piece Toilet
7645	Rimless One Piece Toilet - Natalia (S-Trap)	child	One Piece Toilet
7644	Rimless One Piece Toilet - Natalia (S-Trap)	parent	One Piece Toilet
7643	Rimless One Piece Toilet - Neon (S-Trap)	child	One Piece Toilet
7642	Rimless One Piece Toilet - Neon (S-Trap)	parent	One Piece Toilet
7641	Rimless One Piece Toilet - Opal (S-Trap)	child	One Piece Toilet
7640	Rimless One Piece Toilet - Opal	parent	One Piece Toilet
7639	One Piece Toilet - Palestine	parent	One Piece Toilet
7638	One Piece Toilet - Space	parent	One Piece Toilet
7636	One Piece Toilet - Spania (S-Trap)	parent	One Piece Toilet
7635	One Piece Toilet - Victoria (S-Trap)	child	One Piece Toilet
7634	One Piece Toilet - Victoria (S-Trap)	parent	One Piece Toilet
7633	One Piece Toilet - Viva (Syphonic) (S-trap)	child	One Piece Toilet
7632	One Piece Toilet - Viva (Syphonic) (S-trap)	parent	One Piece Toilet
7631	One Piece Toilet - Rolex (Syphonic) (S-Trap)	child	One Piece Toilet
7630	One Piece Toilet - Rolex (Syphonic) (S-Trap)	parent	One Piece Toilet
7629	One Piece Washdown Toilet - Vega	child	One Piece Toilet
7628	One Piece Washdown Toilet - Vega	child	One Piece Toilet
7627	One Piece Washdown Toilet - Vega	parent	One Piece Toilet
7626	One Piece Toilet - Force	child	One Piece Toilet
7625	One Piece Toilet - Force	child	One Piece Toilet
7624	One Piece Toilet - Force	parent	One Piece Toilet
7623	One Piece Toilet - Grand P - Trap	child	One Piece Toilet
7622	One Piece Toilet - Grand S - Trap	child	One Piece Toilet
7621	One Piece Toilet - Grand	parent	One Piece Toilet
7620	One Piece Toilet - Winger P - Trap	child	One Piece Toilet
7619	One Piece Toilet - Winger	parent	One Piece Toilet
7618	Baby Toilet Seat Cover Yellow	child	Toilet Seat Cover
7617	Baby Toilet Seat Cover Rose	child	Toilet Seat Cover
7616	Baby Toilet Seat Cover Green	child	Toilet Seat Cover
7615	Grab Bar - 450MM	standalone	Special Products
7614	Jazz D200 Double Bowl with Drainer Quartz Kitchen Sink - 46X20 Croma	child	Kitchen Sink
7611	Jazz D200 Double Bowl with Drainer Quartz Kitchen Sink - 46X20 Croma	child	Kitchen Sink
6749	Vivaldi Single Bowl with Drainer Quartz Kitchen Sink - 40"X20"	child	Kitchen Sink
6738	Vivaldi Single Bowl with Drainer Quartz Kitchen Sink - 40"X20"	child	Kitchen Sink
6727	Vivaldi Single Bowl with Drainer Quartz Kitchen Sink - 40"X20"	child	Kitchen Sink
5396	Enigma D100 Single Bowl with Drainer Quartz  Kitchen Sink  - 34"X20"	child	Kitchen Sink
5385	Enigma D100 Single Bowl with Drainer Quartz  Kitchen Sink  - 34"X20"	child	Kitchen Sink
5374	Enigma D100 Single Bowl with Drainer Quartz  Kitchen Sink  - 34"X20"	child	Kitchen Sink
5363	Enigma D100 Single Bowl with Drainer Quartz  Kitchen Sink  - 34"X20"	child	Kitchen Sink
5352	Enigma D100 Single Bowl with Drainer Quartz  Kitchen Sink  - 34"X20"	child	Kitchen Sink
5341	Enigma D100 Single Bowl with Drainer Quartz  Kitchen Sink  - 34"X20"	child	Kitchen Sink
5330	Enigma D100 Single Bowl with Drainer Quartz  Kitchen Sink  - 34"X20"	child	Kitchen Sink
5319	Enigma D100 Single Bowl with Drainer Quartz Kitchen Sink - 34"X20"	child	Kitchen Sink
5308	Enigma D100 Single Bowl with Drainer Quartz  Kitchen Sink - 34"X20"	child	Kitchen Sink
4969	One Piece Toilet - Rolex (Syphonic) (S-Trap)	child	None
4968	One Piece Toilet - Rolex (Syphonic) (S-Trap)	child	None
4965	One Piece Toilet - Viva (Syphonic) (S-trap)	child	None
4964	One Piece Toilet - Viva (Syphonic) (S-trap)	child	None
4960	One Piece Toilet - Wipro (P-Trap)	child	None
4959	One Piece Toilet - Wipro (P-Trap)	child	None
4958	One Piece Toilet - Wipro (P-Trap)	child	None
4954	One Piece Toilet - Eva (S-Trap)	child	None
4953	One Piece Toilet - Eva (S-Trap)	child	None
4951	One Piece Toilet - Clair (S-Trap)	child	None
4950	One Piece Toilet - Clair (S-Trap)	child	None
4948	One Piece Toilet - Beetle (S-Trap)	child	None
4947	One Piece Toilet - Beetle (S-Trap)	child	None
4945	One Piece Toilet - Alex (S-Trap)	child	None
4944	One Piece Toilet - Alex (S-Trap)	child	None
4943	One Piece Toilet - Spania (S-Trap)	child	None
4942	One Piece Toilet - Spania (S-Trap)	child	None
4939	One Piece Toilet - Opal (S-Trap)	child	None
4938	One Piece Toilet - Opal (S-Trap)	child	None
4937	One Piece Toilet - Neon (S-Trap)	child	None
4936	One Piece Toilet - Neon (S-Trap)	child	None
4935	One Piece Toilet - Natalia (S-Trap)	child	None
4934	One Piece Toilet - Natalia (S-Trap)	child	None
4932	One Piece Toilet - Victoria (S-Trap)	child	None
4931	One Piece Toilet - Victoria (S-Trap)	child	None
4856	One Piece Toilet - Wipro (S-Trap)	child	None
4855	One Piece Toilet - Wipro (S-Trap)	child	None
4854	One Piece Toilet - Wipro (S-Trap)	child	None
4277	Plato Ceiling Rain Shower- Super Slim	child	Showers
4276	Plato Ceiling Rain Shower- Super Slim	child	Showers
4275	Plato Ceiling Rain Shower- Super Slim	child	Showers
4274	Plato Ceiling Rain Shower- Super Slim	child	Showers
4273	Plato Ceiling Rain Shower- Super Slim	child	Showers
4272	Plato Ceiling Rain Shower- Super Slim	child	Showers
4271	Plato Ceiling Rain Shower- Super Slim	child	Showers
4270	Plato Ceiling Rain Shower- Super Slim	child	Showers
4268	Plato Shower Arm - Lavanya Cube - 600 MM	child	Accessories
4267	Plato Shower Arm - Lavanya Cube - 450 MM	child	Accessories
4266	Plato Shower Arm - Lavanya Cube - 375 MM	child	Accessories
4265	Plato Shower Arm - Lavanya Cube - 300 MM	child	Accessories
4264	Plato Shower Arm - Lavanya Cube - 225 MM	child	Accessories"""


def fetch_image(url: str, instance: models.Model, field: str, name: Optional[str] = None):
    try:
        print(url)
        conn = urllib3.PoolManager()
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.flush()
        img_temp.write(conn.request('GET', url).data)
        img_temp.flush()
        img_format = url.split('.')[-1]
        if name is None:
            name = url.split('/')[-1]
        if not name.endswith(img_format):
            name += f'.{img_format}'
        (getattr(instance, field)).save(name, File(img_temp))
        print((getattr(instance, field)).url)
        print(instance)
    except Exception as e:
        bcolors.eprint(e)
        print(url, instance, field, name)
    return instance


class Command(BaseCommand):

    def handle(self, *args, **options):
        global data
        lines = data.split('\n')
        for line in lines:
            _id, _product_name, _structure, _pclass_name = line.split('	')
            p = Product.objects.get(pk=_id)
            print(_id, _product_name)
            while True:
                url = input("URL : ")
                if not url:
                    break
                pi = ProductImage(product=p)
                fetch_image(url, pi, field='original', name=_product_name)
