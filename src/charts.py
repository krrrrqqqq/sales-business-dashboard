"""Plotly chart builders used by the Streamlit dashboard."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


LAYOUT = {
    "template": "plotly_white",
    "margin": {"l": 15, "r": 15, "t": 50, "b": 15},
    "font": {"family": "Inter, Arial, sans-serif", "size": 12},
}


def funnel_chart(funnel: pd.DataFrame) -> go.Figure:
    labels = [
        f"{int(row.leads)} лидов · {row.conversion_from_previous_pct:.1f}% к пред. этапу"
        for row in funnel.itertuples(index=False)
    ]
    customdata = funnel[["conversion_from_previous_pct"]].to_numpy()
    fig = go.Figure(
        go.Funnel(
            x=funnel["leads"],
            y=funnel["stage"],
            text=labels,
            textinfo="text",
            customdata=customdata,
            hovertemplate=(
                "Этап: %{y}<br>Лидов, достигших этапа: %{x}"
                "<br>Конверсия от предыдущего этапа: %{customdata[0]:.1f}%<extra></extra>"
            ),
        )
    )
    fig.update_layout(title="Воронка продаж и конверсия по этапам", **LAYOUT)
    return fig


def revenue_chart(revenue: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        revenue,
        x="period",
        y="revenue",
        title="Выручка по месяцу закрытия сделки",
        labels={"period": "Месяц закрытия", "revenue": "Выручка"},
        text_auto=".2s",
    )
    fig.update_traces(hovertemplate="Месяц: %{x|%b %Y}<br>Выручка: %{y:,.0f}<extra></extra>")
    fig.update_layout(**LAYOUT, xaxis={"tickformat": "%b %Y"})
    return fig


def source_chart(source_metrics: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=source_metrics["source"],
            y=source_metrics["leads"],
            name="Количество лидов",
            customdata=source_metrics[["won", "revenue"]].to_numpy(),
            hovertemplate=(
                "Источник: %{x}<br>Лидов: %{y}<br>Выиграно сделок: %{customdata[0]}"
                "<br>Выручка: %{customdata[1]:,.0f} у.е.<extra></extra>"
            ),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=source_metrics["source"],
            y=source_metrics["win_rate_pct"],
            name="Конверсия в Won, %",
            mode="lines+markers",
            line={"width": 3},
            hovertemplate="Источник: %{x}<br>Win rate: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.update_layout(title="Эффективность источников", **LAYOUT, legend={"orientation": "h", "y": 1.12})
    fig.update_xaxes(title_text="Источник")
    fig.update_yaxes(title_text="Количество лидов", secondary_y=False)
    fig.update_yaxes(title_text="Конверсия в Won, %", secondary_y=True, rangemode="tozero")
    return fig


def status_chart(df: pd.DataFrame) -> go.Figure:
    counts = df["status"].value_counts().rename_axis("status").reset_index(name="leads")
    fig = px.pie(
        counts,
        names="status",
        values="leads",
        hole=0.55,
        title="Распределение лидов по статусам",
        labels={"status": "Статус", "leads": "Лиды"},
    )
    fig.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="%{label}<br>Лидов: %{value}<extra></extra>")
    fig.update_layout(**LAYOUT, showlegend=False)
    return fig
