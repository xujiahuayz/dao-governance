"""
Load a chifra json file with all positions from a given EOA address. For a given list of ERC-20
tokens, for each parse out the Transfer event.

* Author: Magnus Hansson (https://magnushansson.xyz, https://github.com/HanssonMagnus).
* License: MIT.
"""

# Import packages
import time
import argparse
import os
import sys
import logging
import multiprocessing
from pprint import pprint
import pandas as pd

from token_tracker.shared import common  # Import the shared module
from token_tracker.shared import constants  # Import the shared module
from token_tracker.shared import parsing  # Import the shared module

# Start timer
start = time.time()

####################################################################################################
# Parse Arguments Passed to the Script and set up Logger
####################################################################################################

# Initialize argument parser
parser = argparse.ArgumentParser(description="Parse Transfer events.")
parser.add_argument("eoa_address", help="Address of the EOA")
parser.add_argument("input_file_json", help="Path to the input JSON file")
parser.add_argument("output_file_parquet", help="Path to the output PARQUET file")
parser.add_argument("log_file", help="Path to the log file")
parser.add_argument(
    "contract_addresses", nargs="+", help="ERC-20 smart contract addresses"
)

# Parse arguments
args = parser.parse_args()

# Paths from arguments
eoa_address = args.eoa_address  # String with EOA address
input_file_json = args.input_file_json  # String with path to input file
output_file_parquet = args.output_file_parquet  # String with path to output file
log_file = args.log_file  # String with path to log file
contract_address_list = args.contract_addresses  # List of contract addresses

# Set up logger
logging.basicConfig(
    filename=log_file,
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    filemode="w+",
)

logger = logging.getLogger(__name__)

# Example log message
logger.error("Logging setup complete.")

# Check that the input path exists
if not os.path.exists(os.path.dirname(input_file_json)):
    logger.error("input_file_json directory does not exist.")
    sys.exit(1)

# Check that the output path exists
if not os.path.exists(os.path.dirname(output_file_parquet)):
    logger.error("output_file_parquet directory does not exist.")
    sys.exit(1)


###################################################################################################
# Load tx data as a json dict.
###################################################################################################
data = common.load_json(input_file_json)

# Flatten the dict into a list of tuples
block_index_pairs = [
    (block, index) for block, indexes in data.items() for index in indexes
]

###################################################################################################
# Load the contract ABI.
###################################################################################################
erc20_abi = common.load_abi(constants.PATH_ERC20_ABI)
erc20_bytes32_abi = common.load_abi(constants.PATH_ERC20_BYTES_ABI)

###################################################################################################
# Prepare arguments for multiprocessing
###################################################################################################
args_for_multiprocessing = [
    (block, index, erc20_abi, erc20_bytes32_abi, eoa_address, contract_address_list)
    for block, index in block_index_pairs
]

###################################################################################################
# Define multiprocessing function for parsing Transfer events.
###################################################################################################
def parse_transaction(
    block_number,
    index,
    erc20_abi_local,
    erc20_bytes32_abi_local,
    eoa_address_local,
    contract_address_list_local,
):
    """Parse Transfer events from a transaction."""
    # Initialize transfer event to None
    transfer_events = []

    # Get tx, receipt, and block data from the blockchain
    try:
        tx_data, receipt_data, block_data = common.get_tx_receipt_block_by_index(
            hex(int(block_number)), hex(int(index))
        )

    except Exception as e:
        logger.error(e, exc_info=True)

    # Check if there is any Transfer event in the tx associated with the contract address list
    try:
        logs = receipt_data["logs"]
        for log in logs:
            transfer_event = parsing.parse_transfer_event(
                log,
                eoa_address_local,
                contract_address_list_local,
                erc20_abi_local,
                erc20_bytes32_abi_local,
            )

            if transfer_event is not None:
                transfer_events.append(transfer_event)
    except Exception as e:
        logger.error(e, exc_info=True)

    # Return function if there are no valid Transfer events
    if not transfer_events:
        return

    # Collect additional meta data
    try:
        tx_hash = tx_data["hash"]
        timestamp = block_data["timestamp"]
        timestamp = int(timestamp, 0)  # from hex to int
        gas = int(tx_data['gas'], 16)
        gas_price = int(tx_data['gasPrice'], 16)


    except Exception as e:
        logger.error(e, exc_info=True)

    # Append txes to global list
    try:
        for transfer_event in transfer_events:
            output_data = [
                timestamp,
                block_number,
                transfer_event["log_index"],
                index,
                tx_hash,
                transfer_event["token_symbol"],
                transfer_event["decimals"],
                transfer_event["from_address"],
                transfer_event["to_address"],
                transfer_event["value"],
                gas,
                gas_price,
            ]
            L.append(output_data)
    except Exception as e:
        logger.error(e, exc_info=True)


###################################################################################################
# Collect transactions with the multiprocessing library
###################################################################################################
with multiprocessing.Manager() as manager:
    L = manager.list() # Can be shared between multiprocesses
    n_cpu = multiprocessing.cpu_count() # n threads
    # Processes outside of the loop otherwise too many files error
    # I've previously had trouble with too high maxtasksperchild and set it to 2, however, ChatGPT
    # thinks I can increase it a bit. So I should try it out for increased performance. Increasing
    # it from 2 to 15, made the test code run at 0.8s instead of 2.04. However, increating to 40
    # did not improve the speed further.
    pool = multiprocessing.Pool(n_cpu, maxtasksperchild=100)

    # Map get_tx to a range of blocks
    #pool.imap_unordered(parse_transaction, hashes_list)
    pool.starmap(parse_transaction, args_for_multiprocessing)

    pool.close()
    pool.join() # Synchronization point needed for this to work
    all_transfer_events = list(L)

###################################################################################################
# Create Dataframe
###################################################################################################
# Transform to dataframe
col_names= ['timestamp', 'block_number', 'index', 'log_index', 'tx_hash', 'token_symbol',
            'token_decimals', 'from_address', 'to_address', 'transfer_value', 'gas', 'gas_price']

df = pd.DataFrame(data=all_transfer_events, columns=col_names)

# Sort dataframe by blockNumber
df = df.sort_values(by=['block_number', 'index', 'log_index'])

pprint(df)

###################################################################################################
# Write to file
###################################################################################################
# Define column types
column_types = {
    'timestamp': 'Int64',  # Changed to nullable integer type
    'block_number': 'Int64',  # Changed to nullable integer type
    'index': 'Int64',  # Changed to nullable integer type
    'log_index': 'Int64',  # Changed to nullable integer type
    'tx_hash': 'str',
    'token_symbol': 'str',
    'token_decimals': 'Int64',  # Changed to nullable integer type
    'from_address': 'str',
    'to_address': 'str',
    'transfer_value': 'float64',
    'gas': 'float64',
    'gas_price': 'float64',
}

# Apply types to DataFrame
for column, dtype in column_types.items():
    df[column] = df[column].astype(dtype)

# Now, df is ready to be saved as a Parquet file
df.to_parquet(output_file_parquet, index=False)


####################################################################################################
# Print elapsed time with days included
####################################################################################################
end = time.time()
elapsed_seconds = int(end - start)
days, rem = divmod(elapsed_seconds, 86400)
hours, rem = divmod(rem, 3600)
minutes, seconds = divmod(rem, 60)
pprint(f"Elapsed time: {days} days, {hours:0>2}:{minutes:0>2}:{seconds:0>2}")
