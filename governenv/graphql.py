"""GraphQL query helper functions."""

import os
import gzip
import json
import datetime
import time
from typing import Optional

import requests
from governenv.constants import SNAPSHOT_ENDPOINT


def query_structurer(series: str, spec: str, arg: str = "") -> str:
    """Structure a GraphQL query."""

    # format query arguments
    if arg != "":
        arg = "(" + arg + ")"

    # format query content
    q = series + arg + "{" + spec + "}"
    return q


def graphdata(
    *q, url: str = SNAPSHOT_ENDPOINT, headers: Optional[dict[str, str]] = None
) -> dict:
    """Fetch data from a GraphQL endpoint."""

    # pack all subqueries into one big query concatenated with linebreak '\n'
    query = "{" + "\n".join(q) + "}"
    r = requests.post(url, json={"query": query}, headers=headers, timeout=60)

    response_json = json.loads(r.text)
    time.sleep(0.5)
    return response_json


def query_single(
    save_path: str,
    series: str,
    query_template: str,
    end_point: str = SNAPSHOT_ENDPOINT,
):
    """Query single data point."""

    with gzip.open(save_path, "at") as f:
        # Query data
        reservepara_query = query_structurer(
            series,
            query_template,
        )
        res = graphdata(reservepara_query, url=end_point)
        if "data" in set(res):
            if res["data"][series]:
                # Process fetched rows
                rows = res["data"][series]
                # Write rows to file and break the loop
                f.write("\n".join([json.dumps(row) for row in rows]) + "\n")
        else:
            raise ValueError("Error in fetching data")


def query(
    save_path: str,
    series: str,
    query_template: str,
    headers: Optional[dict[str, str]] = None,
    time_var: str = "created",
    end_point: str = SNAPSHOT_ENDPOINT,
    batch_size: int = 1000,
):
    """Query data and save to a file."""

    # Interrupt and resume
    if os.path.exists(save_path):
        with gzip.open(save_path, "rt") as f:
            lines = f.readlines()
            if lines:
                # Get the last created timestamp and add 1 to avoid duplication
                last_created = json.loads(lines[-1])[time_var] + 1
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
                arg=f'first: {batch_size}, orderBy: "{time_var}", '
                + f"orderDirection: asc, where: {{{time_var}_gte: {last_created}}}",
            )
            res = graphdata(reservepara_query, url=end_point, headers=headers)
            # Pagination check
            if "data" in set(res):
                if res["data"][series]:
                    # Process fetched rows
                    rows = res["data"][series]
                    length = len(rows)

                    # Update last_created timestamp
                    last_created = rows[-1][time_var]
                    print(f"Fetched {datetime.datetime.fromtimestamp(last_created)}")

                    if length == batch_size:
                        # Remove the last_created update from the write operation
                        rows = [row for row in rows if row[time_var] != last_created]
                        # Write remaining rows to file
                        f.write("\n".join([json.dumps(row) for row in rows]) + "\n")
                    else:
                        # Write rows to file and break the loop
                        f.write("\n".join([json.dumps(row) for row in rows]) + "\n")
                        break
                else:
                    break
            else:
                raise ValueError("Error in fetching data")


def query_id(
    save_path: str,
    idx: str,
    idx_var: str,
    series: str,
    query_template: str,
    time_var: str = "created",
    end_point: str = SNAPSHOT_ENDPOINT,
    batch_size: int = 1000,
):
    """Query data give id and save to a file."""

    os.makedirs(save_path, exist_ok=True)
    last_created = 0

    tmp_path = f"{save_path}/{idx}.jsonl.tmp"
    final_path = f"{save_path}/{idx}.jsonl"

    with open(tmp_path, "w", encoding="utf-8") as f:
        while True:
            # Query data
            reservepara_query = query_structurer(
                series,
                query_template,
                arg=f'first: {batch_size}, orderBy: "{time_var}", '
                + f'orderDirection: asc, where: {{{time_var}_gte: {last_created}, {idx_var}: "{idx}"}}',
            )
            res = graphdata(reservepara_query, url=end_point)

            # Pagination check
            if "data" in set(res):
                if res["data"][series]:
                    # Process fetched rows
                    rows = res["data"][series]
                    length = len(rows)

                    # Update last_created timestamp
                    last_created = rows[-1][time_var]
                    print(
                        f"Fetched {datetime.datetime.fromtimestamp(last_created)} for {idx}"
                    )
                    if length == batch_size:
                        # Remove the last_created update from the write operation
                        rows = [row for row in rows if row[time_var] != last_created]
                        # Write remaining rows to file
                        f.write("\n".join([json.dumps(row) for row in rows]) + "\n")
                    else:
                        # Write rows to file and break the loop
                        f.write("\n".join([json.dumps(row) for row in rows]) + "\n")
                        break
                else:
                    break
            else:
                raise ValueError("Error in fetching data")

    os.rename(tmp_path, final_path)
