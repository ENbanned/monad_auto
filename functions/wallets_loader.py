import csv
from data.config import IMPORT_FILE

def load_wallets():
    wallets = []
    try:
        with open(IMPORT_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                wallets.append(row)
    except Exception as e:
        raise Exception(f"Ошибка загрузки кошельков: {e}")
    return wallets


