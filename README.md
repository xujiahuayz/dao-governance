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

### 1. fetch snapshot spaces data

```
python scripts/fetch_spaces.py
```

### 2. fetch snapshot proposals data

```
python scripts/fetch_proposals.py
```

### 3. fetch coingecko data

```
python scripts/fetch_coingecko.py
```

### 4. fetch defillama data

```
python scripts/fetch_defillama.py
```

### 5. fetch risk-free rate

```
Python scripts/fetch_rf
```

- Output: data / rf.csv

### 6. fetch ethereum smart contract data

- Run following command is snowflake
```
COPY INTO @~/eth_contract/
FROM (
  SELECT *
  FROM ETHEREUM_ONCHAIN_CORE_DATA.CORE.DIM_CONTRACTS
)
FILE_FORMAT = (TYPE = PARQUET COMPRESSION = SNAPPY)
SINGLE = FALSE
MAX_FILE_SIZE = 536870912   -- ~512 MB compressed
OVERWRITE = TRUE;

LIST @~/eth_contract/;
```

- Unload the data
```
GET @~/eth_contract/ file://./data/ethereum/contract PATTERN='.*[.]parquet' PARALLEL=7;
```

## General Data Processing

### 1. merge proposals

```
python script/merge_proposals
```

- Output: processed_data / proposals_spaces.csv

### 2. process coingecko market charts and market index

```
python script/process_charts.py
```

- Output: processed_data / coingecko_charts.csv

### 3. process coingecko id Ethereum smart contract

```
python script/process_smart_contract.py
```

- Output: processed_data / coingecko_id_smart_contract_eth.json.gz

## Event Study

### CAR Processing

#### 1. merge spaces data with Coingecko data

```
python scripts / merge_spaces_gecko.py
```

- Output: processed_data / spaces_gecko.csv

#### 2. process event study CAR

```
python scripts / process_event_study_car
```

### Vote Characteristics Regression

#### 1. fetch block timestamp

```
python scripts/fetch_block_ts.py
```

- Output: data / block_ts.jsonl.gz

#### 2. process_votes

```
python scripts / process_votes.py
```

#### 3. process address

```
python scripts / merge_sc_proposal_adj.py
```
- Output: processed_data / proposals_adjusted_with_sc.csv

#### 4. Convert proposal timestamp to block in order to merge the holding

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

### 3. generate the cohort DID panel

```
python scripts/reg_did_fees
```

- Output: processed_data / reg_fee_proposals_panel.csv