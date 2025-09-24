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

# Data Feching

1. fetch snapshot spaces data

```
python scripts/fetch_spaces.py
```

2. fetch snapshot proposals data

```
python scripts/fetch_proposals.py
```

# Calculate the HHI for ENS discussion forum:

1. Filter ENS links (with discussion link) from snapshot:

```
python scripts/ens_snapshot_filter.py
```

2. For each post in the discussion forum URLs, find the author and their associated discussions:

```
python scripts/ens_authors.py
```

3. Calculate the HHI for each url to evaluate the concentration of activity:

```
python scripts/ens_hhi.py
```

# Calculate the sentiments for ENS discussion forum:

1. Create two folders named "html_200" and "idf" under "data" folder, then fetch the http response of the discussion links

```
mkdir data/html_200
mkdir data/idf
```

```
python scripts/ens_fetch_html.py
```

2. For each ENS link (with discussion link) from snapshot, filter out the html formatting code

```
python scripts/ens_process_html.py
```

3. Check whether the discussion thread have at least one discussion

```
python scripts/ens_process_identify_html.py
```

4. Calculate the sentiment of the discussion thread

```
python scripts/ens_process_sentiment.py
```

5. Calculate the statistics of HHI and sentiments and put it in a .tex table

```
python scripts/ens_hhi_senti_stats.py
```

# Calculate the votes for ENS discussion forum:

1. Calculate the total number of votes; the number of voters when it reached 50% of the total voting power for each proposal; and the timestamp when it reached 50% of the total voting power for each proposal.

```
python scripts/ens_votes.py
```

2. Put it in a csv table (together with HHI and sentiments for each proposal)

```
python scripts/ens_votes_HHI_senti.py
```
