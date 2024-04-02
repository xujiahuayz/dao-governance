import gzip
import json
import requests

from governenv.constants import GITHUB_PATH_REFCLIENT_ISSUES
from governenv.settings import GITHUB_TOKEN

# GitHub GraphQL endpoint
GITHUB_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

# GraphQL query 
def get_github_query(after_cursor=None):
    after = f', after: "{after_cursor}"' if after_cursor else ""
    return f"""
    {{
      # Fetch Reference Client Issues
      repository(owner: "algorand", name: "go-algorand") {{
        issues(first: 100{after}) {{
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
              author {{
                login    # author of the issue
              }}
              labels(first: 10) {{
                edges {{ node {{ name }} }} 
              }}
              comments(first: 20) {{
                edges {{ node {{ author {{ login }} }} }} # commenters
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
    issues = []

    while has_next_page:
        query = get_github_query(end_cursor)
        headers = {"Authorization": f"bearer {GITHUB_TOKEN}"}
        response = requests.post(GITHUB_GRAPHQL_ENDPOINT, json={'query': query}, headers=headers)
        if response.status_code == 200:
            data = response.json()
            prs = data['data']['repository']['issues']['edges']
            issues.extend(prs)
            pageInfo = data['data']['repository']['issues']['pageInfo']
            has_next_page = pageInfo['hasNextPage']
            end_cursor = pageInfo['endCursor']
        else:
            raise Exception(f"Query failed to run by returning code of {response.status_code}")
            break

    return issues

# Fetch the data 
data = fetch_github_data()

# Save the data to a gzip file
with gzip.open(GITHUB_PATH_REFCLIENT_ISSUES, "wt") as f:
    f.write("\n".join([json.dumps(pr['node']) for pr in data]) + "\n")
