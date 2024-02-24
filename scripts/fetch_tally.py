import requests
from governenv.settings import TALLY_API_KEY


url2 = "https://api.tally.xyz/query"
headers2 = {"Api-Key": TALLY_API_KEY}
data2 = {
    "query": "query Accounts(\n  $ids: [AccountID!],\n  $addresses: [Address!]\n) {\n  accounts(\n    ids: $ids,\n    addresses: $addresses\n  ) {\n    id\n    address\n    ens\n    twitter\n    name\n    bio\n}\n}",
    "variables": {
        "ids": ["eip155:1:0x7e90e03654732abedf89Faf87f05BcD03ACEeFdc"],
        "addresses": ["0x1234567800000000000000000000000000000abc"],
    },
}

response2 = requests.post(url2, json=data2, headers=headers2)
result = response2.json()
