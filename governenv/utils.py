"""
Utility functions
"""

from governenv.constants import EXKW


def kw_filt(data: dict[str, str]) -> dict[str, str]:
    """
    Function to filter discussions based on keywords
    """

    return {k: v for k, v in data.items() if not any([i in v for i in EXKW])}


def slash_filt(data: dict[str, str]) -> dict[str, str]:
    """
    Function to filter discussions based on slashes
    """

    # typically, a discussion has at least 4 levels of slashes
    # if the slash count is less than 4, remove the discussion
    return {k: v for k, v in data.items() if v.count("/") >= 4}
