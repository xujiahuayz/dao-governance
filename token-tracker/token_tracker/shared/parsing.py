"""
This file contains the parser for Transfer events.

* Author: Magnus Hansson (https://magnushansson.xyz, https://github.com/HanssonMagnus).
* License: MIT.
"""

# Import packages
import logging
from typing import Any
from dataclasses import dataclass, asdict
from web3 import Web3
from token_tracker.shared import constants  # Import the shared module
from token_tracker.shared import common  # Import the shared module


@dataclass
class TransferEvent:
    """Dataclass for Transfer event. The ERC-20 Transfer event is defined as:
    event Transfer(address indexed from, address indexed to, uint256 value);
    """

    # Variables from the Transfer Event
    log_index: int  # The index of the log (important if many Transfers in one tx).
    token_symbol: str  # The symbol of the token.
    decimals: int  # The number of decimals of the token.
    from_address: str  # The address of the token sender.
    to_address: str  # The address of the token recipient.
    value: int | float  # The number of tokens transferred (transformed to base unit).

    def __post_init__(self) -> None:
        # Transform amounts to base units
        self.value = self.transform_to_base(self.value, self.decimals)


    @staticmethod
    def transform_to_base(amount: int | float, decimals: int) -> float | int:
        """
        Transforms token amounts to base values based on their decimals. Raise
        ValueError if the amount is None.
        """
        if amount is None:
            raise ValueError("Amount cannot be None for base unit transformation.")
        return amount * 10**-decimals if decimals > 0 else amount


    # Class method
    def get_event_data(self) -> dict[str, int | str] | None:
        """Return dataclass object as dict."""
        return asdict(self)


def parse_transfer_event(
    log: dict,
    eoa_address: str,
    contract_address_list: list,
    erc20_abi: dict[str, Any],
    erc20_bytes32_abi: dict[str, Any],
) -> dict[str, int | str] | None:
    """Parse Transfer event."""

    # Check if the log is a Transfer event
    try:
        topic_0 = log["topics"][0] # Topic 0 (should be Transfer)
    except Exception as e:
        logging.error(f"Error getting topic 0: {e}")
        return None

    if not topic_0 == constants.TRANSFER_TOPIC:
        logging.info("Not a Transfer event.")
        return None

    # Check if contract address is in the ERC-20 contract address list
    try:
        log_address = Web3.to_checksum_address(log["address"]) # Address of the ERC-20 contract
    except Exception as e:
        logging.error(f"Error getting log contract address: {e}")
        return None

    if not log_address in contract_address_list:
        logging.info("Not of the specified token contracts.")
        return None

    # Check if the EOA address is involved in the Transfer event
    try:
        eoa_address = Web3.to_checksum_address(eoa_address)
        from_address = "0x" + log["topics"][1][-40:] # Address of the sender
        from_address = Web3.to_checksum_address(from_address)
        to_address = "0x" + log["topics"][2][-40:] # Address of the recipient
        to_address = Web3.to_checksum_address(to_address)
    except Exception as e:
        logging.error(f"Error getting from and to address: {e}")
        return None

    if to_address != eoa_address and from_address != eoa_address:
        logging.info("Not involving the EOA address.")
        return None

    if to_address == from_address:
        logging.info("The sender and recipient are the same.")
        return None

    # Parse the value of the Transfer event
    try:
        value = int(log["data"], 16) # Value of the transfer
        if eoa_address == from_address:
            value = -value
    except Exception as e:
        logging.error(f"Error parsing the value of the Transfer event: {e}")
        return None

    # Get the ERC-20 symbol and decimals
    try:
        token_symbol, decimals = common.get_erc20_symbol(
            log_address, erc20_abi, erc20_bytes32_abi
        )
    except Exception as e:
        logging.error(f"Error getting ERC-20 symbol: {e}")
        return None

    # Get log index
    try:
        log_index_hex = log['logIndex']
        log_index = int(log_index_hex, 16)
    except Exception as e:
        logging.error(f"Error getting log index: {e}")
        return None

    return TransferEvent(
        log_index=log_index,
        token_symbol=token_symbol,
        decimals=decimals,
        from_address=from_address,
        to_address=to_address,
        value=value,
    ).get_event_data()
