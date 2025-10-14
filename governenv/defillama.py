"""Script to interact with DefiLlama API."""

import time
import json
import os
from typing import Literal, Optional

import pandas as pd
import requests
from tqdm import tqdm

from governenv.constants import DATA_DIR
from governenv.settings import DEFILLAMA_API_KEY

os.makedirs(DATA_DIR / "defillama", exist_ok=True)


class DefiLlama:
    """Class to interact with DefiLlama API."""

    BASE_URL = "https://api.llama.fi"
    PRO_URL = "https://pro-api.llama.fi"

    def __init__(self):
        self.protocols = self._get_protocols()
        self.fee_protocols = self._get_fee_protocols()
        self.user_protocols = self._get_user_protocols()

    # Method to fetch list
    def _get_protocols(
        self, save_path: str = DATA_DIR / "defillama_protocols.csv"
    ) -> pd.DataFrame:
        """Fetch the list of DeFi protocols."""
        if os.path.exists(save_path):
            return pd.read_csv(save_path)
        url = f"{self.BASE_URL}/protocols"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        ptc = pd.DataFrame(data)
        ptc.to_csv(save_path, index=False)
        return ptc

    def _get_fee_protocols(self) -> pd.DataFrame:
        """Fetch the list of protocols with fee data."""
        if os.path.exists(DATA_DIR / "defillama_fee_protocols.csv"):
            return pd.read_csv(DATA_DIR / "defillama_fee_protocols.csv")
        url = f"{self.BASE_URL}/overview/fees"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        ptc = pd.DataFrame(data["protocols"])
        ptc.to_csv(DATA_DIR / "defillama_fee_protocols.csv", index=False)
        return ptc

    def _get_user_protocols(self) -> dict:
        """Fetch the list of protocols with user data."""
        if os.path.exists(DATA_DIR / "defillama_user_protocols.json"):
            with open(
                DATA_DIR / "defillama_user_protocols.json", "r", encoding="utf-8"
            ) as f:
                data = json.load(f)
            return data

        url = f"{self.PRO_URL}/{DEFILLAMA_API_KEY}/api/activeUsers"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        with open(
            DATA_DIR / "defillama_user_protocols.json", "w", encoding="utf-8"
        ) as f:
            json.dump(data, f, indent=4)
        return data

    # Fetch protocol TVL
    def _get_protocol_tvl(
        self,
        protocol: str,
        save_path: str,
    ) -> None:
        """Fetch the TVL data for a specific protocol."""
        # to avoid rate limiting
        time.sleep(1)

        # fetch data
        try:
            url = f"{self.BASE_URL}/protocol/{protocol}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            with open(save_path / f"{protocol}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except requests.RequestException as e:
            time.sleep(5)
            print(f"Error fetching TVL data for {protocol}: {e}")

    def get_protocol_tvls(self) -> None:
        """Fetch TVL data for all protocols."""
        path = DATA_DIR / "defillama" / "tvls"
        os.makedirs(path, exist_ok=True)

        ptc_without_parent = self.protocols.loc[
            self.protocols["parentProtocolSlug"].isna(), "slug"
        ].tolist()
        ptc_with_parent = (
            self.protocols.loc[
                self.protocols["parentProtocolSlug"].notna(), "parentProtocolSlug"
            ]
            .unique()
            .tolist()
        )
        ptc_to_fetch = set(ptc_without_parent) | set(ptc_with_parent)

        # interrupt and resume support
        if os.path.exists(path):
            existing_files = os.listdir(path)
            existing_protocols = {f.replace(".json", "") for f in existing_files}
            ptc_to_fetch = ptc_to_fetch - existing_protocols

        for protocol in tqdm(ptc_to_fetch, total=len(ptc_to_fetch)):
            self._get_protocol_tvl(protocol, path)

    # Fetch protocol fee
    def _get_protocol_fee(
        self,
        protocol: str,
        save_path: str,
    ) -> None:
        """Fetch the fee data for a specific protocol."""
        # to avoid rate limiting
        time.sleep(2)

        # fetch data
        try:
            url = f"{self.BASE_URL}/summary/fees/{protocol}"
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            with open(save_path / f"{protocol}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except requests.RequestException as e:
            time.sleep(5)
            print(f"Error fetching fee data for {protocol}: {e}")

    def get_protocol_fees(self) -> None:
        """Fetch fee data for all protocols."""
        path = DATA_DIR / "defillama" / "fees"
        os.makedirs(path, exist_ok=True)

        protocol_fees = self.fee_protocols["slug"].tolist()
        # interrupt and resume support
        if os.path.exists(path):
            existing_files = os.listdir(path)
            existing_protocols = {f.replace(".json", "") for f in existing_files}
            protocol_fees = set(protocol_fees) - existing_protocols

        for protocol in tqdm(protocol_fees, total=len(protocol_fees)):
            self._get_protocol_fee(protocol, path)

    # Fetch protocol users
    def _get_protocol_user(
        self,
        protocol_id: str,
        save_path: str,
        type_str: Literal["users", "txs", "gas", "newusers"],
    ) -> None:
        """Fetch the list of protocols with user data."""

        url = (
            f"{self.PRO_URL}/{DEFILLAMA_API_KEY}/api/userData/{type_str}/{protocol_id}"
        )
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        os.makedirs(save_path, exist_ok=True)
        if data:
            with open(save_path / f"{protocol_id}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

    def get_protocol_users(
        self, type_str: Literal["users", "txs", "gas", "newusers"]
    ) -> None:
        """Fetch user data for all protocols."""
        path = DATA_DIR / "defillama" / "users" / type_str
        os.makedirs(path, exist_ok=True)

        # handle protocols with parent protocols
        protocol_users = self.user_protocols.keys()
        id_protocol_users = [idx for idx in protocol_users if "#" not in idx]
        parent_protocol_users = [
            idx.split("#")[-1] for idx in protocol_users if "parent#" in idx
        ]
        id_parent_protocol_users = self.protocols.loc[
            self.protocols["parentProtocolSlug"].isin(parent_protocol_users), "id"
        ].tolist()

        id_protocol_users = set(id_protocol_users) | set(id_parent_protocol_users)

        # interrupt and resume support
        if os.path.exists(path):
            existing_files = os.listdir(path)
            existing_protocols = {f.replace(".json", "") for f in existing_files}
            id_protocol_users = id_protocol_users - existing_protocols

        for protocol in tqdm(id_protocol_users, total=len(id_protocol_users)):
            self._get_protocol_user(protocol, path, type_str)

    # Fetch block by timestamp
    def get_block_by_timestamp(self, timestamp: int) -> Optional[int]:
        """
        Function to get the block by timestamp
        """

        length = 0
        result = {"timestamp": None, "height": None}

        while length == 0:
            result = requests.get(
                f"{self.PRO_URL}/{DEFILLAMA_API_KEY}/coins/block/ethereum/{timestamp}",
                timeout=60,
            ).json()
            length = len(result)

        return result["height"]


if __name__ == "__main__":
    defillama = DefiLlama()
    block = defillama.get_block_by_timestamp(1630008000)
