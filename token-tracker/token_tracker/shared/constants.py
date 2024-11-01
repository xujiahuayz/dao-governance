"""
This file contains constants.

* Author: Magnus Hansson (https://magnushansson.xyz, https://github.com/HanssonMagnus).
* License: MIT.
"""
# Import packages
import os

# Absolute path to the directory where constants.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the Ethereum Archive Node
NODE_URL = "http://localhost:8545"

# Paths to ERC-20 ABIs
PATH_ERC20_ABI = os.path.join(BASE_DIR, "../abis/ERC20_abi.json")
PATH_ERC20_BYTES_ABI = os.path.join(BASE_DIR, "../abis/ERC20_bytes32_abi.json")

# Topics
TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
