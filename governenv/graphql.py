"""GraphQL query helper functions."""

import os
import gzip
import json
import datetime
import time

import requests


def query_structurer(series: str, spec: str, arg: str = "") -> str:
    """Structure a GraphQL query."""

    # format query arguments
    if arg != "":
        arg = "(" + arg + ")"

    # format query content
    q = series + arg + "{" + spec + "}"
    return q


def graphdata(*q, url: str = "https://hub.snapshot.org/graphql") -> dict:
    """Fetch data from a GraphQL endpoint."""

    # pack all subqueries into one big query concatenated with linebreak '\n'
    query = "{" + "\n".join(q) + "}"
    r = requests.post(url, json={"query": query}, timeout=60)

    response_json = json.loads(r.text)
    time.sleep(1)
    print(response_json)
    return response_json


def query(
    save_path: str,
    series: str,
    query_template: str,
    batch_size: int = 1000,
):
    """Query data and save to a file."""

    # Interrupt and resume
    if os.path.exists(save_path):
        with gzip.open(save_path, "rt") as f:
            lines = f.readlines()
            if lines:
                # Get the last created timestamp and add 1 to avoid duplication
                last_created = json.loads(lines[-1])["created"] + 1
            else:
                last_created = 0
    else:
        last_created = 0

    # Fetch data
    with gzip.open(save_path, "at") as f:

        while True:
            # Query data
            reservepara_query = query_structurer(
                series,
                query_template,
                arg=f'first: {batch_size}, orderBy: "created", '
                + f"orderDirection: asc, where: {{created_gte: {last_created}}}",
            )
            res = graphdata(reservepara_query)

            # Pagination check
            if "data" in set(res) and res["data"][series]:

                # Process fetched rows
                rows = res["data"][series]
                length = len(rows)

                # Update last_created timestamp
                last_created = rows[-1]["created"]
                print(f"Fetched {datetime.datetime.fromtimestamp(last_created)}")

                if length == batch_size:
                    # Remove the last_created update from the write operation
                    rows = [row for row in rows if row["created"] != last_created]
                    # Write remaining rows to file
                    f.write("\n".join([json.dumps(row) for row in rows]) + "\n")
                else:
                    # Write rows to file and break the loop
                    f.write("\n".join([json.dumps(row) for row in rows]) + "\n")
                    break
            else:
                break
