#!/home/jk/.env/grocery/bin/python3
"""
    ./grupify.py
"""
import csv
from pprint import pprint



unique_data = """Material
Size
Color
Suitable
Brand
Length
Finish
Usage
Material Used
Materials Used
Quantity
Available Color
Available Colors
Primary Material
Surface Finish
Trap Size
Trap Distance
Colors
Bowl Dimensions
Single Bowl Dimensions
Left Bowl Dimensions
Right Bowl Dimensions
Trap Type
Trap Types
Dimension
Available Size
Application
Package Content
Installation Type
Series
Capacity
Colour
Material Type
Item Form
Container Type
Room Type
Thichness
Warranty
Bowl Size
Left Bowl Size
Half Bowl Dimension
Half Bowl Dimensions
Thickness
Thread Type
Inlet Connection Size
Suitable For
Dimensions (mm)
Key Feature
Right Bowl Size
Brand Name
Corner Radius
Package Contents
Key Features
Salient Features
Type
Country of Origin
Seating Height
Shelf Life
Applications
Weight
Wieght
Waste Coupling Type
Other Features"""
filename = 'public/dataset/abchauz_wp/wc-product-export-16-8-2021-1629114021490.csv'

fields = [f'Attribute {i} name' for i in range(1, 9)]



phrase = {
    'Material': 'Material',
    'Size': 'Size',
    'Color': 'Color',
    'Suitable': 'Suitable',
    'Brand': 'Brand',
    'Length': 'Length',
    'Finish': 'Finish',
    'Usage': 'Usage',
    'Material Used': 'Material',
    'Materials Used': 'Material',
    'Quantity': 'Quantity',
    'Available Color': 'Color',
    'Available Colors': 'Color',
    'Primary Material': 'Material',
    'Surface Finish': 'Surface Finish',
    'Trap Size': 'Trap Size',
    'Trap Distance': 'Trap Distance',
    'Colors': 'Color',
    'Bowl Dimensions': 'Bowl Dimension',
    'Single Bowl Dimensions': 'Single Bowl Dimension',
    'Left Bowl Dimensions': 'Left Bowl Dimension',
    'Right Bowl Dimensions': 'Right Bowl Dimension',
    'Trap Type': 'Trap Type',
    'Trap Types': 'Trap Type',
    'Dimension': 'Dimension',
    'Available Size': 'Size',
    'Application': 'Application',
    'Package Content': 'Package Content',
    'Installation Type': 'Installation Type',
    'Series': 'Series',
    'Capacity': 'Capacity',
    'Colour': 'Color',
    'Material Type': 'Material Type',
    'Item Form': 'Item Form',
    'Container Type': 'Container Type',
    'Room Type': 'Room Type',
    'Thichness': 'Thickness',
    'Warranty': 'Warranty',
    'Bowl Size': 'Bowl Size',
    'Left Bowl Size': 'Left Bowl Size',
    'Half Bowl Dimension': 'Half Bowl Dimension',
    'Half Bowl Dimensions': 'Half Bowl Dimensions',
    'Thickness': 'Thickness',
    'Thread Type': 'Thread Type',
    'Inlet Connection Size': 'Inlet Connection Size',
    'Suitable For': 'Suitable For',
    'Dimensions (mm)': 'Dimensions (mm)',
    'Key Feature': 'Key Feature',
    'Right Bowl Size': 'Right Bowl Size',
    'Brand Name': 'Brand Name',
    'Corner Radius': 'Corner Radius',
    'Package Contents': 'Package Contents',
    'Key Features': 'Key Features',
    'Salient Features': 'Salient Features',
    'Type': 'Type',
    'Country of Origin': 'Country of Origin',
    'Seating Height': 'Seating Height',
    'Shelf Life': 'Shelf Life',
    'Applications': 'Applications',
    'Weight': 'Weight',
    'Wieght': 'Weight',
    'Waste Coupling Type': 'Waste Coupling Type',
    'Other Features': 'Other Features'
}

with open(filename, 'r') as _fp:
    contents = csv.DictReader(_fp)
    dataset_container = []
    matrix = [
        set([phrase.get(line[f], line[f]) for f in fields if line[f]])
        for line in contents]
    for line in matrix:
        if line and line not in dataset_container:
            dataset_container.append(line)
    for p in dataset_container:
        print(p)



