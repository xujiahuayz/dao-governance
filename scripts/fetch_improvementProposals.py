import gzip
import json
import requests

from governenv.constants import GITHUB_PATH_IP_PULLREQUESTS
from governenv.settings import GITHUB_TOKEN

# GitHub GraphQL endpoint
GITHUB_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

# GraphQL query 
def get_github_query(after_cursor=None):
    after = f', after: "{after_cursor}"' if after_cursor else ""
    return f"""
    {{
      # Fetch IPs Pull Requests 
      repository(owner: "Ethereum", name: "EIPs") {{
        pullRequests(first: 100{after}) {{
          pageInfo {{
            endCursor
            hasNextPage
          }}
          edges {{
            node {{
              number
              title
              state
              url
              createdAt
              mergedAt
              author {{
                login    # author of the proposal
              }}
              labels(first: 10) {{
                edges {{ node {{ name }} }} 
              }}
              comments(first: 20) {{
                edges {{ node {{ author {{ login }} }} }} # commenters/discussants
              }}
              reviews(first: 10) {{
                edges {{ node {{ author {{ login }} state }} }} # reviewers
              }}
            }}
          }}
        }}
      }}
    }}
    """

# Function to fetch data 
def fetch_github_data():
    has_next_page = True
    end_cursor = None
    pull_requests = []

    while has_next_page:
        query = get_github_query(end_cursor)
        headers = {"Authorization": f"bearer {GITHUB_TOKEN}"}
        response = requests.post(GITHUB_GRAPHQL_ENDPOINT, json={'query': query}, headers=headers)
        if response.status_code == 200:
            data = response.json()
            prs = data['data']['repository']['pullRequests']['edges']
            pull_requests.extend(prs)
            pageInfo = data['data']['repository']['pullRequests']['pageInfo']
            has_next_page = pageInfo['hasNextPage']
            end_cursor = pageInfo['endCursor']
        else:
            raise Exception(f"Query failed to run by returning code of {response.status_code}")
            break

    return pull_requests

# Fetch the data 
data = fetch_github_data()

# Save the data to a gzip file
with gzip.open(GITHUB_PATH_IP_PULLREQUESTS, "wt") as f:
    f.write("\n".join([json.dumps(pr['node']) for pr in data]) + "\n")
