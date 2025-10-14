"""Script to fetch data from DefiLlama's fundamental data."""

import os

from governenv.defillama import DefiLlama
from governenv.constants import DATA_DIR

os.makedirs(DATA_DIR / "defillama", exist_ok=True)


defillama = DefiLlama()
defillama.get_protocol_fees()
defillama.get_protocol_tvls()
defillama.get_protocol_users(type_str="users")
defillama.get_protocol_users(type_str="txs")
# defillama.get_protocol_users(type_str="newusers")
defillama.get_protocol_users(type_str="gas")
