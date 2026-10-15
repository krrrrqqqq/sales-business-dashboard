# Sales & Leads Dashboard

Interactive business dashboard built with Python, Pandas, Streamlit, and Plotly.

> **Educational project:** the bundled dataset is synthetic and does not represent a real company or real customers.

## Business questions

- How many leads entered the sales pipeline during the selected period?
- What share of leads convert to won deals?
- How does revenue change over time?
- Which lead sources generate the most leads and the best conversion?

## Dashboard features

- KPI cards for lead count, won deals, revenue, and win conversion.
- Sales funnel counts and conversion between consecutive stages.
- Monthly revenue visualization.
- Lead-source comparison by volume and conversion.
- Filters for lead creation date, source, and status.
- CSV upload with required-column checks and readable handling of empty or invalid files.
- Small fixture CSV for manually checking calculations.

## Metrics

- **Leads:** number of rows after filters and validation.
- **Won deals:** count of records whose status is `Won`.
- **Revenue:** sum of deal values for won deals, grouped by closing month.
- **Win conversion:** won deals / all filtered leads × 100%.
- **Stage conversion:** number in the next stage / number in the previous stage × 100%.
- **Source conversion:** won leads from source / all leads from source × 100%.

Rows without a valid creation date or required fields are reported or excluded during validation. Revenue is counted only for won deals. The filters operate on the selected set of lead records; monthly revenue is grouped by closing date.

## Project structure

```text
sales-business-dashboard/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   └── synthetic_sales.csv
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── metrics.py
│   └── charts.py
└── tests/
    ├── test_metrics.py
    ├── test_data_loader.py
    └── fixtures/
        └── small_sample.csv
```

## Run locally

Python 3.10+ is recommended.

### Windows PowerShell

```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`).

## Run tests

```bash
python -m pytest -q
```

## Dataset

`data/synthetic_sales.csv` contains generated learning data only. It is clearly labeled as synthetic and should not be interpreted as actual business performance. `tests/fixtures/small_sample.csv` is a deliberately small example intended for checking metric calculations by hand.

## Tech stack

- Python
- Pandas
- Streamlit
- Plotly
- pytest

## Limitations

This is a portfolio/demo project, not a production CRM. Conversion metrics reflect the current records and simple stage/status definitions; real sales pipelines may require stage history and cohort-based conversion logic.
