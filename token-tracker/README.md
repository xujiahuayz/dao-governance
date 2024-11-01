# token-tracker

A tool for tracking historical ERC-20 token balances for Ethereum addresses. It uses
TrueBlocks for indexing transactions and an Erigon archive node for querying logs. The
tool reconstructs token balance histories and outputs time series data in Parquet
format.

## The virtual environment

Create a python virtual environment,
```bash
python3 -m venv .venv
```

To activate the virtual environment,
```bash
source .venv/bin/activate
```

Update pip (such that setuptools is up to date),
```bash
python3 -m pip install --upgrade pip
```

Install the project in editable mode,
```bash
pip install -e .
```

`pip install -e ".[dev]"` if you also want to install the optional dependencies from
`pyproject.toml`.

To deactivate the virtual environment,
```bash
deactivate
```

## Adding Required Packages
Install via `pip`,

```bash
source .venv/bin/activate
pip install <package-name>
```

Then check the package version with `pip show <package-name>`, and then add it manually
to `pyproject.toml`.

## Running token-tracker

The program is run through a shell script associated with the EOA addresses of interest
and the specified ERC-20 contract. An example can be found in
`token-tracker/data/ENS/ens_fetch_data.sh`.

## Inspect Parquet Data
token-tracker delivers the data in parquet format. Parquet is becoming the standard for
high performance data storage, however one disadvantage is that you cannot view the data
file in your editor. One way to inspect the data from the command line is to use
`parquet-cli`, which is installed through pip and then run in the command line.

```
pip install parquet-cli
parq your_file.parquet --head 10
```
