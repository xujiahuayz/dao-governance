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

# fetch snapshot spaces data

```
python scripts/fetch_spaces.py
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
