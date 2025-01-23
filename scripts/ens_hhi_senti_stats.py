"""
Calculate the statistics of ENS links (with discussion link) from snapshot:
"""

import pandas as pd
import json
from governenv.constants import DATA_DIR

with open(DATA_DIR / "ens_hhi.json", "r") as f:
    data_hhi = json.load(f)

df_hhi = pd.DataFrame(data_hhi)
fields = ["number_of_discussions", "HHI_length_weighted", "HHI_equal_weighted"]

statistics = {}
for field in fields:
    stats = {
        "number": int(df_hhi[field].count()),  # number of non-null values
        "mean": float(df_hhi[field].mean()),
        "median": float(df_hhi[field].median()),
        "STD": float(df_hhi[field].std()),
        "Q1": float(df_hhi[field].quantile(0.25)),
        "Q3": float(df_hhi[field].quantile(0.75)),
        "min": float(df_hhi[field].min()),
        "max": float(df_hhi[field].max()),
    }
    statistics[field] = stats


df_hhi = pd.DataFrame(statistics).T
df_hhi.index.name = "Statistics"
df_hhi.reset_index(inplace=True)
df_hhi["number"] = df_hhi["number"].astype(int)

df_hhi["Statistics"] = df_hhi["Statistics"].replace(
    {
        "number_of_discussions": "number of discussions",
        "HHI_length_weighted": "HHI length weighted",
        "HHI_equal_weighted": "HHI equal weighted",
    }
)


with open(DATA_DIR / "ens_senti.json", "r") as f:
    data_senti = json.load(f)

class_prob_data = {key: value["class_prob"] for key, value in data_senti.items()}
df_senti = pd.DataFrame(class_prob_data).T

statistics_senti = {}
for field in df_senti.columns:
    stats = {
        # number of non-null values
        "number": int(df_senti[field].count()),
        "mean": float(df_senti[field].mean()),
        "median": float(df_senti[field].median()),
        "STD": float(df_senti[field].std()),
        "Q1": float(df_senti[field].quantile(0.25)),
        "Q3": float(df_senti[field].quantile(0.75)),
        "min": float(df_senti[field].min()),
        "max": float(df_senti[field].max()),
    }
    statistics_senti[field] = stats


df_senti = pd.DataFrame(statistics_senti).T
df_senti.index.name = "Statistics"
df_senti.reset_index(inplace=True)
df_senti["number"] = df_senti["number"].astype(int)

# Combine the two tables into one

latex_hhi = df_hhi.to_latex(index=False, float_format="%.4f", escape=False)
latex_senti = df_senti.to_latex(index=False, float_format="%.4f", escape=False)

lines_hhi = latex_hhi.splitlines()
lines_senti = latex_senti.splitlines()

midrule_idx_senti = None
for i, line in enumerate(lines_senti):
    if "\\midrule" in line:
        midrule_idx_senti = i
        break

combined_lines = []
for line in lines_hhi:
    if "\\bottomrule" in line:
        # Instead of adding \bottomrule, we insert a \midrule
        combined_lines.append(r"\midrule")
        # Then we'll append the data lines from the second table skipping up to its \midrule
        for line_senti in lines_senti[midrule_idx_senti + 1 :]:
            # Stop if we hit \bottomrule in the second table:
            if "\\bottomrule" in line_senti:
                break
            combined_lines.append(line_senti)
        # Finally, we append the \bottomrule from the first table
        # (or from the second; they are effectively the same).
        combined_lines.append(r"\bottomrule")
    elif "\\end{tabular}" in line:
        pass
    else:
        combined_lines.append(line)

combined_lines.append(r"\end{tabular}")
latex_table_combined = "\n".join(combined_lines)


# Write the combined table to a new file
latex_code = f"""
\\documentclass{{article}}
\\usepackage{{booktabs}}
\\usepackage{{graphicx}}
\\begin{{document}}
\\begin{{table}}[ht]
    \\centering
    \\small
{latex_table_combined}
    \\caption{{Summary statistics of ENS links and sentiment analysis}}
\\end{{table}}
\\end{{document}}
"""

with open(DATA_DIR / "ens_stats_table.tex", "w") as file:
    file.write(latex_code)
