# dao-governance

## Setup

```
git clone https://github.com/xujiahuayz/dao-governance.git
cd dao-governance
```

### Give execute permission to your script and then run `setup_repo.sh`

```
chmod +x setup_repo.sh
./setup_repo.sh
. venv/bin/activate
```

or follow the step-by-step instructions below between the two horizontal rules:

---

#### Create a python virtual environment

- MacOS / Linux

```bash
python3 -m venv venv
```

- Windows

```bash
python -m venv venv
```

#### Activate the virtual environment

- MacOS / Linux

```bash
. venv/bin/activate
```

- Windows (in Command Prompt, NOT Powershell)

```bash
venv\Scripts\activate.bat
```

#### Install toml

```
pip install toml
```

#### Install the project in editable mode

```bash
pip install -e ".[dev]"
```

## Set up the environmental variables

put your APIs in `.env`:

```
COINGLASS_SECRET="abc123"
KAIKO_API_KEY="abc123"
TALLY_API_KEY="xxx"
SNAPSHOT_API_KEY="aaa"
OPENAI_API_KEY="sk-xxx"
HEADERS="{xxxxx}"
```

```
export $(cat .env | xargs)
```

## Data Feching

### fetch snapshot space, proposal, and network data

```
python scripts/fetch/fetch_proposals.py
```

- Output: 
  - data/snapshot.json.gz
  - data/snapshot_spaces.json.gz
  - data/snapshot_networks.json.gz

### fetch coingecko data

```
python scripts/fetch/fetch_coingecko.py
```
- Output:
  - data/coingecko_coins.csv
  - data/coingecko/coins/*.json
  - data/coingecko/market_charts/*.json


### fetch risk-free rate

```
python scripts/fetch/fetch_rf.py
```
- Output: 
  - data/rf.csv

### fetch ethereum smart contract and label data from snowflake flipside

- Output: 
  - data/smart_contracts_eth.json.gz
  - data/labels_smart_contracts_eth.json.gz

### fetch on-chain delegation
```
python scripts/fetch/fetch_delegations_onchain.py
```
- Output:
  - data/snapshot_set_delegation_onchain.jsonl.gz
  - data/snapshot_clear_delegation_onchain.jsonl.gz
  
## Dataset Processing and Merging

### merge proposals

```
python scripts/process/merge_proposals.py
```

- Output: 
  - processed_data/proposals_spaces.csv

### process coingecko market charts and market index

```
python scripts/process/process_charts.py
```

- Output: 
  - processed_data/coingecko_charts.csv

#### merge spaces data with Coingecko data

```
python scripts/process/merge_spaces_gecko.py
```

- Output: 
  - processed_data/spaces_gecko.csv

### process coingecko id Ethereum smart contract

```
python scripts/process/process_smart_contract.py
```

- Output: 
  - processed_data/coingecko_id_smart_contract_eth.json.gz

## Event Study

### CAR Processing

#### process event study CAR

```
python scripts/process/process_event_study.py
```

- Output: 
  - processed_data/proposals_event_study.csv

#### process smart contracts

```
python scripts/process/process_proposals_with_sc.py
```
- Output: processed_data / proposals_with_sc.csv

#### fetch transfers

```
python scripts/fetch/fetch_transfers.py
```
- Output: data/transfer/*/*.csv

#### process transfer
```
python scripts/process/process_transfers.py
```
- Output: processed_data/transfer/*.csv

### Vote Characteristics Regression

#### process_votes

```
python scripts/process/process_votes.py
```

#### Convert proposal timestamp to block in order to merge the holding

```
python scripts / fetch_ts_block.py
```
- Output: processed_data / proposals_adjusted_with_block.csv

#### 5. Process the vote characterstics

```
python scripts/process_vote_characteristics.py
```
- Output: processed_data / proposals_adjusted_votes.csv

#### 6. Vote characteristics regression

```
reg_car_votes.ipynb
```
- Output: tables / reg_car_votes_{created/end}

### Discussion Regression 

#### 1. Fetch discussion html
```
python scripts/fetch_discussion.py
```

We also manually collect the source code of some anti-crawler websites as HTML or TXT.

- Output: data / discussion

## Difference-in-Difference

### 1. merge spaces data with DefiLlama data

```
python scripts/merge_spaces_defillama_fees.py
```

- Output: processed_data / spaces_defillama_fees.csv

### 2. process fees and revenues data

```
python scripts/process_defillama_fees
```

- Output: processed_data / fees.csv