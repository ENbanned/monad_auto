from dataclasses import dataclass
from utils.classes import AutoRepr, Singleton
from utils.files.file_utils import read_json
from .config import SETTINGS_FILE

@dataclass
class FromTo:
    from_: int | float
    to_: int | float

@dataclass
class WalletCSV:
    header = ['private_key', 'proxy', 'name']

    def __init__(self, private_key: str, proxy: str = '', name: str = ''):
        self.private_key = private_key
        self.proxy = proxy
        self.name = name


class Settings(Singleton, AutoRepr):
    def __init__(self):
        json_data = read_json(path=SETTINGS_FILE)

        self.minimal_balance: float = json_data['minimal_balance']
        self.oklink_api_key: str = json_data['oklink_api_key']
        self.blockvision_api_key = json_data['blockvision_api_key']
        self.capsolver_api_key: str = json_data['capsolver_api_key']
        self.mexc_api_key: str = json_data['mexc_api_key']
        self.mexc_secret_key: str = json_data['mexc_secret_key']
        
        self.number_of_swaps: FromTo = FromTo(
            from_=json_data['number_of_swaps']['from'], to_=json_data['number_of_swaps']['to'])

        self.initial_actions_delay: FromTo = FromTo(
            from_=json_data['initial_actions_delay']['from'], to_=json_data['initial_actions_delay']['to']
        )
        self.activity_actions_delay: FromTo = FromTo(
            from_=json_data['activity_actions_delay']['from'], to_=json_data['activity_actions_delay']['to']
        )

        self.mod_amount_for_swap: FromTo = FromTo(
            from_=json_data['mod_amount_for_swap']['from'], to_=json_data['mod_amount_for_swap']['to']
        )

        self.mod_amount_for_stake: FromTo = FromTo(
            from_=json_data['mod_amount_for_stake']['from'], to_=json_data['mod_amount_for_stake']['to']
        )
        