

pc = ProductClass.objects.get(name="WallHung Toilet")
pc_products = pc.products.all()
attr_len, _ = ProductAttribute.objects.get_or_create(product_class=pc, name="Length", code="length", )
attr_wid, _ = ProductAttribute.objects.get_or_create(product_class=pc, name="Width", code="width")
attr_height, _ = ProductAttribute.objects.get_or_create(product_class=pc, name="Height", code="height")
attr_dim, _ = ProductAttribute.objects.get_or_create(product_class=pc, name="Dimension", code="dimension")

for p in pc_products:
    if p.length:
        p.attr.length = str(int(p.length)) + " MM"
    if p.width:
        p.attr.width = str(int(p.width)) + " MM"
    if p.height:
        p.attr.height = str(int(p.height)) + " MM"
    dt = ""
    if p.length:
        dt += f"{int(p.length)} X "
    if p.width:
        dt += f"{int(p.width)} X "
    if p.height:
        dt += f"{int(p.height)} "
    dt = dt.rstrip(' X ') + 'MM'
    if dt:
        p.attr.dimension = dt 
    p.attr.save()



