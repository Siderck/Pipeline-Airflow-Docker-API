import pandas as pd
from datetime import datetime
import requests
import os
import json

# Configurar la fecha actual
DATE = str(datetime.today().date()).replace('-', '')

def getKeyFromItem(item, key):
    return str(item[key]).replace(' ', '').strip() if item.get(key) else "null"

# Función para realizar el ETL
def get_most_relevant_item_by_category(category):
    category = "MLA1577"
    url = f"https://api.mercadolibre.com/sites/MLA/search?category={category}#json"
    response = requests.get(url).text
    response = json.loads(response)
    data = response["results"]

    # Crear una lista para almacenar los datos
    records = []

    for item in data:
        _id = getKeyFromItem(item, 'id')
        title = getKeyFromItem(item, 'title')
        price = float(getKeyFromItem(item, 'price')) if getKeyFromItem(item, 'price') != "null" else None
        sold_quantity = int(getKeyFromItem(item, 'sold_quantity')) if getKeyFromItem(item, 'sold_quantity') != "null" else None
        thumbnail = getKeyFromItem(item, 'thumbnail')

        records.append({
            'id': _id,
            'title': title,
            'price': price,
            'sold_quantity': sold_quantity,
            'thumbnail': thumbnail,
            'date': DATE
        })

    # Convertir a DataFrame
    df = pd.DataFrame(records)

    # Crear el directorio si no existe
    output_dir = r"D:\airflow-docker\tmp"
    os.makedirs(output_dir, exist_ok=True)

    # Guardar como archivo TSV
    file_path = os.path.join(output_dir, "file.tsv")
    df.to_csv(file_path, sep='\t', index=False)

def main():
    CATEGORY = "MLA1577"
    get_most_relevant_item_by_category(CATEGORY)

main()
