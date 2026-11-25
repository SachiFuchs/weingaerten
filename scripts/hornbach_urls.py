import glob, json
fs = glob.glob(r"c:\Development\weingaerten\catalog\imported_material\hornbach-*.json")
urls = [json.load(open(f, encoding="utf-8"))["url"] for f in fs]
json.dump([u for u in urls if u], open(r"c:\Development\weingaerten\scripts\hornbach_urls.json", "w"))
