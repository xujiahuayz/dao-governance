import json
import gzip
import matplotlib.pyplot as plt
import pandas as pd

from governenv.constants import GITHUB_PATH_PULL_REQUESTS

# Load the data
with gzip.open(GITHUB_PATH_PULL_REQUESTS, "rt") as f:
    data = [json.loads(line) for line in f]

# Convert data to DataFrame
df = pd.DataFrame(data)

# Convert 'createdAt' to datetime and extract year
df['createdAt'] = pd.to_datetime(df['createdAt'])
df['year'] = df['createdAt'].dt.year

# Determine if the pull request was merged based on 'mergedAt' being null or not
df['merged'] = ~df['mergedAt'].isnull()

# Plot the distribution of pull requests by creation year
fig, ax = plt.subplots(figsize=(10, 5))
df_merged = df[df['merged'] == True]
df_not_merged = df[df['merged'] == False]

# Histogram settings
bins = range(df['year'].min(), df['year'].max() + 1)

df_merged['year'].plot.hist(ax=ax, bins=bins, alpha=0.5, label='Merged')
df_not_merged['year'].plot.hist(ax=ax, bins=bins, alpha=0.5, label='Not Merged')
ax.set_title("Distribution of Pull Requests by Year")
ax.set_xlabel("Year")
ax.set_ylabel("Number of Pull Requests")
plt.legend()

# Display the plot
plt.show()

# Display the entire DataFrame
print(df)
