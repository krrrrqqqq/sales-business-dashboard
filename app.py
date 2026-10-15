from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.charts import funnel_chart, revenue_chart, source_chart, status_chart
from src.data import DataValidationError, load_and_validate
from src.metrics import (
    calculate_funnel,
    calculate_kpis,
    calculate_revenue_by_period,
    calculate_source_metrics,
    filter_data,
)

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_CSV = BASE_DIR / "data" / "synthetic_sales.csv"

st.set_page_config(
    page_title="Sales & Leads Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.8rem; padding-bottom: 2.5rem;}
      [data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.22); padding: 16px; border-radius: 12px;}
      .dashboard-subtitle {color: #64748b; margin-top: -10px; margin-bottom: 20px;}
      div[data-testid="stAlert"] {border-radius: 10px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Sales & Leads Dashboard")
st.markdown(
    '<p class="dashboard-subtitle">Обзор воронки, выручки и каналов привлечения</p>',
    unsafe_allow_html=True,
)
st.info(
    "Учебный проект для портфолио. Встроенный CSV содержит синтетические данные — "
    "это не реальные продажи и не реальные клиенты."
)

with st.sidebar:
    st.header("Настройки отчёта")
    uploaded_file = st.file_uploader(
        "Загрузить другой CSV",
        type=["csv"],
        help="Ожидаются столбцы из README. Если файл не загружен, используется демонстрационный набор.",
    )
    st.caption("Без загрузки используется data/synthetic_sales.csv.")

input_file = uploaded_file if uploaded_file is not None else SAMPLE_CSV
try:
    df, validation_warnings = load_and_validate(input_file)
except DataValidationError as exc:
    st.error(f"Не удалось использовать файл: {exc}")
    st.stop()
except Exception as exc:  # keep unexpected file errors user-friendly
    st.error(f"Ошибка обработки файла: {exc}")
    st.stop()

for warning in validation_warnings:
    st.warning(warning)

if uploaded_file is not None:
    st.caption(f"Источник данных: загруженный файл **{uploaded_file.name}**.")
else:
    st.caption("Источник данных: встроенный учебный CSV (синтетические записи).")

min_date = df["created_at"].dt.date.min()
max_date = df["created_at"].dt.date.max()

with st.sidebar:
    date_range = st.date_input(
        "Период создания лида",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="DD.MM.YYYY",
    )
    source_options = sorted(df["source"].unique().tolist())
    selected_sources = st.multiselect("Источник", options=source_options, default=source_options)
    status_options = [status for status in ["Open", "Won", "Lost"] if status in df["status"].unique()]
    selected_statuses = st.multiselect("Статус", options=status_options, default=status_options)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
    start_date = end_date = date_range[0]
else:
    start_date, end_date = min_date, max_date

filtered = filter_data(df, start_date, end_date, selected_sources, selected_statuses)

st.subheader("Ключевые показатели")
if filtered.empty:
    st.warning("По выбранным фильтрам нет данных. Измените период, источник или статус.")
    st.stop()

kpis = calculate_kpis(filtered)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Количество лидов", f"{kpis['leads']:,}".replace(",", " "))
col2.metric("Выигранные сделки", f"{kpis['won']:,}".replace(",", " "))
col3.metric("Выручка Won", f"{kpis['revenue']:,.0f}".replace(",", " ") + " у.е.")
col4.metric("Конверсия в Won", f"{kpis['win_rate']:.1f}%")
average_won_deal_label = f"{kpis['average_won_deal']:,.0f}".replace(",", " ")
st.caption(
    f"Средний размер выигранной сделки: {average_won_deal_label} у.е. "
    "| Выручка считается только по сделкам со статусом Won."
)

st.divider()
left, right = st.columns(2, gap="large")
with left:
    st.plotly_chart(funnel_chart(calculate_funnel(filtered)), use_container_width=True)
with right:
    revenue = calculate_revenue_by_period(filtered)
    if revenue.empty:
        st.info("В выбранной выборке нет выигранных сделок с датой закрытия — график выручки пуст.")
    else:
        st.plotly_chart(revenue_chart(revenue), use_container_width=True)

left, right = st.columns(2, gap="large")
with left:
    source_metrics = calculate_source_metrics(filtered)
    st.plotly_chart(source_chart(source_metrics), use_container_width=True)
with right:
    st.plotly_chart(status_chart(filtered), use_container_width=True)

with st.expander("Сравнение источников в таблице"):
    source_table = source_metrics.rename(
        columns={
            "source": "Источник",
            "leads": "Лиды",
            "won": "Выиграно",
            "win_rate_pct": "Конверсия в Won, %",
            "revenue": "Выручка, у.е.",
        }
    ).copy()
    source_table["Конверсия в Won, %"] = source_table["Конверсия в Won, %"].round(1)
    source_table["Выручка, у.е."] = source_table["Выручка, у.е."].round(0).astype(int)
    st.dataframe(source_table, use_container_width=True, hide_index=True)

with st.expander("Посмотреть данные после фильтрации"):
    display_cols = ["lead_id", "created_at", "source", "status", "stage", "deal_amount", "closed_at"]
    st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)
    st.download_button(
        "Скачать отфильтрованный CSV",
        data=filtered[display_cols].to_csv(index=False).encode("utf-8-sig"),
        file_name="filtered_leads.csv",
        mime="text/csv",
    )

st.caption("Метрики рассчитываются на лету через Pandas; графики построены на Plotly и обновляются при изменении фильтров.")
