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

### 1. merge spaces data with Coingecko data

```
python scripts / merge_spaces_gecko.py
```

- Output: processed_data / spaces_gecko.csv

### 2. process event study CAR

```
python scripts / process_event_study_car
```

### 3. fetch block timestamp

```
python scripts/fetch_block_ts.py
```

- Output: data / block_ts.jsonl.gz

### 4. process_votes

```
python scripts / process_votes.py
```

### 5. process address

```
python scripts / merge_sc_proposal_adj.py
```
- Output: processed_data / proposals_adjusted_with_sc.csv

### 6. Convert proposal timestamp to block in order to merge the holding

```
python scripts / fetch_ts_block.py
```
- Output: processed_data / proposals_adjusted_with_block.csv

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

## Calculate the HHI for ENS discussion forum:

### Filter ENS links (with discussion link) from snapshot:

```
python scripts/ens_snapshot_filter.py
```

### For each post in the discussion forum URLs, find the author and their associated discussions:

```
python scripts/ens_authors.py
```

### Calculate the HHI for each url to evaluate the concentration of activity:

```
python scripts/ens_hhi.py
```

## Calculate the sentiments for ENS discussion forum:

### Create two folders named "html_200" and "idf" under "data" folder, then fetch the http response of the discussion links

```
mkdir data/html_200
mkdir data/idf
```

```
python scripts/ens_fetch_html.py
```

### For each ENS link (with discussion link) from snapshot, filter out the html formatting code

```
python scripts/ens_process_html.py
```

### Check whether the discussion thread have at least one discussion

```
python scripts/ens_process_identify_html.py
```

### Calculate the sentiment of the discussion thread

```
python scripts/ens_process_sentiment.py
```

### Calculate the statistics of HHI and sentiments and put it in a .tex table

```
python scripts/ens_hhi_senti_stats.py
```

## Calculate the votes for ENS discussion forum:

### Calculate the total number of votes; the number of voters when it reached 50% of the total voting power for each proposal; and the timestamp when it reached 50% of the total voting power for each proposal.

```
python scripts/ens_votes.py
```

### Put it in a csv table (together with HHI and sentiments for each proposal)

```
python scripts/ens_votes_HHI_senti.py
```
