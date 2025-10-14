"""Class for Etherscan API interaction."""

import os

import requests


class Etherscan:
    """Class for Etherscan API interaction."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.etherscan.io/v2/api"

    def get_contract_creation(self, contract_address: str, chain_id: str = "1") -> dict:
        """Get contract creation information."""

        results = {}
        params = {
            "chainid": chain_id,
            "module": "contract",
            "action": "getcontractcreation",
            "contractaddresses": contract_address,
            "apikey": self.api_key,
        }
        response = requests.get(self.base_url, params=params, timeout=60)
        data = response.json()
        results[contract_address] = data["result"]
        return results


if __name__ == "__main__":
    ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

    etherscan = Etherscan(api_key=ETHERSCAN_API_KEY)
    res = etherscan.get_contract_creation(
        "0xB83c27805aAcA5C7082eB45C868d955Cf04C337F".lower(),
    )
    print(res)
