"""
Load a chifra csv list and parse it into .json format.  The block is the key,
and the values are all txes in that block.

* Author: Magnus Hansson (https://magnushansson.xyz, https://github.com/HanssonMagnus).
* License: MIT.
"""

# Import packages
import argparse
import csv
import json
from io import StringIO
import logging

def chifra_csv_to_json(chifra_csv_content: str) -> dict[str, list[str]]:
    """
    Transforms CSV content with blockNumber and transactionIndex to a JSON-like dict
    with the block as the key and the transactionIndex as values for that block. 'chifra
    list' can return duplicates of transactions, and this transformation avoids that.

    Args:
        csv_content (str): CSV content as a string. Which can be read in, e.g., like:
            with open(path_input, mode='r', encoding='utf-8') as file:
                csv_content = file.read()

    Returns:
        dict: A dictionary with block numbers as keys and lists of transaction indices
        as values.
    """
    # Convert the CSV content string into a file-like object
    csv_file = StringIO(chifra_csv_content)

    # Use csv.reader to parse the file-like object
    csv_reader = csv.reader(csv_file)
    next(csv_reader, None)  # Skip the headers

    chifra_tx_dict: dict[str, list[str]] = {}
    for row in csv_reader:
        block_number, tx_index = row[0], row[1]
        try:
            if not tx_index in chifra_tx_dict[block_number]:
                chifra_tx_dict[block_number].append(tx_index)
        except KeyError:
            chifra_tx_dict[block_number] = []
            chifra_tx_dict[block_number].append(tx_index)
    return chifra_tx_dict

# Initialize argument parser
parser = argparse.ArgumentParser(description='Process chifra transaction data.')
parser.add_argument('input_path', help='Path to the input CSV file')
parser.add_argument('output_path', help='Path to the output JSON file')
parser.add_argument('log_path', help='Path to the log directory (same as files)')

# Parse arguments
args = parser.parse_args()

# Paths from arguments
path_input = args.input_path
path_output = args.output_path
path_log = args.log_path

# Set up logger
logging.basicConfig(filename=path_log, level=logging.ERROR,
    format='%(asctime)s %(levelname)s %(name)s %(message)s', filemode='w+')
logger = logging.getLogger(__name__)
logger.error("Logging setup complete.")

# Create json/dict of transactions
try:
    with open(path_input, mode='r', encoding='utf-8') as file:
        csv_content = file.read()
    tx_dict = chifra_csv_to_json(csv_content)

except Exception as e:
    logger.error(e, exc_info=True)

# Save dictionary as JSON
with open(path_output, 'w+', encoding='utf-8') as fjson:
    json.dump(tx_dict, fjson, indent=4)
fjson.close()
