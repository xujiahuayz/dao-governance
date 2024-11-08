"""
Fetch the http response of the discussion links
"""

import asyncio
import pickle
import time

import aiohttp
import requests

from governenv.constants import DATA_DIR, EXKW, HEADERS


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


def fetch_http_response(url: str, timeout: int = 10) -> str:
    """
    Fetches the HTTP response from a given URL.
    """
    return requests.get(url, headers=HEADERS, timeout=timeout).text


async def fetch(session, url: str) -> str:
    """
    Fetch the HTTP response from a given URL
    """
    async with session.get(
        url, ssl=True
    ) as response:  # Use ssl=True for default SSL context
        return (
            await response.text()
        )  # Use .text() for HTML/text response or .json() for JSON


async def fetch_all(urls: list[str], time_out: int = 10) -> list[str | BaseException]:
    """
    Fetch all HTTP responses from a list of URLs
    """
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=time_out)
    ) as session:  # No need for loop argument
        results = await asyncio.gather(
            *[fetch(session, url) for url in urls], return_exceptions=True
        )
        return results


if __name__ == "__main__":
    # unpickle data_unique
    with open(DATA_DIR / "discussion_links.pkl", "rb") as f:
        data_unique = pickle.load(f)
        print(f"Data length before filtering: {len(data_unique)}")

    # filter discussions
    data_unique = slash_filt(kw_filt(data_unique))
    print(f"Data length after filtering: {len(data_unique)}")

    # omly keep the first 10 for demonstration
    data_unique = dict(list(data_unique.items())[:100])

    # record start time
    start_time = time.time()

    # for idx, (_, url) in enumerate(data_unique.items()):
    #     try:
    #         http_response = requests.get(url, headers=HEADERS, timeout=10).text
    #     except Exception as e:  # pylint: disable=broad-except
    #         pass

    urls = list(data_unique.values())
    htmls = asyncio.run(fetch_all(urls))  # Use asyncio.run for a cleaner main loop

    # print the length of the correct responses
    print(len([html for html in htmls if not isinstance(html, Exception)]))

    print(f"Total time taken: {time.time() - start_time}")
