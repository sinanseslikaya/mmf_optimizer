import json

def get_unique_categories():
    with open('fundYields.json') as f:
        data = json.load(f)

    categories = set()
    for fund in data:
        categories.add(fund['category'])

    return categories

unique_categories = get_unique_categories()
print(unique_categories)