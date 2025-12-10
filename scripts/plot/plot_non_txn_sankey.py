"""Script to plot the two-column transaction Sankey diagram with category colors and percentage labels"""

import pandas as pd
import plotly.graph_objects as go
from governenv.constants import PROCESSED_DATA_DIR, FIGURE_DIR

# === Load data ===
df_flow = pd.read_csv(PROCESSED_DATA_DIR / "transfer_characteristics.csv")

# pick the directed edges you care about
EDGE_LIST = [
    ("whale", "whale"),
    ("whale", "smart_contract"),
    ("whale", "non_whale"),
    ("non_whale", "whale"),
    ("non_whale", "non_whale"),
    ("non_whale", "smart_contract"),
    ("smart_contract", "whale"),
    ("smart_contract", "non_whale"),
    ("smart_contract", "smart_contract"),
]
edge_df = pd.DataFrame(EDGE_LIST, columns=["identity_from", "identity_to"])

# Filter to just the edges of interest
df_txn0 = df_flow.merge(edge_df, on=["identity_from", "identity_to"], how="inner")

# Collapse duplicates just in case
df_txn0 = (
    df_txn0.groupby(["proposal_id", "stage", "identity_from", "identity_to"])["amount"]
    .sum()
    .reset_index()
)

# cartesian-product to "complete the edge space" with zeros
keys = df_txn0[["proposal_id", "stage"]].drop_duplicates()

# cross join (works in pandas>=1.2 using merge with a dummy key)
keys["key"] = 1
edge_df["key"] = 1
full = keys.merge(edge_df, on="key", how="outer").drop(columns="key")

# left-join the actual amounts; fill missing with 0
full = full.merge(
    df_txn0, on=["proposal_id", "stage", "identity_from", "identity_to"], how="left"
).fillna({"amount": 0.0})

# compute per-(proposal, stage) totals and percentages (safe with zeros)
full["amount_total"] = full.groupby(["proposal_id", "stage"])["amount"].transform("sum")
# avoid division by zero: if a proposal-stage has no flow in your filtered edges, keep pct=0
full["amount_pct"] = 0.0
mask = full["amount_total"] > 0
full.loc[mask, "amount_pct"] = full.loc[mask, "amount"] / full.loc[mask, "amount_total"]

df = (
    full.groupby(["stage", "identity_from", "identity_to"])["amount_pct"]
    .mean()
    .reset_index()
)

# The identities to include (both sides)
left_identities = ["smart_contract", "whale", "non_whale"]
right_identities = ["non_whale", "whale", "smart_contract"]

# --- Define color mapping ---
COLOR_MAP = {
    "smart_contract": "#ffcc00",  # yellow
    "whale": "#ff7f0e",  # orange
    "non_whale": "#1f77b4",  # blue
}

# --- Define pretty display names ---
DISPLAY_NAME = {
    "smart_contract": "Smart Contracts",
    "whale": "Whales",
    "non_whale": "Small Shareholders",
}

for stage in ["created", "end"]:
    df_stage = df[df["stage"] == stage]

    # --- Build left and right node labels ---
    left_labels = [f"L_{i}" for i in left_identities]
    right_labels = [f"R_{i}" for i in right_identities]
    labels = left_labels + right_labels

    # --- Map to numeric indices ---
    label_to_index = {label: i for i, label in enumerate(labels)}

    # --- Filter valid pairs ---
    df_stage = df_stage[
        df_stage["identity_from"].isin(left_identities)
        & df_stage["identity_to"].isin(right_identities)
    ]

    source = df_stage["identity_from"].map(lambda x: label_to_index[f"L_{x}"]).tolist()
    target = df_stage["identity_to"].map(lambda x: label_to_index[f"R_{x}"]).tolist()
    value = df_stage["amount_pct"].tolist()

    # If amount_pct is in [0,1], use this for labels:
    pct_labels = [f"{v*100:.1f}%" for v in value]

    # Node y-positions
    left_y_vals = [0.1, 0.5, 0.9]
    right_y_vals = [0.1, 0.5, 0.9]
    left_y_map = {iden: y for iden, y in zip(left_identities, left_y_vals)}
    right_y_map = {iden: y for iden, y in zip(right_identities, right_y_vals)}

    # --- Build the figure ---
    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="fixed",
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=[DISPLAY_NAME[label.split("_", 1)[1]] for label in labels],
                    color=[COLOR_MAP[label.split("_", 1)[1]] for label in labels],
                    x=[0.1] * len(left_identities) + [0.9] * len(right_identities),
                    y=left_y_vals + right_y_vals,
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=value,
                    label=pct_labels,
                    hovertemplate="%{label}<extra></extra>",
                    color="rgba(120,120,120,0.35)",
                ),
            )
        ]
    )

    # --- Add on-band percentage annotations (fix Y by flipping to paper coords) ---

    Y_MAPPING = {
        ("whale", "smart_contract"): 0.41,
        ("whale", "non_whale"): 0.2,
        ("smart_contract", "non_whale"): 0.95,
        ("smart_contract", "whale"): 0.6,
        ("non_whale", "smart_contract"): 0.05,
        ("non_whale", "whale"): 0.8,
    }

    annotations = []

    # for i, (_, row) in enumerate(df_stage.iterrows()):
    #     lf, rt = row["identity_from"], row["identity_to"]

    #     annotations.append(
    #         dict(
    #             x=0.5,
    #             y=Y_MAPPING[(lf, rt)],
    #             xref="paper",
    #             yref="paper",
    #             text=f"{row['amount_pct']*100:.1f}%",  # drop *100 if already 0–100
    #             showarrow=False,
    #             font=dict(size=16, color="black"),
    #         )
    #     )

    fig.update_layout(
        font=dict(size=16, color="black"),
        annotations=annotations,
        autosize=False,
        width=800,
        height=500,
    )
    fig.show()
    # write into tight layout pdf
    fig.write_image(
        FIGURE_DIR / f"sankey_non_txn_{stage}.pdf",
        format="pdf",
        width=800,
        height=500,
        scale=3,
    )
