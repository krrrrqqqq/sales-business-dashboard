"""Business metric calculations, kept separate from the Streamlit UI."""
from __future__ import annotations

import pandas as pd

from .data import STAGES


def calculate_kpis(df: pd.DataFrame) -> dict[str, float | int]:
    """Return lead count, wins, won revenue, win rate and average won deal size."""
    total_leads = int(len(df))
    wins = df.loc[df["status"].eq("Won")]
    won_count = int(len(wins))
    revenue = float(wins["deal_amount"].sum())
    return {
        "leads": total_leads,
        "won": won_count,
        "revenue": revenue,
        "win_rate": (won_count / total_leads * 100) if total_leads else 0.0,
        "average_won_deal": (revenue / won_count) if won_count else 0.0,
    }


def calculate_funnel(df: pd.DataFrame) -> pd.DataFrame:
    """Count leads that reached each stage and calculate progression rates.

    \`stage\` stores the furthest stage reached by a lead. Lost leads retain the
    stage they reached before being marked Lost. Counts are cumulative: e.g. a
    lead at Proposal is counted at New, Contacted, Qualified and Proposal.
    """
    records: list[dict[str, float | int | str]] = []
    rank_map = {stage: i for i, stage in enumerate(STAGES)}
    ranks = df["stage"].map(rank_map)
    for idx, stage in enumerate(STAGES):
        count = int((ranks >= idx).sum())
        previous_count = int((ranks >= idx - 1).sum()) if idx > 0 else count
        conversion = (count / previous_count * 100) if previous_count else 0.0
        records.append(
            {
                "stage": stage,
                "leads": count,
                "conversion_from_previous_pct": conversion if idx > 0 else 100.0,
            }
        )
    return pd.DataFrame(records)


def calculate_revenue_by_period(df: pd.DataFrame, frequency: str = "M") -> pd.DataFrame:
    """Sum revenue from Won leads by closing period."""
    won = df.loc[df["status"].eq("Won") & df["closed_at"].notna()].copy()
    if won.empty:
        return pd.DataFrame(columns=["period", "revenue"])
    won["period"] = won["closed_at"].dt.to_period(frequency).dt.to_timestamp()
    result = won.groupby("period", as_index=False)["deal_amount"].sum()
    return result.rename(columns={"deal_amount": "revenue"}).sort_values("period")


def calculate_source_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compare lead volume, win rate and won revenue across acquisition sources."""
    columns = ["source", "leads", "won", "win_rate_pct", "revenue"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    prepared = df.assign(
        is_won=df["status"].eq("Won").astype(int),
        won_revenue=df["deal_amount"].where(df["status"].eq("Won"), 0.0),
    )
    result = (
        prepared.groupby("source", dropna=False)
        .agg(
            leads=("lead_id", "nunique"),
            won=("is_won", "sum"),
            revenue=("won_revenue", "sum"),
        )
        .reset_index()
    )
    result["win_rate_pct"] = (result["won"] / result["leads"] * 100).fillna(0)
    return result[columns].sort_values(["revenue", "leads"], ascending=False).reset_index(drop=True)


def filter_data(
    df: pd.DataFrame,
    start_date,
    end_date,
    sources: list[str] | None = None,
    statuses: list[str] | None = None,
) -> pd.DataFrame:
    """Apply the creation-date, source and status filters used by the dashboard."""
    mask = df["created_at"].dt.date.between(start_date, end_date)
    if sources:
        mask &= df["source"].isin(sources)
    if statuses:
        mask &= df["status"].isin(statuses)
    return df.loc[mask].copy()
