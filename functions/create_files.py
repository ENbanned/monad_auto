import os
import csv
import json

from data import config
from data.models import WalletCSV

from utils.files.file_utils import touch, write_json, read_json, update_dict


def create_files():
    touch(path=config.FILES_DIR)
    touch(path=config.LOG_FILE, file=True)
    touch(path=config.ERRORS_FILE, file=True)

    if not os.path.exists(config.IMPORT_FILE):
        with open(config.IMPORT_FILE, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(WalletCSV.header)

    try:
        current_settings: dict | None = read_json(path=config.SETTINGS_FILE)
    except Exception:
        current_settings = {}

    settings = {
        'minimal_balance': 0.03,
        'oklink_api_key': '',
        'blockvision_api_key': '',
        'capsolver_api_key': '',
        'mexc_api_key': '',
        'mexc_secret_key': '',
        'number_of_swaps': {'from': 5, 'to': 15},
        'initial_actions_delay': {'from': 1800, 'to': 10800},
        'activity_actions_delay': {'from': 18000, 'to': 36000},
        'mod_amount_for_swap': {'from': 0.01, 'to': 0.03},
        'mod_amount_for_stake': {'from': 0.01, 'to': 0.02}
    }
    write_json(path=config.SETTINGS_FILE, obj=update_dict(modifiable=current_settings, template=settings), indent=2)


create_files()