file = open("product_attr_data.json", "r")
content = "".join(file.read())
file.close()
file2 = open("product_attr_data2.json", "w")
file2.write(content)
file2.close()

