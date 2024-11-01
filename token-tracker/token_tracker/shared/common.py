"""
This file contains general helper functions.

* Author: Magnus Hansson (https://magnushansson.xyz, https://github.com/HanssonMagnus).
* License: MIT.
"""

# Import packages
import logging
import json
from typing import Any
import requests
from web3 import Web3
from token_tracker.shared import constants  # Import the shared module

# Get logger
logger = logging.getLogger(__name__)

####################################################################################################
# RPC call functions
####################################################################################################
def get_tx_receipt_block_by_index(
    block_hex: str, index_hex: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """
    Get tx, receipt, and block response from node.

    Args:
        block_hex (str): Hex of block number.
        index_hex (str): Hex of transaction index in block.

    Returns:
        tuple (dict, dict, dict): Transaction, receipt, and block data.

    """
    tx_data = get_tx_data_by_block_and_index(block_hex, index_hex)
    tx_hash = tx_data["hash"]
    receipt_data = get_receipt_data_by_hash(tx_hash)
    block_data = get_block_data_by_block_number(block_hex)
    return tx_data, receipt_data, block_data


def get_tx_data_by_hash(tx_hash: str) -> dict[str, Any]:
    """
    Get tx response from node.

    Args:
        tx_hash (str): Transaction hash.

    Returns:
        dict: JSON dict object of transation data.

    """
    url = constants.NODE_URL
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getTransactionByHash",
        "params": [tx_hash],
        "id": 1,
    }
    timeout_seconds = 10
    res_tx = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)
    tx_data = res_tx.json()["result"]
    return tx_data


def get_tx_data_by_block_and_index(block_hex: str, index_hex: str) -> dict[str, Any]:
    """Get tx response from node."""
    url = constants.NODE_URL
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getTransactionByBlockNumberAndIndex",
        "params": [block_hex, index_hex],
        "id": 1,
    }
    timeout_seconds = 10
    res_tx = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)
    tx_data = res_tx.json()["result"]
    return tx_data


def get_receipt_data_by_hash(tx_hash: str) -> dict[str, Any]:
    """Get receipt response from node."""
    url = constants.NODE_URL
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getTransactionReceipt",
        "params": [tx_hash],
        "id": 1,
    }
    timeout_seconds = 10
    res_receipt = requests.post(
        url, headers=headers, json=payload, timeout=timeout_seconds
    )
    receipt_data = res_receipt.json()["result"]
    return receipt_data


def get_block_data_by_block_number(block_hex: str) -> dict[str, Any]:
    """Get block response from node."""
    url = constants.NODE_URL
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": [block_hex, False],
        "id": 1,
    }
    timeout_seconds = 10
    res_block = requests.post(
        url, headers=headers, json=payload, timeout=timeout_seconds
    )
    block_data = res_block.json()["result"]
    return block_data

########################################################################################
# Load files
########################################################################################
def load_json(path_json: str) -> dict:
    """Load a JSON file, e.g., a dictionary with blockNumber as key and txIndex as
    values."""
    with open(path_json, "r", encoding="utf-8") as file:
        return json.load(file)

def load_abi(path_abi):
    """Load an ABI as a json object."""
    with open(path_abi, "r", encoding="utf-8") as file:
        data = json.load(file)
        return data["abi"]  # How they are constructed in this repo

########################################################################################
# ABI call functions
########################################################################################
def get_erc20_symbol(
    token_address: str, erc20_abi: dict[str, Any], erc20_bytes32_abi: dict[str, Any]
) -> tuple[str, int]:
    """
    Match an ERC-20 token smart contract address to its symbol and get the number of
    decimals for that ERC-20 token.

    Args:
        token_address (str): Smart contract address of ERC-20 token.
        erc20_abi (dict): ERC-20 ABI.
        erc20_bytes32_abi (dict): ERC-20 ABI with Bytes32 type for symbol (some
                                  contracts have this to save gas).

    Returns:
        tuple (str, int): Symbol and number of decimals of the ERC-20 token.
    """
    # Transform address to checksum address
    token_address = Web3.to_checksum_address(token_address)
    try:
        url = constants.NODE_URL
        w3 = Web3(Web3.HTTPProvider(url))
        token_address = Web3.to_checksum_address(token_address)
        token_contract = w3.eth.contract(address=token_address, abi=erc20_abi)
        symbol = token_contract.functions.symbol().call()
        decimals = token_contract.functions.decimals().call()
    except OverflowError as e:  # some tokens return symbol as bytes32
        logger.error(e, exc_info=True)
        token_contract = w3.eth.contract(address=token_address, abi=erc20_bytes32_abi)
        symbol = token_contract.functions.symbol().call()
        symbol = bytes32_to_string(symbol)
        decimals = token_contract.functions.decimals().call()

    return symbol, decimals

########################################################################################
# Bytes32 parsing
########################################################################################
def bytes32_to_string(bytes32: bytes) -> str:
    """Decode using utf-8 and then strip the null characters."""
    return bytes32.decode("utf-8").rstrip("\x00")
