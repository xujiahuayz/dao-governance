"""Run H4 regressions for discussion quality and market reaction.

This script uses the proposal-level panel built by scripts/reg/reg_small.py and
writes the feasibility counts plus H4 regression tables requested in
h4_empirical_task.tex.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from governenv.constants import PROCESSED_DATA_DIR


TABLE_DIR = PROJECT_ROOT / "tables"
PANEL_PATH = PROCESSED_DATA_DIR / "proposals_panel.csv"
H4_PANEL_PATH = PROCESSED_DATA_DIR / "reg_h4_panel.csv"

SMALL_WIN = "non_whale_victory_vn"
QUALITY_VARS = {
    "concensus_diff": r"${\it \Delta Concensus}_{i}$",
    "concensus_full": r"${\it Concensus}^{\it full}_{i}$",
}
CAR_VARS = {
    "car_created": r"${\it CAR}^{\it Create}_{i}$",
    "car_end": r"${\it CAR}^{\it End}_{i}$",
}
ID_VARS = ["space", "gecko_id", "date"]
BASE_VARS = ID_VARS + [SMALL_WIN, "post_number", *QUALITY_VARS, *CAR_VARS]


@dataclass
class RegressionResult:
    """Small container for table-ready OLS output."""

    name: str
    nobs: int
    r2_adj: float
    coef: dict[str, float]
    se: dict[str, float]
    tstat: dict[str, float]


def require_columns(df: pd.DataFrame, columns: list[str], name: str) -> None:
    """Raise a clear error if an input file is missing required columns."""

    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def winsorize_upper(series: pd.Series, pct: float = 0.99) -> pd.Series:
    """Winsorize the upper tail, matching the paper's existing convention."""

    if series.dropna().empty:
        return series
    upper = series.quantile(pct)
    return series.clip(upper=upper)


def prepare_panel(winsorized: bool = False) -> pd.DataFrame:
    """Load and clean the proposal panel for H4."""

    if not PANEL_PATH.exists():
        raise FileNotFoundError(
            f"{PANEL_PATH} does not exist. Run `python3 -m scripts.reg.reg_small` "
            "after the processed input CSVs are available."
        )

    df = pd.read_csv(PANEL_PATH)
    require_columns(df, BASE_VARS, PANEL_PATH.name)

    out = df[BASE_VARS].copy()
    numeric_cols = [SMALL_WIN, "post_number", "non_small_win", *QUALITY_VARS, *CAR_VARS]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["year"] = out["date"].dt.year
    out["quality_defined"] = (
        out["post_number"].ge(2)
        & out["concensus_diff"].notna()
        & out["concensus_full"].notna()
    )
    out["non_small_win"] = 1 - out[SMALL_WIN]

    if winsorized:
        for col in [*QUALITY_VARS, *CAR_VARS]:
            out[col] = winsorize_upper(out[col])

    return out


def feasibility_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Build the mandatory feasibility counts from h4_empirical_task.tex."""

    quality = df["quality_defined"]
    small_quality = quality & df[SMALL_WIN].eq(1)
    return pd.DataFrame(
        [
            ("Proposals with discussion posts >= 2 and quality defined", int(quality.sum())),
            ("of which non-missing CARCreate", int((quality & df["car_created"].notna()).sum())),
            ("of which non-missing CAREnd", int((quality & df["car_end"].notna()).sum())),
            ("SmallWin = 1 and quality defined", int(small_quality.sum())),
            (
                "SmallWin = 1, quality defined, and non-missing CARCreate",
                int((small_quality & df["car_created"].notna()).sum()),
            ),
            (
                "SmallWin = 1, quality defined, and non-missing CAREnd",
                int((small_quality & df["car_end"].notna()).sum()),
            ),
        ],
        columns=["cell", "count"],
    )


def make_design(df: pd.DataFrame, regressors: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    """Create the OLS design matrix with token and year fixed effects."""

    x = df[regressors].astype(float).copy()
    token_fe = pd.get_dummies(df["gecko_id"], prefix="token", drop_first=True, dtype=float)
    year_fe = pd.get_dummies(df["year"], prefix="year", drop_first=True, dtype=float)
    x = pd.concat([pd.Series(1.0, index=df.index, name="_cons"), x, token_fe, year_fe], axis=1)
    clusters = df["gecko_id"].astype(str)
    return x, clusters


def ols_cluster(
    df: pd.DataFrame,
    y_var: str,
    regressors: list[str],
    keep_params: list[str],
    name: str,
) -> RegressionResult:
    """Estimate OLS with token/year FE and token-clustered standard errors."""

    needed = [y_var, "gecko_id", "year", *regressors]
    reg = df.dropna(subset=needed).copy()
    if reg.empty:
        raise ValueError(f"No observations available for {name}.")

    y = reg[y_var].astype(float).to_numpy()
    x_df, clusters = make_design(reg, regressors)
    x = x_df.to_numpy(dtype=float)

    xtx_inv = np.linalg.pinv(x.T @ x)
    beta = xtx_inv @ x.T @ y
    resid = y - x @ beta

    meat = np.zeros((x.shape[1], x.shape[1]))
    for _, idx in clusters.groupby(clusters).groups.items():
        xg = x_df.loc[idx].to_numpy(dtype=float)
        ug = resid[x_df.index.get_indexer(idx)]
        xu = xg.T @ ug
        meat += np.outer(xu, xu)

    nobs, k = x.shape
    nclusters = clusters.nunique()
    cov = xtx_inv @ meat @ xtx_inv
    if nclusters > 1 and nobs > k:
        cov *= (nclusters / (nclusters - 1)) * ((nobs - 1) / (nobs - k))

    se_all = np.sqrt(np.maximum(np.diag(cov), 0.0))
    ssr = float(np.sum(resid**2))
    tss = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ssr / tss if tss else np.nan
    r2_adj = 1 - (1 - r2) * (nobs - 1) / (nobs - k) if nobs > k and tss else np.nan

    coef = dict(zip(x_df.columns, beta, strict=True))
    se = dict(zip(x_df.columns, se_all, strict=True))
    return RegressionResult(
        name=name,
        nobs=nobs,
        r2_adj=r2_adj,
        coef={param: coef.get(param, np.nan) for param in keep_params},
        se={param: se.get(param, np.nan) for param in keep_params},
        tstat={
            param: coef.get(param, np.nan) / se.get(param, np.nan)
            if se.get(param, np.nan) > 0
            else np.nan
            for param in keep_params
        },
    )


def star(tstat: float) -> str:
    """Return significance stars from a normal approximation to the t-statistic."""

    if pd.isna(tstat):
        return ""
    at = abs(tstat)
    if at >= 2.576:
        return r"\sym{***}"
    if at >= 1.960:
        return r"\sym{**}"
    if at >= 1.645:
        return r"\sym{*}"
    return ""


def fmt_num(value: float, digits: int = 3) -> str:
    """Format table numbers with blanks for missing values."""

    if pd.isna(value):
        return ""
    return f"{value:,.{digits}f}"


def coef_cell(result: RegressionResult, param: str) -> str:
    return f"{fmt_num(result.coef[param])}{star(result.tstat[param])}"


def t_cell(result: RegressionResult, param: str) -> str:
    return f"({fmt_num(result.tstat[param], 2)})" if not pd.isna(result.tstat[param]) else ""


def write_latex_table(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    print(f"Wrote {path}")


def write_feasibility_table(counts: pd.DataFrame) -> None:
    rows = "\n".join(
        f"{row.cell} & {row.count:,} \\\\" for row in counts.itertuples(index=False)
    )
    body = rf"""\begin{{tabular}}{{lc}}
\toprule
Cell & Count \\
\midrule
{rows}
\bottomrule
\end{{tabular}}
"""
    write_latex_table(TABLE_DIR / "h4_feasibility.tex", body)
    counts.to_csv(PROCESSED_DATA_DIR / "h4_feasibility.csv", index=False)


def write_interaction_table(
    results: list[RegressionResult],
    suffix: str = "",
    treatment_label: str = r"${\it Small Win}_{i}$",
) -> None:
    params = [
        (SMALL_WIN, treatment_label),
        ("small_win_quality", treatment_label.rstrip("$") + r" \times {\it Quality}_{i}$"),
        ("quality", r"${\it Quality}_{i}$"),
    ]
    rows = []
    for param, label in params:
        rows.append(label + "&" + "&".join(coef_cell(res, param) for res in results) + r"\\")
        rows.append(" " + "&" + "&".join(t_cell(res, param) for res in results) + r"\\[2pt]")
    rows.extend(
        [
            r"\midrule",
            "Token FE&Y&Y&Y&Y\\\\",
            "Year FE&Y&Y&Y&Y\\\\",
            "Observations&" + "&".join(f"{res.nobs:,}" for res in results) + r"\\",
            "Adjusted R$^2$&" + "&".join(fmt_num(res.r2_adj) for res in results) + r"\\",
        ]
    )
    body = rf"""{{
\def\sym#1{{\ifmmode^{{#1}}\else\(^{{#1}}\)\fi}}
\begin{{tabular}}{{lcccc}}
\toprule
 & \multicolumn{{2}}{{c}}{{Quality $=\Delta$ Consensus}} & \multicolumn{{2}}{{c}}{{Quality $=$ Consensus level}} \\
\cmidrule(lr){{2-3}}\cmidrule(lr){{4-5}}
 & {CAR_VARS["car_created"]} & {CAR_VARS["car_end"]} & {CAR_VARS["car_created"]} & {CAR_VARS["car_end"]} \\
 & (1) & (2) & (3) & (4) \\
\midrule
{chr(10).join(rows)}
\bottomrule
\end{{tabular}}
}}
"""
    write_latex_table(TABLE_DIR / f"reg_h4_interaction{suffix}.tex", body)


def write_split_table(results: list[RegressionResult], quality_var: str, suffix: str = "") -> None:
    rows = [
        r"${\it Small Win}_{i}$&" + "&".join(coef_cell(res, SMALL_WIN) for res in results) + r"\\",
        " &" + "&".join(t_cell(res, SMALL_WIN) for res in results) + r"\\",
        r"\midrule",
        "Token FE&Y&Y&Y&Y\\\\",
        "Year FE&Y&Y&Y&Y\\\\",
        "Observations&" + "&".join(f"{res.nobs:,}" for res in results) + r"\\",
        "Adjusted R$^2$&" + "&".join(fmt_num(res.r2_adj) for res in results) + r"\\",
    ]
    body = rf"""{{
\def\sym#1{{\ifmmode^{{#1}}\else\(^{{#1}}\)\fi}}
\begin{{tabular}}{{lcccc}}
\toprule
 & \multicolumn{{2}}{{c}}{{{CAR_VARS["car_created"]}}} & \multicolumn{{2}}{{c}}{{{CAR_VARS["car_end"]}}} \\
\cmidrule(lr){{2-3}}\cmidrule(lr){{4-5}}
 & Low quality & High quality & Low quality & High quality \\
 & (1) & (2) & (3) & (4) \\
\midrule
{chr(10).join(rows)}
\bottomrule
\end{{tabular}}
}}
% Split variable: {quality_var}
"""
    write_latex_table(TABLE_DIR / f"reg_h4_split{suffix}.tex", body)


def run_interaction(df: pd.DataFrame, treatment: str = SMALL_WIN) -> list[RegressionResult]:
    """Run interaction regressions for both quality proxies and CAR windows."""

    sample = df.loc[df["quality_defined"]].copy()
    results = []
    for quality in QUALITY_VARS:
        sample["quality"] = sample[quality]
        sample["small_win_quality"] = sample[treatment] * sample["quality"]
        for y_var in CAR_VARS:
            results.append(
                ols_cluster(
                    sample,
                    y_var,
                    [treatment, "small_win_quality", "quality"],
                    [treatment, "small_win_quality", "quality"],
                    name=f"{y_var}_{quality}_{treatment}",
                )
            )
            results[-1].coef[SMALL_WIN] = results[-1].coef.pop(treatment)
            results[-1].se[SMALL_WIN] = results[-1].se.pop(treatment)
            results[-1].tstat[SMALL_WIN] = results[-1].tstat.pop(treatment)
    return results


def run_split(df: pd.DataFrame, quality_var: str = "concensus_full") -> list[RegressionResult]:
    """Run median-split regressions using the requested quality variable."""

    sample = df.loc[df["quality_defined"] & df[quality_var].notna()].copy()
    median = sample[quality_var].median()
    low = sample.loc[sample[quality_var].le(median)]
    high = sample.loc[sample[quality_var].gt(median)]
    results = []
    for y_var in CAR_VARS:
        for label, sub in [("low", low), ("high", high)]:
            results.append(
                ols_cluster(
                    sub,
                    y_var,
                    [SMALL_WIN],
                    [SMALL_WIN],
                    name=f"{y_var}_{quality_var}_{label}",
                )
            )
    return [results[0], results[1], results[2], results[3]]


def main() -> None:
    df = prepare_panel(winsorized=False)
    df.to_csv(H4_PANEL_PATH, index=False)
    print(f"Wrote {H4_PANEL_PATH} ({len(df):,} rows)")

    counts = feasibility_counts(df)
    print("\nH4 feasibility counts")
    print(counts.to_string(index=False))
    write_feasibility_table(counts)

    interaction = run_interaction(df)
    write_interaction_table(interaction)

    split = run_split(df, "concensus_full")
    write_split_table(split, "concensus_full")

    placebo = run_interaction(df, treatment="non_small_win")
    write_interaction_table(
        placebo,
        suffix="_placebo",
        treatment_label=r"${\it NonSmallWin}_{i}$",
    )

    winsorized = prepare_panel(winsorized=True)
    write_interaction_table(run_interaction(winsorized), suffix="_winsorized")


if __name__ == "__main__":
    main()
