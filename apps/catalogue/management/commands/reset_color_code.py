from django.core.management import BaseCommand

from apps.catalogue.models import ProductAttribute, ProductAttributeValue

data = """Alert Tan=#934D30
BLACK=#000000
BLUE=#0000FF
Black=#000000
Black=#000000
Gray=#808080
Yellow-Brown=#523F21
Black=#000000
White=#FFFFFF
Blue=#0000FF
Blue=#0000FF
Green=#043A14
Bourbon=#af6c3e
Brown=#623C1F
Brown and White=#623C1F,#FFFFFF
Brown=#623C1F
Green=#043A14
Brownish Red=#A6594B
Bull Shot=#674342
Burnt Umber=#8A3324
COFFEE=#60392F
CREAM=#C57644
Cashmere=#F1E6DD
Champange=#F7E7CE
Chelsea Gem=#95532f
Christine=#C3541F
Concrete=#7F8076
Cornflakes=#f0e68c
Crater=401E2B
Croma=#0047bb
Deep Oak=#4F2412
Espresso=#3C2218
Fiery Orange=#D01C1F
Foggy Grey=#a7a69d
GRAY=#808080
GREEN=#043A14
Gray=#808080
Green=#043A14
Green=#043A14
Blue=#0000FF
Grey=#808080
Halloween Orange=#FF7518
Hash=#A4AEA8
Lite Yellow=#FFA400
Meroon Seat=#510400
Wooden Colour Table=#745D43
Meteor=#bb7431
Nera=#000000
Nera=#000000
Espresso=#3C2218
Croma=#0047bb
Snova=#f6cf00
Champange=#F7E7CE
Concrete=#7F8076
Cornflakes=#f0e68c
Crater=401E2B
Yellow=#FFB70B
Red=#FF0000
Off White=#F8F0E3
PINK=#ECB2B3
Paarl=#864b36
Paper Coating Gray=#fbfbf8
Pastel Grey=#CCCCC4
Peru Tan=#7F3A02
Pink=#E2B8B4
Pink=#E2B8B4
Brown=#623C1F
Blue=#0000FF
Green=#043A14
Gray=#808080
Potters Clay=#875632
RED=#FF0000
ROSE=#E22E43
Red=#FF0000
Red=#FF0000
Black=#000000
Brown=#623C1F
Green=#043A14
Blue=#0000FF
Red=#FF0000
Black=#000000
White=#FFFFFF
Blue=#0000FF
Red=#FF0000
Green=#043A14
Gray=#808080
Red=#FF0000
Yellow=#FFB70B
Brown=#623C1F
Reddish Orange=#F73718
Rich Gold=#ECBE07
Rodeo Dust=#c7a384
Rope=#8e593c
Rust=#AE3415
Saddle Brown=#8B4513
Silver=#C0C0C0
Snova=#f6cf00
Teak Finish=#c29467
Tenne=#CD5700
WHITE=#FFFFFF
White=#FFFFFF
White Aand Teak=#FFFFFF,#c29467
White and Dark Brown=#FFFFFF,#5C4033.
White and Dark Green="#FFFFFF,#006400"
White and Gold Shading=#FFFFFF,#FFD700
White and Gray=#FFFFFF,#808080
Wooden Finish=#731b00
YELLOW=#FFB70B
Yellow=#FFB70B
Yellow-Brown=#cc9966""".split('\n')


class Command(BaseCommand):
    
    def handle(self, *args, **options):
        text_color_attrs = ProductAttribute.objects.filter(code='color')
        color_wheel = {}
        color_attr = ProductAttribute.objects.filter(type=ProductAttribute.COLOR).select_related('product_class').first()
        for line in data:
            color, _hex = line.split('=')
            hex_secondary = None
            if ',' in _hex:
                _hex, hex_secondary = _hex.split(',')
            color_wheel[color] = {'primary': _hex, 'secondary': hex_secondary}
        for text_color in text_color_attrs:
            pass
        return
