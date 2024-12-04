# token-tracker

A tool for tracking historical ERC-20 token balances for Ethereum addresses. It uses
TrueBlocks for indexing transactions and an Erigon archive node for querying logs. The
tool reconstructs token balance histories and outputs time series data in Parquet
format.

## The virtual environment
```bash
poetry shell
poetry install
```

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
