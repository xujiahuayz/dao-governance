#!/bin/bash

# Start timer and print start message
start_time="$(date -u +%s)"
echo "Get ready, Token Tracker is starting!"

# Create data and log directories if it doesn't exist
mkdir -p ./trueblocks_data
mkdir -p ./time_series_data
mkdir -p ./logs

# List of EOA addresses to fetch data for
EOA_ADDRESSES=(
    "0xb8c2C29ee19D8307cb7255e1Cd9CbDE883A267d5"
    "0x839395e20bbB182fa440d08F850E6c7A8f6F0780"
)

# List of ERC-20 contract addresses to parse Transfer events for
ERC_20_CONTRACTS=(
    "0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72"
    "0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D73" # Just to add a random 2nd address to see that it works with a list
)

for EOA_ADDRESS in "${EOA_ADDRESSES[@]}"
do
    # Query positions from node using TrueBlocks, output format is CSV with blockNumber and transactionIndex
    {
        echo 'blockNumber,transactionIndex'
        chifra list $EOA_ADDRESS | awk '(NR>1) {print $2","$3}' #"," for csv format
    } > ./trueblocks_data/$EOA_ADDRESS.csv

    # Transform csv data into json format, removing duplicates
    python3 ../../token_tracker/scripts/process_trueblocks_csv_to_json.py ./trueblocks_data/$EOA_ADDRESS.csv ./trueblocks_data/$EOA_ADDRESS.json ./logs/trueblocks_python.log

    # Parse Transfer events from ERC-20 contracts
    PYTHON_CMD="python3 ../../token_tracker/scripts/process_transaction_logs.py $EOA_ADDRESS ./trueblocks_data/$EOA_ADDRESS.json ./time_series_data/$EOA_ADDRESS.parquet ./logs/process_transaction_logs.log"

    # Append each ERC-20 address to the command
    for ERC_20_CONTRACT in "${ERC_20_CONTRACTS[@]}"
    do
        PYTHON_CMD="$PYTHON_CMD $ERC_20_CONTRACT"
    done

    # Run the final Python command after all ERC-20 addresses are appended
    eval $PYTHON_CMD

done

# Print time elapsed
end_time="$(date -u +%s)"
elapsed="$(($end_time-$start_time))"
echo "Elapsed time: $elapsed seconds."
