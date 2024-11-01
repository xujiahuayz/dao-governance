# token-tracker

## {name}_fetsh_data.sh
The `{name}_fetsh_data.sh` is the main script that runs the entire pipline: collecting
data from the node, parse the data, and returns time series data of the reconstructed
token holdings.


The script works as follows:

Inputs:
    - EOA_ADDRESSES, list of EOA addresses.
    - ERC_20_CONTRACTS, list of ERC-20 token contracts.

Script:
    - For each EOA address the script:
        - Collects all historic transaction positions with TrueBlocks.
        - Transform csv data into json format, removing duplicates, by calling:
            token_tracker/scripts/process_trueblocks_csv_to_json.py

    - Parse all Transfer events from the contracts in ERC_20_CONTRACTS, by calling:
            token_tracker/scripts/process_transaction_logs.py
